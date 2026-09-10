from pyspark import pipelines as dp
from pyspark.sql import functions as F


BU_ID = spark.conf.get("bu_id")


TABLES = {
    "crm_companies": {
        "pk": ["company_id"],
        "target": "companies",
    },
    "crm_contacts": {
        "pk": ["contact_id"],
        "target": "contacts",
    },
    "crm_deals": {
        "pk": ["deal_id"],
        "target": "deals",
    },
    "erp_vendors": {
        "pk": ["vendor_key", "bu_id"],
        "target": "vendors",
    },
    "erp_cost_centers": {
        "pk": ["cc_key", "bu_id"],
        "target": "cost_centers",
    },
    "erp_gl_invoices": {
        "pk": ["invoice_id"],
        "target": "gl_invoices",
    },
}


def clean(df, name):

    df = df.withColumn(
        "updated_at",
        F.to_timestamp("updated_at")
    )

    # SHARED dimensions
    if name in ["erp_vendors", "erp_cost_centers"]:

        df = (
            df
            .filter(
                (F.col("bu_id") == BU_ID)
                |
                (
                    (F.col("bu_id") == "SHARED")
                    &
                    F.array_contains(
                        F.split(F.col("shared_with"), r"\|"),
                        BU_ID
                    )
                )
            )
            .withColumn("bu_id", F.lit(BU_ID))
        )

    else:
        df = df.withColumn(
            "bu_id",
            F.lit(BU_ID)
        )

    return df


def create_silver(name, config):

    source = f"bronze_{name}"
    staging = f"{name}_staging"
    target = f"silver_{config['target']}"

    @dp.table(
        name=staging,
        private=True
    )
    @dp.expect_or_drop(
        "valid_updated_at",
        "updated_at IS NOT NULL"
    )
    @dp.expect_or_fail(
        "valid_bu",
        "bu_id IS NOT NULL AND bu_id <> 'SHARED'"
    )
    def staging_table():

        df = (
            spark.readStream
            .table(source)
            .withColumn(
                "parsed",
                F.explode(
                    F.from_json(
                        "value",
                        """
                        array<struct<
                            annual_revenue:double,
                            bu_id:string,
                            business_group:string,
                            company_id:string,
                            contact_id:string,
                            deal_id:string,
                            vendor_key:string,
                            cc_key:string,
                            invoice_id:string,
                            country:string,
                            created_at:string,
                            domain:string,
                            employee_count:long,
                            industry:string,
                            is_active:boolean,
                            is_deleted:int,
                            name:string,
                            owner_rep:string,
                            updated_at:string,
                            first_name:string,
                            last_name:string,
                            email:string,
                            phone:string,
                            job_title:string,
                            amount:double,
                            currency:string,
                            stage:string,
                            close_date:string,
                            probability:double,
                            tax_amount:double,
                            invoice_date:string,
                            due_date:string,
                            status:string,
                            payment_terms:string,
                            shared_with:string,
                            _ingested_at:string,
                            _source_system:string,
                            _source_object:string,
                            _batch_id:string
                        >>
                        """
                    )
                )
            )
            .select("parsed.*")
        )

        return clean(df, name)

    dp.create_streaming_table(
        name=target
    )

    dp.create_auto_cdc_flow(
        target=target,
        source=staging,
        keys=config["pk"],
        sequence_by=F.col("updated_at"),
        apply_as_deletes=F.expr("is_deleted = 1"),
        stored_as_scd_type=1,
    )


for name, config in TABLES.items():
    create_silver(name, config)