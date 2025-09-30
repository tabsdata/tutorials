import os
import polars as pl
import requests
import tabsdata as td
from datetime import datetime
import io
from typing import List


class NycTaxiStatsSource(td.SourcePlugin):
    def chunk(self, working_dir: str) -> str:
        filenames = []
        data = []

        #get current datetime info
        now = datetime.now()
        year = now.year
        month = now.month
        timestamp = now.strftime("%Y%m%d%H%M%S")

        #create endpoints to append to base url for data
        months = [f"{year}-{m:02d}" for m in range(1, month)]

        #request to nyc taxi site and read parquet data into temp directory
        for i in months:
            endpoint = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{i}.parquet"
            try:
                payload = requests.get(endpoint)
                filename = f"yellow_tripdata_{i}"
                destination_file = f"{timestamp}_{filename}.parquet" 
                destination_path = os.path.join(working_dir, destination_file)
                with open(destination_path, "wb") as f:
                    f.write(payload.content)
                filenames.append(destination_file)
            except:
                payload = None
        return [filenames]


@td.publisher(
    source=NycTaxiStatsSource(),
    tables="nyc_taxi_stats",
)

def nyc_taxi_pub(tf: List[td.TableFrame]):
    return td.concat(tf)

