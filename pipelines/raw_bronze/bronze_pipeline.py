from pyspark import pipelines as dp

BU_ID = spark.conf.get("bu_id")

SOURCES = {
    "crm": ["companies", "contacts", "deals"],
    "erp": ["vendors", "cost_centers", "gl_invoices"],
}


def create_bronze_table(source_system, source_object):
    table_name = f"bronze_{source_system}_{source_object}"

    source_path = (
        f"/Volumes/shared/landing/raw/"
        f"{source_system}/{BU_ID}/{source_object}/"
    )

    schema_path = (
        f"/Volumes/shared/landing/autoloader_metadata/"
        f"dev/{BU_ID}/{table_name}/"
    )

    @dp.table(
        name=table_name,
        comment=f"Bronze table for {source_system}.{source_object} - {BU_ID}",
        table_properties={"quality": "bronze"},
    )
    def bronze_table():
        return (
            spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "text")
            .option("wholeText", "true")
            .option("cloudFiles.schemaLocation", schema_path)
            .load(source_path)
        )


for source_system, objects in SOURCES.items():
    for source_object in objects:
        create_bronze_table(source_system, source_object)