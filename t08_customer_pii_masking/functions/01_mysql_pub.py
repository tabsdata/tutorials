import tabsdata as td

MYSQL_USERNAME = td.EnvironmentSecret("MYSQL_USERNAME")
MYSQL_PASSWORD = td.EnvironmentSecret("MYSQL_PASSWORD")
MYSQL_URI = td.EnvironmentSecret("MYSQL_URI").secret_value


@td.publisher(
    source=td.MySQLSource(
        uri=MYSQL_URI,
        query=["SELECT * FROM raw_customer_data"],
        credentials=td.UserPasswordCredentials(MYSQL_USERNAME, MYSQL_PASSWORD),
    ),
    tables=["raw_customer_data"],
)
def mysql_pub(tf1: td.TableFrame):
    return tf1
