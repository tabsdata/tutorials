import tabsdata as td

s3_credentials=td.S3AccessKeyCredentials(
    td.EnvironmentSecret("AWS_ACCESS_KEY_ID"), td.EnvironmentSecret("AWS_SECRET_ACCESS_KEY")
)

@td.subscriber(
    tables=["customers", "customers_cdc"],
    destination=td.S3Destination(
        uri=["s3://tabsdata-oracle/customer_data/customers-$EXPORT_TIMESTAMP.parquet", "s3://tabsdata-oracle/customer_data/customers_cdc-$EXPORT_TIMESTAMP.parquet"],
        region="us-east-2",
        credentials=s3_credentials,
        catalog = td.AWSGlue(
        definition= {
            "name": "default",
            "type": "glue",
            "client.region": "us-east-2",
        },
        tables=["tabsdata-oracle.customers", "tabsdata-oracle.customers_cdc"],
        auto_create_at=["s3://tabsdata-oracle", "s3://tabsdata-oracle"],
        if_table_exists="replace",
        credentials = s3_credentials
    )
    )
)
def sub_s3_iceberg(customers: td.TableFrame, customers_cdc: td.TableFrame):
    return customers, customers_cdc
