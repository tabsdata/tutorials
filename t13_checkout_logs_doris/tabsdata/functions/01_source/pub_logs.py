#
# Copyright 2026 Tabsdata Inc.
#

from datetime import datetime, timezone

from tabsdatak.api import TableFrameSpec, TableFramesSpec, publisher
from tabsdatak.conn.localfile import LocalFileSrc, SrcFileFormat
from tabsdatak.tableframe.functions import concat

# cursor start for the incremental loads, the first run reads every file and
# later runs only read files added or modified since the previous run
SINCE = datetime(2000, 1, 1, tzinfo=timezone.utc)
DROP_FILE_PATH = {"tabsdata.src_metadata.drop": True}


# helper function that takes the list of TableFrames read from the matched files
# and concats them using the "diagonal_relaxed" scheme to avoid type mismatching
# or schema ordering differences between files, None when no files changed
def new_files(frames: TableFramesSpec) -> TableFrameSpec:
    frames = [frame for frame in (frames or []) if frame is not None]
    return concat(frames, how="diagonal_relaxed") if frames else None


# publisher that reads the browser analytics events, ndjson with camelCase fields
# and epoch millisecond timestamps, standing in for a kafka topic export
@publisher(
    source=LocalFileSrc(
        paths=["frontend/web_events_*.jsonl"],
        format=SrcFileFormat.JSON,
        initial_last_modified=SINCE,
        src_cfg=DROP_FILE_PATH,
    ),
    output_tables=["raw_frontend"],
)
def pub_frontend(frontend: TableFramesSpec) -> TableFrameSpec:
    return new_files(frontend)


# publisher that reads the api gateway access logs as plain text, the LOG format
# returns each line as one message column so the transformer can grok it
@publisher(
    source=LocalFileSrc(
        paths=["gateway/access_*.log"],
        format=SrcFileFormat.LOG,
        initial_last_modified=SINCE,
        src_cfg=DROP_FILE_PATH,
    ),
    output_tables=["raw_gateway"],
)
def pub_gateway(gateway: TableFramesSpec) -> TableFrameSpec:
    return new_files(gateway)


# publisher that reads the structured logs of the auth, cart, catalog, checkout
# and orders services, ndjson with snake_case fields and ISO timestamps
@publisher(
    source=LocalFileSrc(
        paths=["services/app_*.jsonl"],
        format=SrcFileFormat.JSON,
        initial_last_modified=SINCE,
        src_cfg=DROP_FILE_PATH,
    ),
    output_tables=["raw_services"],
)
def pub_services(services: TableFramesSpec) -> TableFrameSpec:
    return new_files(services)


# publisher that reads the payment provider webhook events exported from the
# payments database as csv
@publisher(
    source=LocalFileSrc(
        paths=["payments/payment_events_*.csv"],
        format=SrcFileFormat.CSV,
        initial_last_modified=SINCE,
        src_cfg=DROP_FILE_PATH,
    ),
    output_tables=["raw_payments"],
)
def pub_payments(payments: TableFramesSpec) -> TableFrameSpec:
    return new_files(payments)


# publisher that reads the orders database postgres logs exported from
# cloudwatch, ndjson where the log line itself is in the message field
@publisher(
    source=LocalFileSrc(
        paths=["infra/orders_db_*.jsonl"],
        format=SrcFileFormat.JSON,
        initial_last_modified=SINCE,
        src_cfg=DROP_FILE_PATH,
    ),
    output_tables=["raw_infra"],
)
def pub_infra(infra: TableFramesSpec) -> TableFrameSpec:
    return new_files(infra)
