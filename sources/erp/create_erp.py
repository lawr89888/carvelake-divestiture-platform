import os

import psycopg
from dotenv import load_dotenv


load_dotenv('/home/ibrahim-s/carvelake-divestiture-platform/sources/.env')


conn = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    sslmode="disable",
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendors (
    vendor_key VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    country VARCHAR(100),
    is_shared INTEGER NOT NULL DEFAULT 0,
    shared_with VARCHAR(255),
    bu_id VARCHAR(20) NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL,

    PRIMARY KEY (vendor_key, bu_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cost_centers (
    cc_key VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    business_group VARCHAR(50) NOT NULL,
    is_shared INTEGER NOT NULL DEFAULT 0,
    shared_with VARCHAR(255),
    bu_id VARCHAR(20) NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL,

    PRIMARY KEY (cc_key, bu_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gl_invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    bu_id VARCHAR(20) NOT NULL,
    vendor_key VARCHAR(50) NOT NULL,
    cc_key VARCHAR(50) NOT NULL,

    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    tax_amount NUMERIC(18,2),

    invoice_date TIMESTAMPTZ NOT NULL,
    due_date TIMESTAMPTZ NOT NULL,

    status VARCHAR(20) NOT NULL,
    payment_terms VARCHAR(20),

    is_deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL
)
""")

conn.commit()

cursor.close()
conn.close()

