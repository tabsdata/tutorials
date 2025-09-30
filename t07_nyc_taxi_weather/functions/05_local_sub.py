import tabsdata as td
import os

@td.subscriber(
    tables=["taxi_metrics_with_weather"],
    destination=td.LocalFileDestination([os.path.join(os.path.dirname(os.getcwd()), "output", "taxi_metrics_with_weather_$EXPORT_TIMESTAMP.csv")]),
    )
def local_sub(tf1: td.TableFrame):
    return tf1