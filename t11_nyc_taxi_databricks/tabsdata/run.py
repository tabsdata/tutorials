#
# Copyright 2026 Tabsdata Inc.
#

"""The Tabsdata part of the use case, configured by usecase.json at the root of this directory.

    python tabsdata/run.py              # download, deploy, load
    python tabsdata/run.py download     # TLC files into the cache, each fetched once
    python tabsdata/run.py deploy       # project, groups, collections, functions
    python tabsdata/run.py load         # dimensions once, then one month per transaction
"""

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Iterator

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG = json.loads((ROOT / "usecase.json").read_text())
TD, TLC, DBX = CONFIG["tabsdata"], CONFIG["tlc"], CONFIG["databricks"]
CACHE = ROOT / CONFIG["dirs"]["cache"]
LANDING = ROOT / CONFIG["dirs"]["landing"]
ZONE_FILE = "taxi_zone_lookup.csv"

GROUPS = ["BRONZE", "SILVER", "GOLD"]

# function directory -> (collection, group)
COLLECTIONS = {
    "source": ("nyc_landing", "sources"),
    "bronze": ("nyc_bronze", "BRONZE"),
    "silver": ("nyc_silver", "SILVER"),
    "gold": ("nyc_gold", "GOLD"),
    "destination": ("nyc_databricks", "destinations"),
}

# registration order: a function's input tables must already exist
FUNCTIONS = [
    "source/publish_green_taxi_appends.py::publish_green_taxi_appends",
    "source/publish_zone_lookup_snapshot.py::publish_zone_lookup_snapshot",
    "bronze/tfr_green_taxi_append_only_bronze.py::tfr_green_taxi_append_only_bronze",
    "bronze/tfr_zone_lookup_snapshot_diff_bronze.py::tfr_zone_lookup_snapshot_diff_bronze",
    "silver/tfr_green_taxi_standardized.py::tfr_green_taxi_standardized",
    "silver/tfr_green_taxi_quality.py::tfr_green_taxi_quality",
    "silver/tfr_green_taxi_event_silver.py::tfr_green_taxi_event_silver",
    "silver/tfr_zone_lookup_scd1_silver.py::tfr_zone_lookup_scd1_raw",
    "silver/tfr_zone_lookup_scd1_silver.py::tfr_zone_lookup_current_silver",
    "gold/tfr_dim_zone_type1.py::tfr_dim_zone_type1",
    "gold/tfr_dim_date.py::tfr_dim_date",
    "gold/tfr_fct_trip.py::tfr_fct_trip",
    "gold/tfr_trip_summary.py::tfr_trip_summary",
    "destination/sub_gold_dims_to_databricks.py::sub_gold_dims_to_databricks",
    "destination/sub_gold_fct_trip_to_databricks.py::sub_gold_fct_trip_to_databricks",
    "destination/sub_gold_trip_summary_to_databricks.py::sub_gold_trip_summary_to_databricks",
]

LANDING_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdatak.conn.localfile:LocalFileSrcConn
spec:
  base_path: str:{LANDING}
"""

# Tabsdata's egress connection; host and token are read by tdk from the environment and stored as secrets
DATABRICKS_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdatak.conn.databricks:DatabricksDestConn
spec:
  host_url: $secret:DATABRICKS__HOST
  token: $secret:DATABRICKS__TOKEN
  volume: str:{DBX["volume"]}
  warehouse_id: str:{DBX["warehouse_id"]}
  catalog: str:{DBX["catalog"]}
  schema: str:{DBX["schema"]}
"""


def run(*command: str, stdin: str | None = None, shown: str | None = None) -> None:
    print("$", shown or " ".join(command), flush=True)
    if subprocess.run(command, input=stdin, text=True).returncode != 0:
        sys.exit(f"failed: {shown or ' '.join(command)}")


def tdk(*args: str, stdin: str | None = None) -> None:
    run("tdk", "--no-prompt", *args, stdin=stdin)


def login() -> None:
    run("tdk", "--no-prompt", "login", "--server", TD["server"], "--user", TD["user"], "--password", TD["password"],
        shown=f"tdk login --server {TD['server']} --user {TD['user']}")


def months() -> Iterator[str]:
    year, month = map(int, TLC["first_month"].split("-"))
    today = datetime.date.today()
    last = tuple(map(int, TLC["last_month"].split("-"))) if TLC["last_month"] else (today.year, today.month)
    while (year, month) <= last:
        yield f"{year:04d}-{month:02d}"
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def fetch(url: str, target: pathlib.Path) -> bool:
    if target.exists():
        return True
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD")).close()
    except urllib.error.HTTPError as error:
        if error.code in (403, 404):
            return False
        raise
    target.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, target.with_suffix(".part"))
    target.with_suffix(".part").rename(target)
    print(f"downloaded {target.relative_to(ROOT)}")
    return True


def cached_months() -> list[pathlib.Path]:
    return sorted(CACHE.glob("trips/green_tripdata_*.parquet"))


def download() -> None:
    fetch(f"{TLC['base_url']}/misc/{ZONE_FILE}", CACHE / "zones" / ZONE_FILE)
    for month in months():
        name = f"green_tripdata_{month}.parquet"
        if not fetch(f"{TLC['base_url']}/trip-data/{name}", CACHE / "trips" / name):
            print(f"{month} is not published yet")
            break
    print(f"cache: {len(cached_months())} month(s)")


def deploy() -> None:
    os.environ["DATABRICKS__HOST"] = DBX["host"]
    os.environ["DATABRICKS__TOKEN"] = DBX["token"]
    (LANDING / "trips").mkdir(parents=True, exist_ok=True)
    (LANDING / "zones").mkdir(parents=True, exist_ok=True)

    login()
    project = TD["project"]
    tdk("project", "create", "--name", project)
    for group in GROUPS:
        tdk("group", "create", "-P", project, "--name", group)
    connections = {"sources": LANDING_CONNECTION, "destinations": DATABRICKS_CONNECTION}
    for collection, group in COLLECTIONS.values():
        if group in connections:
            tdk("collection", "create", "-P", project, "--name", collection, "--group", group,
                "--conn-file", "-", stdin=connections[group])
        else:
            tdk("collection", "create", "-P", project, "--name", collection, "--group", group)
    for function in FUNCTIONS:
        collection, _ = COLLECTIONS[function.split("/")[0]]
        tdk("fn", "register", "-P", project, "--coll", collection, "--path", str(HERE / "functions" / function))


def trigger(function: str, plan_name: str) -> None:
    tdk("fn", "trigger", "-P", TD["project"], "--coll", "nyc_landing", "--name", function, "--plan-name", plan_name)


def stage(source: pathlib.Path, target: pathlib.Path) -> None:
    # copyfile gives the copy a new modification time, which the trip publisher's cutoff relies on
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def load() -> None:
    login()
    zones = LANDING / "zones" / ZONE_FILE
    if not zones.exists():
        stage(CACHE / "zones" / ZONE_FILE, zones)
        trigger("publish_zone_lookup_snapshot", "dimensions")
    for source in cached_months():
        month = source.stem.removeprefix("green_tripdata_")
        target = LANDING / "trips" / f"green_{month}.parquet"
        if not target.exists():
            stage(source, target)
            trigger("publish_green_taxi_appends", f"trips {month}")
    print(f"loaded: {len(list(LANDING.glob('trips/*.parquet')))} month(s)")


STEPS = {"download": download, "deploy": deploy, "load": load}


def main() -> None:
    steps = sys.argv[1:] or list(STEPS)
    unknown = [step for step in steps if step not in STEPS]
    if unknown:
        sys.exit(f"unknown step {unknown}; steps: {', '.join(STEPS)}")
    if any(not value or "?????" in value or "<" in value for value in DBX.values()):
        sys.exit("fill in the databricks section of usecase.json first (copy it from usecase-template.json)")
    for step in steps:
        STEPS[step]()


if __name__ == "__main__":
    main()
