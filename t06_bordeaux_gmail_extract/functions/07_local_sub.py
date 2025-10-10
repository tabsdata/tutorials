import os
import tabsdata as td

tables = [
    "claims_fact_master_enriched",
    "open_pending_claims",
    "claims_last_90_days",
    "paid_amount_greater_10000",
]
destination = [
    os.path.join(os.path.dirname(os.getcwd()), "output", f"{i}_$EXPORT_TIMESTAMP.jsonl")
    for i in tables
]


@td.subscriber(
    tables=tables,
    destination=td.LocalFileDestination(destination),
)
def local_sub(
    claims_fact_master_enriched,
    open_pending_claims,
    claims_last_90_days,
    paid_amount_greater_10000,
):
    return (
        claims_fact_master_enriched,
        open_pending_claims,
        claims_last_90_days,
        paid_amount_greater_10000,
    )
