from functools import reduce

from pyspark import pipelines as dp
from pyspark.sql import functions as F


PREFIX = spark.conf.get("prefix", "")

BUS = [f"{PREFIX}bu_{i:02d}" for i in range(1, 7)]
ENTERPRISE_CATALOG = f"{PREFIX}enterprise"


def union_mart(mart_name):
    dfs = [
        spark.read.table(f"{bu}.gold.{mart_name}")
        for bu in BUS
    ]

    return reduce(
        lambda left, right: left.unionByName(right),
        dfs
    )


# 1. Which BU performs best in sales?

@dp.materialized_view(
    name=f"{ENTERPRISE_CATALOG}.gold.bu_sales_performance"
)
def bu_sales_performance():

    sales = union_mart("sales_mart")

    return (
        sales
        .groupBy("bu_id")
        .agg(
            F.sum("deal_count").alias("deal_count"),
            F.sum("pipeline_value_usd").alias("pipeline_value_usd"),
            F.sum("won_revenue_usd").alias("won_revenue_usd")
        )
    )


# 2. Which BU spends the most?

@dp.materialized_view(
    name=f"{ENTERPRISE_CATALOG}.gold.bu_finance_performance"
)
def bu_finance_performance():

    finance = union_mart("finance_mart")

    return (
        finance
        .groupBy("bu_id")
        .agg(
            F.sum("invoice_count").alias("invoice_count"),
            F.sum("total_spend_usd").alias("total_spend_usd")
        )
    )


# 3. Which BU has the largest customer base?

@dp.materialized_view(
    name=f"{ENTERPRISE_CATALOG}.gold.bu_customer_performance"
)
def bu_customer_performance():

    customers = union_mart("customer_mart")

    return (
        customers
        .groupBy("bu_id")
        .agg(
            F.sum("company_count").alias("company_count"),
            F.sum("contact_count").alias("contact_count"),
            F.sum("customer_revenue_usd").alias("customer_revenue_usd")
        )
    )