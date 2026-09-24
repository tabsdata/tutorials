#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, subscriber
from tabsdatak.conn.databricks import DatabricksDest


# Appends each load's fct_trip batch to Databricks; td_trx_id makes replaying
# a transaction a no-op.
@subscriber(
    input_tables=["nyc_gold/fct_trip@HEAD"],
    destination=DatabricksDest(
        tables=["fct_trip"],
        if_table_exists="append",
        schema_evolution="update",
        watermark_column="td_trx_id",
    ),
)
def sub_gold_fct_trip_to_databricks(fct_trip: TableFrameSpec) -> TableFrameSpec:
    return fct_trip
