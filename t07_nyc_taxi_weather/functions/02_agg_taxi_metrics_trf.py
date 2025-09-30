import tabsdata as td
import polars as pl
from typing import List



@td.transformer(
    input_tables=["nyc_taxi_stats"],
    output_tables=[
        "daily_taxi_metrics"
    ],

)
def agg_taxi_metrics_trf(nyc_taxi_stats: td.TableFrame): 
    #rename some columns, calculate minute duration of each trip, and cast pickup_datetime into Date format
    nyc_taxi_stats = nyc_taxi_stats.rename({'tpep_pickup_datetime': 'pickup_datetime', 'tpep_dropoff_datetime': 'dropoff_datetime'})
    nyc_taxi_stats = nyc_taxi_stats.with_columns([
        td.col("dropoff_datetime").sub(td.col("pickup_datetime")).alias("trip_duration").dt.total_minutes(),
        td.col("pickup_datetime").cast(td.Date).alias("pickup_day")
        ])
    
    #aggregate by day and calculate revenue/day, trips/day, driving time/day, and average trip duration/day
    tf_daily = nyc_taxi_stats.group_by(
        td.col("pickup_day")).agg(
            td.col("total_amount").sum(),
            td.col("pickup_day").count().alias("total_trips"),
            td.col("trip_duration").sum().alias('total_driving_time'),
            td.col("trip_duration").mean().alias('average_trip_time')
            )
    
    return tf_daily

