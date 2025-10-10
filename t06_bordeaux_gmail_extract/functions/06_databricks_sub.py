import tabsdata as td
import os


@td.subscriber(
    tables=[
        "claims_fact_master_enriched",
        "open_pending_claims",
        "claims_last_90_days",
        "paid_amount_greater_10000",
    ],
    destination=td.DatabricksDestination(
        host_url=os.getenv("databricks_host_url"),
        token=td.EnvironmentSecret("databricks_token"),
        tables=[
            "claims_fact_master_enriched",
            "open_pending_claims",
            "claims_last_90_days",
            "paid_amount_greater_10000",
        ],
        volume=os.getenv("volume"),
        catalog=os.getenv("catalog"),
        schema=os.getenv("schema"),
        warehouse=os.getenv("warehouse"),
        if_table_exists="replace",
        schema_strategy="update",
    ),
)
def databricks_sub(
    claims_fact_master_enriched: td.TableFrame,
    open_pending_claims: td.TableFrame,
    claims_last_90_days: td.TableFrame,
    paid_amount_greater_10000: td.TableFrame,
):
    return (
        claims_fact_master_enriched,
        open_pending_claims,
        claims_last_90_days,
        paid_amount_greater_10000,
    )
