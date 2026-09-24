#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer
from tabsdatak.dataquality import DataQuality, Enrich, IsNotBetween, Summary
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, concat, lit

MAX_PASSENGER_COUNT = 6
VALID_CODES = (1, 6)


def typed(name: str, dtype: type[td_types.DataType], present: set[str]) -> Expr:
    # the column cast to dtype, or a null column of that type if the file lacks it
    return (col(name) if name in present else lit(None)).cast(dtype, strict=False).alias(name)


def key_part(name: str) -> Expr:
    return col(name).cast(td_types.String)


# Brings every batch to one set of column types and derives the trip_id key;
# the DataQuality action flags invalid passenger, payment and rate values.
@transformer(
    input_tables=["nyc_bronze/green_taxi_append_only_bronze@NEW"],
    output_tables=["green_taxi_standardized"],
    on_tables=[
        DataQuality(
            table="green_taxi_standardized",
            classifiers=[
                IsNotBetween(
                    [("passenger_count", "passenger_count_was_imputed")],
                    min_val=1,
                    max_val=MAX_PASSENGER_COUNT,
                    prefix="",
                ),
                IsNotBetween(
                    [("payment_type", "payment_type_was_imputed"), ("RatecodeID", "rate_code_was_imputed")],
                    min_val=VALID_CODES[0],
                    max_val=VALID_CODES[1],
                    prefix="",
                ),
            ],
            # verdict columns added to the table (0 = valid, 1 = out of range, 255 = null)
            # and a tally of invalid values per column
            operators=[Enrich(), Summary()],
        )
    ],
)
def tfr_green_taxi_standardized(new: TableFramesSpec) -> TableFrameSpec:
    frames = [frame for frame in (new or []) if frame is not None]
    if not frames:
        return None
    trips = concat(frames, how="diagonal_relaxed")

    # TLC changes column types between monthly files and adds columns over time
    # (cbd_congestion_fee in 2025, request_source in 2026-06)
    present = set(trips.columns)
    return trips.with_columns([
        # normalized TLC column types, null for columns this file lacks
        typed("VendorID", td_types.Int32, present),
        typed("PULocationID", td_types.Int64, present),
        typed("DOLocationID", td_types.Int64, present),
        typed("RatecodeID", td_types.Int32, present),
        typed("passenger_count", td_types.Int32, present),
        typed("payment_type", td_types.Int32, present),
        typed("trip_type", td_types.Int32, present),
        typed("ehail_fee", td_types.Float64, present),
        typed("store_and_fwd_flag", td_types.String, present),
        typed("cbd_congestion_fee", td_types.Float64, present),
        typed("request_source", td_types.String, present),
    ]).with_columns(
        # business key: when and where the trip started and ended, computed after
        # the casts so it is stable across files
        (
            key_part("@td.medallion.source_ts") + lit("||")
            + key_part("lpep_dropoff_datetime") + lit("||")
            + key_part("PULocationID") + lit("||")
            + key_part("DOLocationID")
        ).hash().alias("trip_id"),
    )
