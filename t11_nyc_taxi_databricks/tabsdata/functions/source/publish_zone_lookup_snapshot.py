#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, TableFramesSpec, publisher
from tabsdatak.conn.localfile import LocalFileSrc


# Full snapshot of the zone lookup on every run; bronze diffs snapshots.
@publisher(
    source=LocalFileSrc(
        paths=["zones/taxi_zone_lookup.csv"],
        src_cfg={"tabsdata.src_metadata.drop": True},
    ),
    output_tables=["zone_lookup_snp_raw"],
)
def publish_zone_lookup_snapshot(zones: TableFramesSpec) -> TableFrameSpec:
    return zones[0] if zones else None
