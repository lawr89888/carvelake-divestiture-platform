import os, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient


ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "tmp/erp"
STATE = ROOT / "state/erp_watermarks.json"

load_dotenv(ROOT / "sources/.env")

DB = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

HOST = os.getenv("DATABRICKS_HOST")
TOKEN = os.getenv("DATABRICKS_TOKEN")

LANDING = "/Volumes/shared/landing/raw/erp"
AUDIT = "/Volumes/shared/landing/raw/audit/erp"

TABLES = ["vendors", "cost_centers", "gl_invoices"]

TMP.mkdir(parents=True, exist_ok=True)
STATE.parent.mkdir(parents=True, exist_ok=True)


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2))


def json_safe(row):
    row = dict(row)

    for k, v in row.items():
        if isinstance(v, datetime):
            row[k] = v.isoformat()
        elif hasattr(v, "as_tuple"):  # Decimal
            row[k] = float(v)

    return row


def extract(conn, table, watermark):
    query = f"SELECT * FROM {table}"
    params = []

    if watermark:
        query += " WHERE updated_at > %s"
        params.append(watermark)

    query += " ORDER BY updated_at"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return [json_safe(r) for r in cur.fetchall()]


def make_batch_id(table, watermark, rows):
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    value = f"{table}|{watermark}|{raw}"

    return hashlib.sha256(
        value.encode()
    ).hexdigest()[:16]


def upload(w, path, data):
    local = TMP / Path(path).name
    local.write_text(json.dumps(data, indent=2))

    w.files.create_directory(str(Path(path).parent))

    w.files.upload_from(
        path,
        str(local),
        overwrite=True
    )


def process(w, conn, table, state):
    key = f"erp.{table}"
    before = state.get(key)

    rows = extract(conn, table, before)

    if not rows:
        print(f"{table}: no new rows")
        return

    batch = make_batch_id(table, before, rows)
    after = max(r["updated_at"] for r in rows)
    ingested = datetime.now(timezone.utc).isoformat()

    # add metadata
    for row in rows:
        row.update({
            "_ingested_at": ingested,
            "_source_system": "erp",
            "_source_object": table,
            "_batch_id": batch
        })

    # split by BU and upload
    grouped = {}

    for row in rows:
        grouped.setdefault(
            row.get("bu_id", "UNKNOWN"),
            []
        ).append(row)

    for bu, bu_rows in grouped.items():
        upload(
            w,
            f"{LANDING}/{bu}/{table}/{batch}.json",
            bu_rows
        )

    # audit
    upload(
        w,
        f"{AUDIT}/{table}_{batch}.json",
        {
            "batch_id": batch,
            "source_system": "erp",
            "source_object": table,
            "records_extracted": len(rows),
            "watermark_before": before,
            "watermark_after": after,
            "status": "SUCCESS"
        }
    )

    # update watermark only after successful uploads
    state[key] = after
    save_state(state)

    print(f"{table}: {len(rows)} rows uploaded")


def main():
    if not all([*DB.values(), HOST, TOKEN]):
        raise RuntimeError("Missing environment variables")

    w = WorkspaceClient(
        host=HOST,
        token=TOKEN
    )

    state = load_state()

    with psycopg.connect(**DB) as conn:
        print("Connected to PostgreSQL")

        for table in TABLES:
            process(w, conn, table, state)

    print("ERP ingestion completed")


if __name__ == "__main__":
    main()