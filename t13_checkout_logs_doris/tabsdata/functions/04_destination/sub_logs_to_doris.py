#
# Copyright 2026 Tabsdata Inc.
#

from tabsdata_doris import DorisDest
from tabsdatak.api import TableFrameSpec, TableFramesSpec, subscriber
from tabsdatak.tableframe.functions import concat


# subscriber that appends the events each silver run added to the doris
# log_events table, @NEW passes the new_log_events versions written since this
# subscriber last ran so every batch is loaded once. both subscribers stream load,
# load_method="s3" stages the files in the bucket set in creds.json instead
@subscriber(
    input_tables=["logs_silver/new_log_events@NEW"],
    destination=DorisDest(tables=["log_events"], if_table_exists="append", load_method="stream_load"),
)
def sub_log_events_to_doris(new_log_events: TableFramesSpec) -> TableFrameSpec:
    frames = [frame for frame in (new_log_events or []) if frame is not None]
    return concat(frames) if frames else None


# subscriber that replaces the doris checkout_requests table each time the gold
# table updates, the summaries change as later events of a checkout arrive
@subscriber(
    input_tables=["logs_gold/checkout_requests"],
    destination=DorisDest(tables=["checkout_requests"], if_table_exists="replace", load_method="stream_load"),
)
def sub_checkout_requests_to_doris(checkout_requests: TableFrameSpec) -> TableFrameSpec:
    return checkout_requests
