import os
import polars as pl
import requests
import tabsdata as td
from datetime import datetime, timedelta
import io


class WeatherNYCSource(td.SourcePlugin):
    def chunk(self, working_dir: str) -> str:
        now = datetime.now()
        today = now.date() - timedelta(days=1)
        timestamp = now.strftime("%Y%m%d%H%M%S")

        payload = requests.get(f'https://archive-api.open-meteo.com/v1/archive?latitude=40.7143&longitude=-74.006&start_date=2025-01-01&end_date={today}&daily=temperature_2m_mean,wind_speed_10m_max,precipitation_hours,sunshine_duration&timezone=America%2FNew_York').json()
        payload = pl.DataFrame(payload["daily"])

        filename = f"nyc_weather"
        destination_file = f"{timestamp}_{filename}.parquet" 
        destination_path = os.path.join(working_dir, destination_file)
        print(destination_path)
        payload.write_parquet(destination_path)
        
        return destination_file
      
@td.publisher(
    source=WeatherNYCSource(),
    tables="nyc_weather",
    trigger_by = ["nyc_taxi_stats"]
)

def weather_pub(tf: td.TableFrame):
    tf = tf.rename({"temperature_2m_mean":"temperature_celsius", "wind_speed_10m_max": "wind_speed", "precipitation_hours": "hours_precipitation"})
    tf = tf.with_columns(td.col("sunshine_duration").truediv(3600).round_sig_figs(3).alias('hours_sunshine'))
    tf = tf.drop('sunshine_duration')
    tf = tf.with_columns(td.col('time').cast(td.Date).alias('date'))

    return tf