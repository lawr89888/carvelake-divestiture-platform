from faker import Faker
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import random



SEED = 42

Faker.seed(SEED)
random.seed(SEED)

fake = Faker()

BU_IDS = [
    "bu_01",
    "bu_02",
    "bu_03",
    "bu_04",
    "bu_05",
    "bu_06",
]

SHARED_WITH = [
    "bu_02",
    "bu_03",
    "bu_06",
]

CURRENCIES = [
    "USD",
    "EUR",
    "GBP",
]

BUSINESS_GROUPS = [
    "bg_direct",
    "bg_partner",
    "bg_online",
]

VENDOR_CATEGORIES = [
    "Technology",
    "Logistics",
    "Consulting",
    "Manufacturing",
    "Office Supplies",
    "Marketing",
]

DEPARTMENTS = [
    "Finance",
    "Sales",
    "Marketing",
    "Operations",
    "IT",
    "HR",
    "Procurement",
    "Customer Success",
]

STATUSES = [
    "OPEN",
    "PAID",
    "VOID",
]

PAYMENT_TERMS = [
    "NET30",
    "NET60",
]


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "erp.db"

START_DATE = datetime(
    2025,
    1,
    1,
    tzinfo=timezone.utc,
)

END_DATE = datetime(
    2026,
    8,
    1,
    tzinfo=timezone.utc,
)



def iso_utc(dt):
    return dt.astimezone(timezone.utc).isoformat()


def random_datetime(start, end):
    seconds = int(
        (end - start).total_seconds()
    )

    offset = random.randint(
        0,
        seconds,
    )

    return start + timedelta(
        seconds=offset
    )



def generate_vendors():

    vendors = []

    for bu_number, bu_id in enumerate(
        BU_IDS,
        start=1,
    ):

        for vendor_number in range(1, 16):

            vendors.append({
                "vendor_key":
                    f"V-{bu_number:02d}-{vendor_number:04d}",

                "name":
                    fake.company(),

                "category":
                    random.choice(
                        VENDOR_CATEGORIES
                    ),

                "country":
                    fake.country(),

                "is_shared":
                    0,

                "shared_with":
                    None,

                "bu_id":
                    bu_id,

                "is_deleted":
                    random.choice([
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 1,
                    ]),

                "updated_at":
                    iso_utc(
                        random_datetime(
                            START_DATE,
                            END_DATE,
                        )
                    ),
            })

    # Shared vendor
    vendors.append({
        "vendor_key":
            "V-SHARED-0001",

        "name":
            "Global Shared Services Ltd",

        "category":
            "Professional Services",

        "country":
            "United States",

        "is_shared":
            1,

        "shared_with":
            "bu_02|bu_03|bu_06",

        "bu_id":
            "SHARED",

        "is_deleted":
            0,

        "updated_at":
            iso_utc(END_DATE),
    })

    return vendors




def generate_cost_centers():

    cost_centers = []

    for bu_number, bu_id in enumerate(
        BU_IDS,
        start=1,
    ):

        for cc_number in range(1, 9):

            department = random.choice(
                DEPARTMENTS
            )

            cost_centers.append({
                "cc_key":
                    f"CC-{bu_number:02d}-{cc_number:04d}",

                "name":
                    f"{department} Cost Center {cc_number}",

                "department":
                    department,

                "business_group":
                    random.choice(
                        BUSINESS_GROUPS
                    ),

                "is_shared":
                    0,

                "shared_with":
                    None,

                "bu_id":
                    bu_id,

                "is_deleted":
                    random.choice([
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 1,
                    ]),

                "updated_at":
                    iso_utc(
                        random_datetime(
                            START_DATE,
                            END_DATE,
                        )
                    ),
            })

    cost_centers.append({
        "cc_key":
            "CC-SHARED-0001",

        "name":
            "Global Shared Operations",

        "department":
            "Operations",

        "business_group":
            "bg_direct",

        "is_shared":
            1,

        "shared_with":
            "bu_02|bu_03|bu_06",

        "bu_id":
            "SHARED",

        "is_deleted":
            0,

        "updated_at":
            iso_utc(END_DATE),
    })

    return cost_centers


def generate_invoices(
    vendors,
    cost_centers,
):

    invoices = []

    invoice_number = 1

    for bu_id in BU_IDS:

        vendor_keys = [
            vendor["vendor_key"]
            for vendor in vendors
            if vendor["bu_id"] == bu_id
        ]

        cc_keys = [
            cc["cc_key"]
            for cc in cost_centers
            if cc["bu_id"] == bu_id
        ]

        # Allow shared dimensions
        if bu_id in SHARED_WITH:
            vendor_keys.append(
                "V-SHARED-0001"
            )

            cc_keys.append(
                "CC-SHARED-0001"
            )

        for _ in range(300):

            invoice_date = random_datetime(
                START_DATE,
                END_DATE - timedelta(days=60),
            )

            payment_terms = random.choice(
                PAYMENT_TERMS
            )

            term_days = (
                30
                if payment_terms == "NET30"
                else 60
            )

            due_date = (
                invoice_date
                + timedelta(days=term_days)
            )

            amount = round(
                random.uniform(
                    100,
                    100_000,
                ),
                2,
            )

            tax_rate = random.choice([
                0,
                0.05,
                0.10,
                0.15,
                0.20,
            ])

            tax_amount = round(
                amount * tax_rate,
                2,
            )

            invoices.append({
                "invoice_id":
                    f"INV-{invoice_number:07d}",

                "bu_id":
                    bu_id,

                "vendor_key":
                    random.choice(
                        vendor_keys
                    ),

                "cc_key":
                    random.choice(
                        cc_keys
                    ),

                "amount":
                    amount,

                "currency":
                    random.choice(
                        CURRENCIES
                    ),

                "tax_amount":
                    tax_amount,

                "invoice_date":
                    iso_utc(
                        invoice_date
                    ),

                "due_date":
                    iso_utc(
                        due_date
                    ),

                "status":
                    random.choice(
                        STATUSES
                    ),

                "payment_terms":
                    payment_terms,

                "is_deleted":
                    random.choice([
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 1,
                    ]),

                "updated_at":
                    iso_utc(
                        random_datetime(
                            invoice_date,
                            END_DATE,
                        )
                    ),
            })

            invoice_number += 1

    return invoices



import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def insert_data(
    vendors,
    cost_centers,
    invoices,
):

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable",
    ) as conn:

        with conn.cursor() as cursor:

            # -------------------------
            # Vendors
            # -------------------------

            cursor.executemany(
                """
                INSERT INTO vendors (
                    vendor_key,
                    name,
                    category,
                    country,
                    is_shared,
                    shared_with,
                    bu_id,
                    is_deleted,
                    updated_at
                )
                VALUES (
                    %(vendor_key)s,
                    %(name)s,
                    %(category)s,
                    %(country)s,
                    %(is_shared)s,
                    %(shared_with)s,
                    %(bu_id)s,
                    %(is_deleted)s,
                    %(updated_at)s
                )
                """,
                vendors,
            )

            # -------------------------
            # Cost Centers
            # -------------------------

            cursor.executemany(
                """
                INSERT INTO cost_centers (
                    cc_key,
                    name,
                    department,
                    business_group,
                    is_shared,
                    shared_with,
                    bu_id,
                    is_deleted,
                    updated_at
                )
                VALUES (
                    %(cc_key)s,
                    %(name)s,
                    %(department)s,
                    %(business_group)s,
                    %(is_shared)s,
                    %(shared_with)s,
                    %(bu_id)s,
                    %(is_deleted)s,
                    %(updated_at)s
                )
                """,
                cost_centers,
            )

            # -------------------------
            # GL Invoices
            # -------------------------

            cursor.executemany(
                """
                INSERT INTO gl_invoices (
                    invoice_id,
                    bu_id,
                    vendor_key,
                    cc_key,
                    amount,
                    currency,
                    tax_amount,
                    invoice_date,
                    due_date,
                    status,
                    payment_terms,
                    is_deleted,
                    updated_at
                )
                VALUES (
                    %(invoice_id)s,
                    %(bu_id)s,
                    %(vendor_key)s,
                    %(cc_key)s,
                    %(amount)s,
                    %(currency)s,
                    %(tax_amount)s,
                    %(invoice_date)s,
                    %(due_date)s,
                    %(status)s,
                    %(payment_terms)s,
                    %(is_deleted)s,
                    %(updated_at)s
                )
                """,
                invoices,
            )

        conn.commit()

    print("ERP data inserted successfully.")
def main():

    vendors = generate_vendors()

    cost_centers = (
        generate_cost_centers()
    )

    invoices = generate_invoices(
        vendors,
        cost_centers,
    )

    insert_data(
        vendors,
        cost_centers,
        invoices,
    )

    print("Data inserted successfully.")
    print(f"Vendors: {len(vendors)}")
    print(
        f"Cost Centers: {len(cost_centers)}"
    )
    print(f"Invoices: {len(invoices)}")


if __name__ == "__main__":
    main()