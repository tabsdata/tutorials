#
# Copyright 2026 Tabsdata Inc.
#

"""script that builds the tabsdata project for this tutorial using the settings
in creds.json

    python tabsdata/run.py               # runs connector, doris, deploy and load
    python tabsdata/run.py connector     # installs the doris connector locally and on the server
    python tabsdata/run.py doris         # creates the doris database and tables from doris/schema.sql
    python tabsdata/run.py deploy        # creates the project, groups, collections and functions
    python tabsdata/run.py load          # triggers the five publishers one plan at a time, each reads the log files added or changed in data/ since the last load and kicks off everything downstream
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CONNECTOR = ROOT / "doris_connector"
SCHEMA = ROOT / "doris" / "schema.sql"
CONFIG_FILE = ROOT / "creds.json"
if not CONFIG_FILE.exists():
    sys.exit("copy creds-template.json to creds.json and fill in the doris section first")
CONFIG = json.loads(CONFIG_FILE.read_text())
TD, DORIS = CONFIG["tabsdata"], CONFIG["doris"]
DATA = ROOT / CONFIG["dirs"]["data"]

GROUPS = ["SILVER", "GOLD"]

# maps the function folders to their collection and group
COLLECTIONS = {
    "01_source": ("logs_landing", "sources"),
    "02_silver": ("logs_silver", "SILVER"),
    "03_gold": ("logs_gold", "GOLD"),
    "04_destination": ("logs_doris", "destinations"),
}

# registration order, a function's input tables have to exist before it can be
# registered
FUNCTIONS = [
    "01_source/pub_logs.py::pub_frontend",
    "01_source/pub_logs.py::pub_gateway",
    "01_source/pub_logs.py::pub_services",
    "01_source/pub_logs.py::pub_payments",
    "01_source/pub_logs.py::pub_infra",
    "02_silver/tfr_log_events.py::tfr_log_events",
    "03_gold/tfr_checkout_requests.py::tfr_checkout_requests",
    "04_destination/sub_logs_to_doris.py::sub_log_events_to_doris",
    "04_destination/sub_logs_to_doris.py::sub_checkout_requests_to_doris",
]

# publishers the load step triggers, one per log source
PUBLISHERS = ["pub_frontend", "pub_gateway", "pub_services", "pub_payments", "pub_infra"]

DATA_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdatak.conn.localfile:LocalFileSrcConn
spec:
  base_path: str:{DATA}
"""

# optional s3 staging location for subscribers that use load_method="s3", added
# to the connection when doris.staging.bucket is set in creds.json, tdk resolves
# the keys from the DORIS__S3_ACCESS_KEY and DORIS__S3_SECRET_KEY env vars
STAGING = DORIS.get("staging") or {}
STAGING_LOCATION = f"""\
  staging:
    kind: dorisS3Location
    apiVersion: '1.0'
    type: tabsdata_doris:S3Location
    spec:
      bucket: str:{STAGING.get("bucket")}
      region: str:{STAGING.get("region")}
      credentials:
        kind: awsAccessSecretKeyCredentials
        apiVersion: '1.0'
        type: tabsdatak.conn.common.types:AwsAccessSecretKey
        spec:
          access_key_id: $secret:DORIS__S3_ACCESS_KEY
          secret_access_key: $secret:DORIS__S3_SECRET_KEY
      base_path: str:{STAGING.get("base_path") or "/"}
""" if STAGING.get("bucket") else ""

# connection for the custom doris connector, tdk resolves the user and password
# from the DORIS__USER and DORIS__PASSWORD env vars and stores them as secrets
DORIS_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdata_doris:DorisDestConn
spec:
  host: str:{DORIS["host"]}
  port: str:{DORIS["port"]}
  http_port: str:{DORIS["http_port"]}
  credentials:
    kind: userPasswordCredentials
    apiVersion: '1.0'
    type: tabsdatak.conn.common.types:UserPassword
    spec:
      user: $secret:DORIS__USER
      password: $secret:DORIS__PASSWORD
  database: str:{DORIS["database"]}
{STAGING_LOCATION}"""


def run(*command: str, stdin: str | None = None, shown: str | None = None) -> None:
    print("$", shown or " ".join(command), flush=True)
    if subprocess.run(command, input=stdin, text=True).returncode != 0:
        sys.exit(f"failed: {shown or ' '.join(command)}")


def tdk(*args: str, stdin: str | None = None) -> None:
    run("tdk", "--no-prompt", *args, stdin=stdin)


def login() -> None:
    run("tdk", "--no-prompt", "login", "--server", TD["server"], "--user", TD["user"], "--password", TD["password"],
        shown=f"tdk login --server {TD['server']} --user {TD['user']}")


def connector() -> None:
    # installs the connector locally so tdk can validate the connection and
    # register the subscribers
    run(sys.executable, "-m", "pip", "install", "--quiet", str(CONNECTOR))
    # installs the connector into the server's fn environment where the functions
    # run, venv update replaces the requirements the instance holds so the ones
    # already there are kept, like another tutorial's connector. on a remote
    # cluster swap the file path for the git url:
    # tabsdata-conn-doris @ git+https://github.com/tabsdata/tutorials.git#subdirectory=...
    held = pathlib.Path.home() / ".tabsdata" / "instances" / TD["instance"] / "init" / "input" / "assets" / "requirements-fn.txt"
    lines = held.read_text().splitlines() if held.exists() else []
    lines = [line for line in lines if not line.startswith("tabsdata-conn-doris")]
    lines.append(f"tabsdata-conn-doris @ {CONNECTOR.as_uri()}")
    with tempfile.NamedTemporaryFile("w", suffix="-requirements-fn.txt", delete=False) as requirements:
        requirements.write("\n".join(lines) + "\n")
    run("tdkserver", "venv", "update", "--instance", TD["instance"], "--name", "fn",
        "--requirements", requirements.name, "--details", "false", "--yes")
    # restarts the instance since venv update stops it
    run("tdkserver", "start", "--instance", TD["instance"], "--yes")


# helper function that splits the schema file into statements, drops the
# comment lines first so a semicolon in a comment doesn't split a statement
def statements(sql: str) -> list[str]:
    code = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    return [statement.strip() for statement in code.split(";") if statement.strip()]


def doris() -> None:
    import pymysql

    database = DORIS["database"]
    print(f"$ create database {database} and the tables in {SCHEMA.relative_to(ROOT)} on "
          f"{DORIS['host']}:{DORIS['port']}", flush=True)
    connection = pymysql.connect(host=DORIS["host"], port=int(DORIS["port"]), user=DORIS["user"],
                                 password=DORIS["password"], autocommit=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
            cursor.execute(f"USE `{database}`")
            for statement in statements(SCHEMA.read_text()):
                cursor.execute(statement)
            cursor.execute("SHOW TABLES")
            print("  tables:", ", ".join(row[0] for row in cursor.fetchall()))
    finally:
        connection.close()


def deploy() -> None:
    os.environ["DORIS__USER"] = DORIS["user"]
    os.environ["DORIS__PASSWORD"] = DORIS["password"]
    if STAGING.get("bucket"):
        os.environ["DORIS__S3_ACCESS_KEY"] = STAGING["access_key"]
        os.environ["DORIS__S3_SECRET_KEY"] = STAGING["secret_key"]

    login()
    project = TD["project"]
    tdk("project", "create", "--name", project)
    for group in GROUPS:
        tdk("group", "create", "-P", project, "--name", group)
    connections = {"sources": DATA_CONNECTION, "destinations": DORIS_CONNECTION}
    for collection, group in COLLECTIONS.values():
        if group in connections:
            tdk("collection", "create", "-P", project, "--name", collection, "--group", group,
                "--conn-file", "-", stdin=connections[group])
        else:
            tdk("collection", "create", "-P", project, "--name", collection, "--group", group)
    for function in FUNCTIONS:
        collection, _ = COLLECTIONS[function.split("/")[0]]
        tdk("fn", "register", "-P", project, "--coll", collection, "--path", str(HERE / "functions" / function))


def load() -> None:
    login()
    project, stamp = TD["project"], time.strftime("%Y%m%d_%H%M%S")
    # triggers the publishers one at a time and waits for each plan to finish so
    # the silver runs append to log_events in order instead of reading the same
    # head
    for publisher in PUBLISHERS:
        plan = f"load_{publisher.removeprefix('pub_')}_{stamp}"
        tdk("fn", "trigger", "-P", project, "--coll", "logs_landing", "--name", publisher, "--plan-name", plan)
        tdk("plan", "list", "--proj", project, "--name", plan, "--monitor")


STEPS = {"connector": connector, "doris": doris, "deploy": deploy, "load": load}


def main() -> None:
    steps = sys.argv[1:] or list(STEPS)
    unknown = [step for step in steps if step not in STEPS]
    if unknown:
        sys.exit(f"unknown step {unknown}; steps: {', '.join(STEPS)}")
    if any("?????" in str(value) for value in DORIS.values()):
        sys.exit("fill in the doris section of creds.json first (copy it from creds-template.json)")
    for step in steps:
        STEPS[step]()


if __name__ == "__main__":
    main()
