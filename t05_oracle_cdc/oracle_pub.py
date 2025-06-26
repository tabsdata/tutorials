import tabsdata as td

@td.publisher(
    source=td.OracleSource(
        uri="oracle://127.0.0.1:1521/orclpdb1",
        query=[
            'select * from TABSDATA_USER.customers'
        ],
        credentials=td.UserPasswordCredentials(td.EnvironmentSecret("ORACLEDB_USERNAME"), td.EnvironmentSecret("ORACLEDB_PASSWORD")),
    ),
    tables=["customers"],
)
def oracle_pub(tf1: td.TableFrame):
    return tf1
