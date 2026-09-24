#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak._medallion.silver.append_only import build_append_only_silver
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer


# Appends the checked trips, one row per trip_id, skipping trips already in silver.
@transformer(
    input_tables=[
        "green_taxi_checked@NEW",
        "green_taxi_event_silver@HEAD",
    ],
    output_tables=["green_taxi_event_silver"],
)
def tfr_green_taxi_event_silver(
    checked: TableFramesSpec,
    silver: TableFrameSpec,
) -> TableFrameSpec:
    return build_append_only_silver(bronze_new=checked, silver_head=silver)
