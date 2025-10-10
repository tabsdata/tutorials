import tabsdata as td
import os
from typing import List
import polars as pl
import functools

MYSQL_USERNAME = td.EnvironmentSecret("MYSQL_USERNAME")
MYSQL_PASSWORD = td.EnvironmentSecret("MYSQL_PASSWORD")


@td.publisher(
    source=td.MySQLSource(
        uri=os.getenv("MYSQL_URI"),
        query=["SELECT * FROM `policy_dim`"],
        credentials=td.UserPasswordCredentials(MYSQL_USERNAME, MYSQL_PASSWORD),
    ),
    tables=["policy_dim"],
    trigger_by=["claims_fact_today"],
)
def policy_dim_pub(tf: td.TableFrame):
    return tf
