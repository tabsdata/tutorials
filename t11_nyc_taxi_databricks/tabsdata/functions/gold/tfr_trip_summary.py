#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, TableFramesSpec, transformer
from tabsdatak.tableframe.functions import col, concat

SUMMARY_COLUMNS = [
    "trip_id",
    "trip_date",
    "date_sk",
    "year",
    "month",
    "month_name",
    "day_of_week",
    "day_name",
    "is_weekend",
    "quarter",
    "is_us_holiday",
    "pickup_hour",
    "time_of_day",
    "pickup_zone_key",
    "pickup_borough",
    "pickup_zone",
    "pickup_region_group",
    "pickup_zone_type",
    "pickup_is_manhattan",
    "dropoff_zone_key",
    "dropoff_borough",
    "dropoff_zone",
    "dropoff_region_group",
    "trip_duration_minutes",
    "trip_distance",
    "passenger_count",
    "fare_amount",
    "extra",
    "mta_tax",
    "improvement_surcharge",
    "tip_amount",
    "tolls_amount",
    "congestion_surcharge",
    "cbd_congestion_fee",
    "total_amount",
    "fare_per_mile",
    "tip_percentage",
    "payment_type",
    "payment_type_name",
    "rate_code_id",
    "rate_type_name",
    "anomaly_flag",
    "pickup_datetime",
    "dropoff_datetime",
    "trip_duration_seconds",
    "avg_speed_mph",
]


# The new fact rows with their date and pickup/dropoff zone attributes: the wide
# table the dashboards read. A dimension load brings no new facts and publishes nothing.
@transformer(
    input_tables=["fct_trip@NEW", "dim_zone@HEAD", "dim_date@HEAD"],
    output_tables=["trip_summary"],
)
def tfr_trip_summary(
    facts: TableFramesSpec,
    dim_zone: TableFrameSpec,
    dim_date: TableFrameSpec,
) -> TableFrameSpec:
    frames = [frame for frame in (facts or []) if frame is not None]
    if not frames or dim_zone is None or dim_date is None:
        return None

    # calendar attributes, keyed on the fact's date_sk
    dates = dim_date.select(
        "date_sk", "year", "month", "month_name", "day_of_week",
        "day_name", "is_weekend", "quarter", "is_us_holiday",
    )
    # zone attributes for the pickup end, keyed on the fact's PULocationID
    pickup_zones = dim_zone.select(
        col("zone_key").alias("PULocationID"),
        col("zone_key").alias("pickup_zone_key"),
        col("borough").alias("pickup_borough"),
        col("zone_name").alias("pickup_zone"),
        col("region_group").alias("pickup_region_group"),
        col("zone_type").alias("pickup_zone_type"),
        col("is_manhattan").alias("pickup_is_manhattan"),
    )
    # zone attributes for the dropoff end, keyed on the fact's DOLocationID
    dropoff_zones = dim_zone.select(
        col("zone_key").alias("DOLocationID"),
        col("zone_key").alias("dropoff_zone_key"),
        col("borough").alias("dropoff_borough"),
        col("zone_name").alias("dropoff_zone"),
        col("region_group").alias("dropoff_region_group"),
    )
    return (
        concat(frames, how="diagonal_relaxed")
        .join(dates, on="date_sk", how="left")
        .join(pickup_zones, on="PULocationID", how="left")
        .join(dropoff_zones, on="DOLocationID", how="left")
        .select(SUMMARY_COLUMNS)
    )
