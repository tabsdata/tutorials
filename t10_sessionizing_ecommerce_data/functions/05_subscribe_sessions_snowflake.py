import os

import tabsdata as td

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PAT = td.EnvironmentSecret("SNOWFLAKE_PAT")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")


CONNECTION_PARAMETERS = {
    "database": SNOWFLAKE_DATABASE,
    "schema": SNOWFLAKE_SCHEMA,
    "warehouse": SNOWFLAKE_WAREHOUSE,
    "account": SNOWFLAKE_ACCOUNT,
    "user": SNOWFLAKE_USER,
    "password": SNOWFLAKE_PAT,
    "role": SNOWFLAKE_ROLE,
}


@td.subscriber(
    tables=["aggregated_sessions", "sessionized_logs"],
    destination=td.SnowflakeDestination(
        CONNECTION_PARAMETERS,
        destination_table=["aggregated_sessions", "sessionized_logs"],
        if_table_exists="replace",
    ),
)
def subscribe_sessions(aggregated_sessions, sessionized_logs):
    return aggregated_sessions, sessionized_logs
