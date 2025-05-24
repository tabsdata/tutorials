import tabsdata as td

s3_credentials=td.S3AccessKeyCredentials(
    td.HashiCorpSecret("sample-secret", "AWS_ACCESS_KEY_ID"), 
    td.HashiCorpSecret("sample-secret", "AWS_SECRET_ACCESS_KEY")
)

@td.subscriber(
    tables=["customer_leads"],
    destination=td.S3Destination(
        uri=["s3://td-iceberg/customers-$EXPORT_TIMESTAMP.parquet"],
        region="us-west-1",
        credentials=s3_credentials,
        # Adding file as db for an Iceberg table in AWS Glue catalog catalog
        catalog = td.AWSGlue(
            definition= {
                "name": "default",
                "type": "glue",
                "client.region": "us-west-1",
            },
            tables=["td-iceberg.customers"],
            auto_create_at="s3://td-iceberg",
            if_table_exists="replace",
            credentials = s3_credentials
        )
    )
)
def sub_s3_iceberg(people: td.TableFrame) -> td.TableFrame:
    return people