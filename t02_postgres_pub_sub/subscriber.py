import tabsdata as td

pg_username = td.HashiCorpSecret("td-pg", "PG_USERNAME")
pg_password = td.HashiCorpSecret("td-pg", "PG_USERNAME")

@td.subscriber(
    # Name of the table to be exported from Tabsdata.
    tables = ["customer_leads"],

    # Postgres details for the data to be written by the Subscriber.
    destination=td.PostgresDestination(
        uri="postgres://127.0.0.1:5432/customers",
        destination_table=["high_value_customer_leads"],
        credentials=td.UserPasswordCredentials(pg_username, pg_password),
        if_table_exists="replace",
    ),
)

def subscribe_order_items_postgres(tf: td.TableFrame):
    output_tf = tf.filter(td.col("DEAL_VALUE") >= 4000)
    return output_tf