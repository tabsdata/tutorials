import os
from typing import List

import tabsdata.tableframe as tdf

import tabsdata as td

SNOWFLAKE_ACCOUNT = td.EnvironmentSecret("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = td.EnvironmentSecret("SNOWFLAKE_USER")
SNOWFLAKE_PAT = td.EnvironmentSecret("SNOWFLAKE_PAT")
SNOWFLAKE_ROLE = td.EnvironmentSecret("SNOWFLAKE_ROLE")
SNOWFLAKE_DATABASE = td.EnvironmentSecret("SNOWFLAKE_DATABASE").secret_value
SNOWFLAKE_SCHEMA = td.EnvironmentSecret("SNOWFLAKE_SCHEMA").secret_value
SNOWFLAKE_WAREHOUSE = td.EnvironmentSecret("SNOWFLAKE_WAREHOUSE").secret_value

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
    tables="sf_snapshot",
    destination=td.SnowflakeDestination(
        CONNECTION_PARAMETERS,
        destination_table="sf_snapshot",
        if_table_exists="replace",
    ),
)
def snowflake_sub(tf):
    return tf
