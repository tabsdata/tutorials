#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, subscriber
from tabsdatak.conn.databricks import DatabricksDest


# Appends each load's trip_summary batch to Databricks; td_trx_id makes replaying
# a transaction a no-op.
@subscriber(
    input_tables=["nyc_gold/trip_summary@HEAD"],
    destination=DatabricksDest(
        tables=["trip_summary"],
        if_table_exists="append",
        schema_evolution="update",
        watermark_column="td_trx_id",
    ),
)
def sub_gold_trip_summary_to_databricks(trip_summary: TableFrameSpec) -> TableFrameSpec:
    return trip_summary
