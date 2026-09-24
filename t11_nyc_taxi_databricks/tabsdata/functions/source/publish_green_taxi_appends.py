#
# Copyright 2026 Tabsdata Inc.
#

from datetime import datetime, timezone

from tabsdatak.api import TableFrameSpec, TableFramesSpec, publisher
from tabsdatak.conn.localfile import LocalFileSrc
from tabsdatak.tableframe.functions import concat


# Loads the trip files that landed since the last run, as they are.
@publisher(
    source=LocalFileSrc(
        paths=["trips/green_*.parquet"],
        initial_last_modified=datetime(2000, 1, 1, tzinfo=timezone.utc),
    ),
    output_tables=["green_taxi_append_raw"],
)
def publish_green_taxi_appends(trips: TableFramesSpec) -> TableFrameSpec:
    return concat(trips, how="diagonal_relaxed")
