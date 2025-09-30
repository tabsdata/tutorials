import tabsdata as td
import polars as pl
from typing import List


@td.transformer(
    input_tables=["daily_taxi_metrics", "nyc_weather"],
    output_tables=[
        "taxi_metrics_with_weather"
    ],
)
def join_weather_trf(daily_taxi_metrics: td.TableFrame, nyc_weather: td.TableFrame): 
    daily_taxi_metrics = daily_taxi_metrics.join(nyc_weather, left_on="pickup_day", right_on="date", how="left").sort("pickup_day", descending = True)
    return daily_taxi_metrics

