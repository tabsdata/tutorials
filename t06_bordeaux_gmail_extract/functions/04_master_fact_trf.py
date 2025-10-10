import tabsdata as td
import polars as pl
import requests
import io
import re


@td.transformer(
    input_tables=["policy_dim", "claims_fact_master"],
    output_tables=["claims_fact_master_enriched"],
)
def master_fact_trf(policy_dim: td.TableFrame, claims_fact: td.TableFrame):
    key = "policy_number"
    master = claims_fact.join(policy_dim, on=key, how="left")
    overlapping = list(set(policy_dim.columns()) & set(claims_fact.columns()) - {key})
    master = master.with_columns(
        [pl.coalesce(col + "_right", col).alias(col) for col in overlapping]
    )
    master = master.select(
        [
            col
            for col in master.columns()
            if col not in [i + "_right" for i in overlapping]
        ]
    )
    master = master.filter(td.col("claim_reference").is_not_null())
    return master
