import tabsdata as td

# input your MYSQL credentials below
MYSQL_USERNAME = td.EnvironmentSecret("MYSQL_USERNAME")
MYSQL_PASSWORD = td.EnvironmentSecret("MYSQL_PASSWORD")
MYSQL_URI = td.EnvironmentSecret("MYSQL_URI").secret_value


@td.subscriber(
    tables=["masked_customer_data"],
    destination=td.MySQLDestination(
        uri=MYSQL_URI,
        destination_table=["masked_customer_data"],
        credentials=td.UserPasswordCredentials(MYSQL_USERNAME, MYSQL_PASSWORD),
        if_table_exists="replace",
    ),
)
def mysql_sub(tf1: td.TableFrame):
    return tf1
