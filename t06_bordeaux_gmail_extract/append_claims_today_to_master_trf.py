import tabsdata as td
import polars as pl
import requests
import io
import re
import datetime as dt


@td.transformer(
    input_tables=["claims_fact_today","claims_fact_master"],
    output_tables=[
       "claims_fact_master"
    ],
)


def append_claims_today_to_master_trf(claims_fact_today: td.TableFrame, claims_fact_master: td.TableFrame):
    if claims_fact_master is None:
        claims_fact_master = claims_fact_today.clear()
    claims_fact_master = td.concat([claims_fact_today,claims_fact_master])
    return claims_fact_master
