from pyspark import pipelines as dp
from pyspark.sql import functions as F


BU_ID = spark.conf.get("bu_id")
SHARED_CATALOG = spark.conf.get("shared_catalog")
BU_CATALOG = spark.conf.get("bu_catalog")

SILVER = f"{SHARED_CATALOG}.{BU_ID}"
GOLD = f"{BU_CATALOG}.gold"


# 1. SALES MART

@dp.materialized_view(
    name=f"{GOLD}.sales_mart",
    comment="Sales KPIs aggregated by BU and business group"
)
def sales_mart():

    deals = (
        spark.read.table(f"{SILVER}.silver_deals")
        .select(
            "deal_id",
            "bu_id",
            "business_group",
            "amount",
            "stage"
        )
    )

    return (
        deals
        .groupBy(
            "bu_id",
            "business_group"
        )
        .agg(
            F.countDistinct("deal_id")
            .alias("deal_count"),

            F.sum("amount")
            .alias("pipeline_value_usd"),

            F.sum(
                F.when(
                    F.lower(F.col("stage")).isin(
                        "closed won",
                        "won"
                    ),
                    F.col("amount")
                ).otherwise(F.lit(0))
            ).alias("won_revenue_usd"),

            F.avg("amount")
            .alias("avg_deal_value_usd")
        )
    )


# 2. FINANCE MART

@dp.materialized_view(
    name=f"{GOLD}.finance_mart",
    comment="Finance KPIs aggregated by BU and business group"
)
def finance_mart():

    invoices = (
        spark.read.table(f"{SILVER}.silver_gl_invoices")
        .select(
            "invoice_id",
            "vendor_key",
            "cc_key",
            "bu_id",
            "amount"
        )
    )

    cost_centers = (
        spark.read.table(f"{SILVER}.silver_cost_centers")
        .select(
            "cc_key",
            "bu_id",
            "business_group"
        )
    )

    finance = (
        invoices
        .join(
            cost_centers,
            ["cc_key", "bu_id"],
            "left"
        )
    )

    return (
        finance
        .groupBy(
            "bu_id",
            "business_group"
        )
        .agg(
            F.countDistinct("invoice_id")
            .alias("invoice_count"),

            F.countDistinct("vendor_key")
            .alias("vendor_count"),

            F.sum("amount")
            .alias("total_spend_usd")
        )
    )


# 3. CUSTOMER MART

@dp.materialized_view(
    name=f"{GOLD}.customer_mart",
    comment="Customer KPIs aggregated by BU and business group"
)
def customer_mart():

    companies = (
        spark.read.table(f"{SILVER}.silver_companies")
        .select(
            "company_id",
            "bu_id",
            "business_group"
        )
    )

    contacts = (
        spark.read.table(f"{SILVER}.silver_contacts")
        .groupBy(
            "company_id",
            "bu_id"
        )
        .agg(
            F.countDistinct("contact_id")
            .alias("contact_count")
        )
    )

    deals = (
        spark.read.table(f"{SILVER}.silver_deals")
        .groupBy(
            "company_id",
            "bu_id"
        )
        .agg(
            F.countDistinct("deal_id")
            .alias("deal_count"),

            F.sum("amount")
            .alias("customer_revenue_usd")
        )
    )

    customers = (
        companies
        .join(
            contacts,
            ["company_id", "bu_id"],
            "left"
        )
        .join(
            deals,
            ["company_id", "bu_id"],
            "left"
        )
        .fillna(
            {
                "contact_count": 0,
                "deal_count": 0,
                "customer_revenue_usd": 0
            }
        )
    )

    return (
        customers
        .groupBy(
            "bu_id",
            "business_group"
        )
        .agg(
            F.countDistinct("company_id")
            .alias("company_count"),

            F.sum("contact_count")
            .alias("contact_count"),

            F.sum("deal_count")
            .alias("deal_count"),

            F.sum("customer_revenue_usd")
            .alias("customer_revenue_usd")
        )
    )