import os, json, hashlib, threading, time
from pathlib import Path
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient


# =========================================================
# CONFIG
# =========================================================

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state/crm_watermarks.json"
TMP = ROOT / "tmp/crm"

load_dotenv(ROOT / "sources/.env")

API_KEY = os.getenv("CRM_API_KEY")
HOST = os.getenv("DATABRICKS_HOST")
TOKEN = os.getenv("DATABRICKS_TOKEN")

BASE_URL = "http://127.0.0.1:8000/api/v1"
LANDING = "/Volumes/shared/landing/raw/crm"
AUDIT = "/Volumes/shared/landing/raw/audit/crm"

OBJECTS = {
    "companies": ("companies.json", "company_id"),
    "contacts": ("contacts.json", "contact_id"),
    "deals": ("deals.json", "deal_id")
}

if not all([API_KEY, HOST, TOKEN]):
    raise RuntimeError("Missing required environment variables")

TMP.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


# =========================================================
# REST API
# =========================================================

def load_data(obj):
    with open(DATA_DIR / OBJECTS[obj][0]) as f:
        return json.load(f)


@app.before_request
def auth():
    if request.path != "/health":
        if request.headers.get("Authorization") != f"Bearer {API_KEY}":
            return jsonify({"error": "Unauthorized"}), 401


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/v1/<obj>")
def get_rows(obj):
    if obj not in OBJECTS:
        return {"error": "Not found"}, 404

    rows = load_data(obj)
    bu = request.args.get("bu_id")
    since = request.args.get("updated_since")

    if bu:
        rows = [r for r in rows if r.get("bu_id") == bu]

    if since:
        try:
            ts = datetime.fromisoformat(since.replace("Z", "+00:00"))
            rows = [
                r for r in rows
                if datetime.fromisoformat(
                    r["updated_at"].replace("Z", "+00:00")
                ) > ts
            ]
        except ValueError:
            return {"error": "Invalid timestamp"}, 400

    try:
        limit = int(request.args.get("limit", 500))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return {"error": "Invalid pagination"}, 400

    if not 1 <= limit <= 500 or offset < 0:
        return {"error": "Invalid pagination"}, 400

    page = rows[offset:offset + limit]
    next_offset = offset + limit if offset + limit < len(rows) else None

    return {
        "data": page,
        "paging": {"next_offset": next_offset}
    }


@app.get("/api/v1/<obj>/<row_id>")
def get_row(obj, row_id):
    if obj not in OBJECTS:
        return {"error": "Not found"}, 404

    key = OBJECTS[obj][1]

    for row in load_data(obj):
        if row.get(key) == row_id:
            return {"data": row}

    return {"error": "Not found"}, 404


# =========================================================
# STATE
# =========================================================

def load_state():
    return (
        json.loads(STATE_FILE.read_text())
        if STATE_FILE.exists()
        else {}
    )


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# =========================================================
# EXTRACT
# =========================================================

def extract(obj, watermark):
    rows, offset = [], 0

    while True:
        params = {"limit": 500, "offset": offset}

        if watermark:
            params["updated_since"] = watermark

        r = requests.get(
            f"{BASE_URL}/{obj}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params=params,
            timeout=30
        )

        r.raise_for_status()
        payload = r.json()

        rows.extend(payload["data"])
        offset = payload["paging"]["next_offset"]

        if offset is None:
            return rows


# =========================================================
# IDEMPOTENCY
# =========================================================

def batch_id(obj, watermark, rows):
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    value = f"{obj}|{watermark}|{raw}"

    return hashlib.sha256(
        value.encode()
    ).hexdigest()[:16]


# =========================================================
# DATABRICKS UPLOAD
# =========================================================

def upload(w, path, data):
    local = TMP / Path(path).name
    local.write_text(json.dumps(data, indent=2))

    w.files.create_directory(str(Path(path).parent))

    w.files.upload_from(
        path,
        str(local),
        overwrite=True
    )


# =========================================================
# PROCESS OBJECT
# =========================================================

def process(w, obj, state):
    before = state.get(obj)
    rows = extract(obj, before)

    if not rows:
        print(f"{obj}: no new rows")
        return

    batch = batch_id(obj, before, rows)
    after = max(r["updated_at"] for r in rows)
    ingested = datetime.now(timezone.utc).isoformat()

    for row in rows:
        row.update({
            "_ingested_at": ingested,
            "_source_system": "crm",
            "_source_object": obj,
            "_batch_id": batch
        })

    # Split by BU
    bus = {}

    for row in rows:
        bus.setdefault(row["bu_id"], []).append(row)

    for bu, bu_rows in bus.items():
        upload(
            w,
            f"{LANDING}/{bu}/{obj}/{batch}.json",
            bu_rows
        )

    # Audit
    upload(
        w,
        f"{AUDIT}/{obj}_{batch}.json",
        {
            "batch_id": batch,
            "source_system": "crm",
            "source_object": obj,
            "records_extracted": len(rows),
            "watermark_before": before,
            "watermark_after": after,
            "status": "SUCCESS"
        }
    )

    # Advance only after successful uploads
    state[obj] = after
    save_state(state)

    print(f"{obj}: {len(rows)} rows uploaded")


# =========================================================
# RUN
# =========================================================

def push():
    w = WorkspaceClient(host=HOST, token=TOKEN)
    state = load_state()

    for obj in OBJECTS:
        process(w, obj, state)

    print("CRM ingestion completed")


if __name__ == "__main__":

    threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=8000,
            debug=False,
            use_reloader=False
        ),
        daemon=True
    ).start()

    time.sleep(1)
    push()