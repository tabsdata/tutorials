import tabsdata as td
import os

AWS_S3_URI = os.getenv("AWS_S3_URI")
AWS_REGION = os.getenv("AWS_REGION")
AWS_SECRET_KEY = td.EnvironmentSecret("AWS_SECRET_KEY")
AWS_ACCESS_KEY = td.EnvironmentSecret("AWS_ACCESS_KEY")
AWS_GLUE_DATABASE = os.getenv("AWS_GLUE_DATABASE")

s3_credentials = td.S3AccessKeyCredentials(AWS_ACCESS_KEY, AWS_SECRET_KEY)


@td.subscriber(
    tables=["masked_customer_data"],
    destination=td.S3Destination(
        uri=[
            f"{AWS_S3_URI}/masked_customer_data/masked_customer_data-$EXPORT_TIMESTAMP.parquet"
        ],
        region=AWS_REGION,
        credentials=s3_credentials,
        catalog=td.AWSGlue(
            definition={
                "name": "default",
                "type": "glue",
                "client.region": AWS_REGION,
            },
            tables=[f"{AWS_GLUE_DATABASE}.masked-customer-data"],
            auto_create_at=[AWS_S3_URI],
            if_table_exists="replace",
            credentials=s3_credentials,
        ),
    ),
)
def s3_sub(masked_customer_data: td.TableFrame):
    return masked_customer_data
