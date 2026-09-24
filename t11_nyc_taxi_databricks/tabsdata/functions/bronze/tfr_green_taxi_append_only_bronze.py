#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak._medallion.bronze.append_only_cdc import build_append_only_cdc_bronze
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer


# Every trip is an insert.
@transformer(
    input_tables=["nyc_landing/green_taxi_append_raw@NEW"],
    output_tables=["green_taxi_append_only_bronze"],
)
def tfr_green_taxi_append_only_bronze(new: TableFramesSpec) -> TableFrameSpec:
    return build_append_only_cdc_bronze(
        new=new,
        pk=[{"trip_id": td_types.UInt64}],
        event_ts_col="lpep_pickup_datetime",
    )
