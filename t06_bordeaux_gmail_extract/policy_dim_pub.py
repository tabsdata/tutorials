import tabsdata as td
import os
from typing import List
import polars as pl
import functools
from td_sync import sync_with_server


import tabsdata as td

db_username = td.EnvironmentSecret("mysql_username")
db_password = td.EnvironmentSecret("mysql_password")

@td.publisher(
    source=td.MySQLSource(
        uri="mysql://127.0.0.1:3306/tabsdata_db",
        query=[
            "SELECT * FROM `tabsdata_db`.`policy_dim`"
        ],
        credentials=td.UserPasswordCredentials(db_username, db_password),
    ),
    tables=["policy_dim"],
    trigger_by=["claims_fact_today"]
)
def policy_dim_pub(tf: td.TableFrame):
    return tf

sync_with_server()





