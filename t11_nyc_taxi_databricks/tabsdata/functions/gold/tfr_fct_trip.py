#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak._medallion.gold.fact import build_fact
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.functions import col, lit

PAYMENT_TYPE_NAMES = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}
RATE_TYPE_NAMES = {
    0: "Unknown",
    1: "Standard rate",
    2: "JFK",
    3: "Newark",
    4: "Nassau or Westchester",
    5: "Negotiated fare",
    6: "Group ride",
}
TIME_OF_DAY_NAMES = {
    hour: (
        "Morning Rush" if 6 <= hour <= 9
        else "Midday" if 10 <= hour <= 15
        else "Evening Rush" if 16 <= hour <= 19
        else "Night" if 20 <= hour <= 23
        else "Late Night"
    )
    for hour in range(24)
}


def with_label(frame: TableFrame, code_column: str, label_column: str, labels: dict[int, str]) -> TableFrame:
    lookup = TableFrame.from_dict({
        code_column: list(labels),
        label_column: list(labels.values()),
    })
    return frame.join(lookup, on=code_column, how="left").with_columns(
        col(label_column).fill_null(lit("Unknown"))
    )


# Trip fact: the new silver trips with their date key and time-of-day, payment
# and rate labels.
@transformer(
    input_tables=["nyc_silver/green_taxi_event_silver@NEW"],
    output_tables=["fct_trip"],
)
def tfr_fct_trip(events: TableFramesSpec) -> TableFrameSpec:
    fct = build_fact(events=events, dim_versions=[])
    if fct is None:
        return None

    fct = with_label(fct, "pickup_hour", "time_of_day", TIME_OF_DAY_NAMES)
    fct = with_label(fct, "payment_type", "payment_type_name", PAYMENT_TYPE_NAMES)
    fct = with_label(fct, "RatecodeID", "rate_type_name", RATE_TYPE_NAMES)
    return fct.with_columns(
        # date key as a regular column; @td.* columns do not leave Tabsdata
        col("@td.medallion.date_sk").alias("date_sk"),
    ).rename({
        "RatecodeID": "rate_code_id",
        "VendorID": "vendor_id",
        "lpep_dropoff_datetime": "dropoff_datetime",
        "pickup_date": "trip_date",
    })
