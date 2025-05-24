
import tabsdata as td

pg_username = td.HashiCorpSecret("td-pg", "PG_USERNAME")
pg_password = td.HashiCorpSecret("td-pg", "PG_PASSWORD")

@td.publisher(
    source=td.PostgresSource(
        uri="postgres://127.0.0.1:5432/customers",
        query=[
            "select * from customer_leads;",
        ],
        credentials=td.UserPasswordCredentials(pg_username, pg_password),
    ),

    # Name of the table created in Tabsdata.
    tables = ["customer_leads"],
)

def publish_customers(tf: td.TableFrame):
    
    # Drop columns from the input file before publishing to Tabsdata.
    output_tf = tf.select(["FIRST_NAME","LAST_NAME","COMPANY_NAME","EMAIL","CITY","WEB","DEAL_VALUE"])

    return output_tf


