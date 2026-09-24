#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, subscriber
from tabsdatak.conn.databricks import DatabricksDest


# Replaces dim_zone and dim_date in Databricks on every dimension load.
@subscriber(
    input_tables=["nyc_gold/dim_zone@HEAD", "nyc_gold/dim_date@HEAD"],
    destination=DatabricksDest(tables=["dim_zone", "dim_date"], if_table_exists="replace"),
)
def sub_gold_dims_to_databricks(
    dim_zone: TableFrameSpec,
    dim_date: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec]:
    return dim_zone, dim_date
