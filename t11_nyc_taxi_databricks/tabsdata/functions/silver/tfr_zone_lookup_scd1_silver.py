#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak._medallion.silver.scd import build_scd1_silver, build_scd1_silver_cleanse
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer
from tabsdatak.tableframe.functions import col


# Folds the zone change events into the latest state per LocationID.
@transformer(
    input_tables=[
        "nyc_bronze/zone_lookup_snp_bronze@NEW",
        "zone_lookup_scd1_raw@HEAD",
    ],
    output_tables=["zone_lookup_scd1_raw"],
)
def tfr_zone_lookup_scd1_raw(
    bronze: TableFramesSpec,
    scd1_head: TableFrameSpec,
) -> TableFrameSpec:
    return build_scd1_silver(bronze=bronze, scd1_head=scd1_head)


# The current zones without the SCD metadata, with names trimmed.
@transformer(
    input_tables=["zone_lookup_scd1_raw@NEW"],
    output_tables=["zone_lookup_current_silver"],
)
def tfr_zone_lookup_current_silver(scd1_raw: TableFramesSpec) -> TableFrameSpec:
    cleansed = build_scd1_silver_cleanse(scd1_raw=scd1_raw)
    if cleansed is None:
        return None
    return cleansed.with_columns([
        # trimmed zone names
        col("Borough").str.strip_chars(),
        col("Zone").str.strip_chars(),
        col("service_zone").str.strip_chars(),
    ])
