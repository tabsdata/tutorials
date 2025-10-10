import tabsdata as td
import os

# input your MYSQL credentials below
MYSQL_USERNAME = td.EnvironmentSecret("MYSQL_USERNAME")
MYSQL_PASSWORD = td.EnvironmentSecret("MYSQL_PASSWORD")
MYSQL_URI = os.getenv("MYSQL_URI")


@td.subscriber(
    tables=["input_data"],
    destination=td.MySQLDestination(
        uri=MYSQL_URI,
        destination_table=["raw_customer_data"],
        credentials=td.UserPasswordCredentials(MYSQL_USERNAME, MYSQL_PASSWORD),
        if_table_exists="replace",
    ),
)
def mysql_setup_sub(tf1: td.TableFrame):
    return tf1
