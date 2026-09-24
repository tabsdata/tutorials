#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak._medallion.bronze.snapshot_diff_cdc import build_snapshot_diff_cdc_bronze
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer


# Converts consecutive zone snapshots into I/U/D change events.
@transformer(
    input_tables=[
        "nyc_landing/zone_lookup_snp_raw@HEAD",
        "nyc_landing/zone_lookup_snp_raw@HEAD^",
        "nyc_landing/zone_lookup_snp_raw@NEW",
    ],
    output_tables=["zone_lookup_snp_bronze"],
)
def tfr_zone_lookup_snapshot_diff_bronze(
    head: TableFrameSpec,
    prev: TableFrameSpec,
    new: TableFramesSpec,
) -> TableFrameSpec:
    return build_snapshot_diff_cdc_bronze(
        prev=prev,
        head=head,
        new=new,
        pk=[{"LocationID": td_types.Int64}],
    )
