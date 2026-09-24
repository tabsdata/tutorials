#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer
from tabsdatak.dataquality import (
    AnyFailed,
    DataQuality,
    Fail,
    Filter,
    IsBetween,
    IsFalse,
    IsNotNull,
    IsPositive,
    IsPositiveOrZero,
    PercentThreshold,
    Summary,
)
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, concat, lit

PICKUP = "@td.medallion.source_ts"

MAX_TRIP_DISTANCE_MI = 100.0
MAX_TRIP_DURATION_MIN = 1440.0
MAX_FARE_AMOUNT = 500.0
MAX_TOTAL_AMOUNT = 500.0
MAX_TIP_AMOUNT = 200.0
MAX_TOLLS_AMOUNT = 200.0
MAX_PASSENGER_COUNT = 6

UNKNOWN_PAYMENT_TYPE = 5
UNKNOWN_RATE_CODE = 0

ANOMALY_LABELS = {0: "NORMAL", 1: "EXTREME_DISTANCE", 2: "EXTREME_FARE"}

TIMESTAMPS_TAG = "timestamps"
ZERO_MILES_TAG = "zero_miles"
REVERSED_TAG = "reversed"
OUTLIER_TAG = "outlier"
DUPLICATES_TAG = "duplicates"

# Rows failing these tags are discarded; duplicates are kept and deduped in silver.
CONTENT_TAGS = [TIMESTAMPS_TAG, ZERO_MILES_TAG, REVERSED_TAG, OUTLIER_TAG]


def or_default(value: Expr, invalid: Expr, default: int) -> Expr:
    """`default` where `invalid` holds, `value` elsewhere (there is no when/then)."""
    bad = invalid.cast(td_types.Int32)
    return value.fill_null(default) * (lit(1) - bad) + lit(default) * bad


def ratio(numerator: Expr, denominator: Expr, absent: float | None = None) -> Expr:
    """`numerator / denominator` where the denominator is positive, else `absent`."""
    keep = (denominator > lit(0)).cast(td_types.Float64)
    return ((numerator * keep) / (denominator * keep)).round(2).fill_nan(absent)


# Imputes the values standardization flagged and derives the trip measures;
# the DataQuality action does every accept/reject decision.
@transformer(
    input_tables=["green_taxi_standardized@NEW"],
    output_tables=["green_taxi_checked"],
    on_tables=[
        DataQuality(
            table="green_taxi_checked",
            classifiers=[
                IsNotNull([("lpep_dropoff_datetime", "dropoff_present")], tags=[TIMESTAMPS_TAG]),
                IsBetween(
                    [("trip_duration_minutes", "duration_sane")],
                    min_val=0.0,
                    max_val=MAX_TRIP_DURATION_MIN,
                    closed_on="upper",
                    tags=[TIMESTAMPS_TAG, OUTLIER_TAG],
                ),
                IsPositive([("trip_distance", "distance_positive")], tags=[ZERO_MILES_TAG]),
                IsPositiveOrZero(
                    [("fare_amount", "fare_not_negative"), ("total_amount", "total_not_negative")],
                    tags=[REVERSED_TAG],
                ),
                IsBetween([("trip_distance", "distance_in_range")], max_val=MAX_TRIP_DISTANCE_MI, tags=[OUTLIER_TAG]),
                IsBetween([("fare_amount", "fare_in_range")], max_val=MAX_FARE_AMOUNT, tags=[OUTLIER_TAG]),
                IsBetween([("total_amount", "total_in_range")], max_val=MAX_TOTAL_AMOUNT, tags=[OUTLIER_TAG]),
                IsBetween([("tip_amount", "tip_in_range")], max_val=MAX_TIP_AMOUNT, tags=[OUTLIER_TAG]),
                IsBetween([("tolls_amount", "tolls_in_range")], max_val=MAX_TOLLS_AMOUNT, tags=[OUTLIER_TAG]),
                IsFalse([("is_duplicate", "trip_id_unique")], tags=[DUPLICATES_TAG]),
            ],
            operators=[
                Filter(
                    AnyFailed(tags=CONTENT_TAGS),
                    to_table="green_taxi_discarded",
                    include_quality_columns="all",
                ),
                Summary(table="green_taxi_dq_summary"),
                Fail(AnyFailed(), PercentThreshold(50)),
            ],
        )
    ],
)
def tfr_green_taxi_quality(new: TableFramesSpec) -> TableFrameSpec:
    frames = [frame for frame in (new or []) if frame is not None]
    if not frames:
        return None
    trips = concat(frames, how="diagonal_relaxed")

    trips = trips.with_columns([
        # verdicts from tfr_green_taxi_standardized as flags: out of range (1) or null (255) is True
        col("passenger_count_was_imputed").cast(td_types.Boolean),
        col("payment_type_was_imputed").cast(td_types.Boolean),
        col("rate_code_was_imputed").cast(td_types.Boolean),
    ]).with_columns([
        # passenger count clamped to 1..6, unknown codes for invalid payment and rate
        col("passenger_count").fill_null(1).clip(1, MAX_PASSENGER_COUNT),
        or_default(col("payment_type"), col("payment_type_was_imputed"), UNKNOWN_PAYMENT_TYPE),
        or_default(col("RatecodeID"), col("rate_code_was_imputed"), UNKNOWN_RATE_CODE),
    ])

    pickup = col(PICKUP)
    dropoff = col("lpep_dropoff_datetime").dt.replace_time_zone("UTC")  # same UTC label as pickup
    seconds = (dropoff - pickup).dt.total_seconds()
    distance = col("trip_distance")
    fare = col("fare_amount")
    trips = trips.with_columns([
        # pickup and dropoff as regular columns, pickup date/hour/weekday (1=Sunday)
        pickup.alias("pickup_datetime"),
        dropoff.alias("lpep_dropoff_datetime"),
        pickup.dt.date().alias("pickup_date"),
        pickup.dt.hour().alias("pickup_hour"),
        (pickup.dt.weekday() % lit(7) + lit(1)).alias("pickup_day_of_week"),
        # trip time and speed
        seconds.alias("trip_duration_seconds"),
        (seconds / lit(60)).round(2).alias("trip_duration_minutes"),
        ratio(distance * lit(3600.0), seconds.cast(td_types.Float64)).alias("avg_speed_mph"),
        # money measures
        ((fare < lit(0)) | (col("total_amount") < lit(0))).alias("is_reversed"),
        ratio(fare, distance).alias("fare_per_mile"),
        ratio(col("tip_amount") * lit(100), fare, absent=0.0).alias("tip_percentage"),
        # 1 = extreme distance, 2 = extreme fare, 0 = normal
        (
            (distance > lit(MAX_TRIP_DISTANCE_MI)).cast(td_types.Int32)
            + ((distance <= lit(MAX_TRIP_DISTANCE_MI)) & (fare > lit(MAX_FARE_AMOUNT))).cast(td_types.Int32) * lit(2)
        ).alias("anomaly_code"),
        # trips whose trip_id appears more than once in this batch
        col("trip_id").is_unique().not_().alias("is_duplicate"),
    ])

    # anomaly code to label
    labels = TableFrame.from_dict({
        "anomaly_code": list(ANOMALY_LABELS),
        "anomaly_flag": list(ANOMALY_LABELS.values()),
    })
    return trips.join(labels, on="anomaly_code", how="left").drop("anomaly_code")
