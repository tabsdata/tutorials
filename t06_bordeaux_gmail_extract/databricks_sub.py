import tabsdata as td

@td.subscriber(
    tables=["claims_fact_master_enriched", "open_pending_claims", "claims_last_90_days","paid_amount_greater_10000"],
    destination=td.DatabricksDestination(
        host_url = td.EnvironmentSecret("databricks_host_url").secret_value,
        token = td.EnvironmentSecret("databricks_token").secret_value,
        tables = ["claims_fact_master_enriched", "open_pending_claims", "claims_last_90_days","paid_amount_greater_10000"],
        volume = "tpa_data",
        catalog = "tabsdata",
        schema = "default",
        warehouse = "tabsdata",
        if_table_exists = "replace",
        schema_strategy = "update"
    )
)

def databricks_sub(claims_fact_master_enriched: td.TableFrame, open_pending_claims: td.TableFrame, claims_last_90_days: td.TableFrame,paid_amount_greater_10000: td.TableFrame):
    return claims_fact_master_enriched, open_pending_claims, claims_last_90_days,paid_amount_greater_10000


