#
# Copyright 2026 Tabsdata Inc.
#

"""script that builds the tabsdata project for this tutorial using the settings
in usecase.json

    python tabsdata/run.py               # runs connector, deploy and load
    python tabsdata/run.py connector     # installs the motherduck connector locally and on the server
    python tabsdata/run.py deploy        # creates the project, groups, collections and functions
    python tabsdata/run.py load          # publishes the csvs in data/ which kicks off everything downstream
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CONNECTOR = ROOT / "motherduck_connector"
CONFIG_FILE = ROOT / "usecase.json"
if not CONFIG_FILE.exists():
    sys.exit("copy usecase-template.json to usecase.json and fill in the motherduck section first")
CONFIG = json.loads(CONFIG_FILE.read_text())
TD, MD = CONFIG["tabsdata"], CONFIG["motherduck"]
DATA = ROOT / CONFIG["dirs"]["data"]

GROUPS = ["SILVER", "GOLD"]

# maps the function folders to their collection and group
COLLECTIONS = {
    "01_source": ("vet_landing", "sources"),
    "02_silver": ("vet_silver", "SILVER"),
    "03_gold": ("vet_gold", "GOLD"),
    "04_destination": ("vet_motherduck", "destinations"),
}

# registration order, a function's input tables have to exist before it can be
# registered
FUNCTIONS = [
    "01_source/pub_pet_records.py::pub_pet_records",
    "02_silver/tfr_cases_silver.py::tfr_cases_silver",
    "02_silver/tfr_case_events_silver.py::tfr_case_events_silver",
    "02_silver/tfr_staff_silver.py::tfr_staff_silver",
    "03_gold/tfr_dimensions.py::tfr_dimensions",
    "03_gold/tfr_facts.py::tfr_facts",
    "04_destination/sub_gold_to_motherduck.py::sub_gold_to_motherduck",
]

DATA_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdatak.conn.localfile:LocalFileSrcConn
spec:
  base_path: str:{DATA}
"""

# connection for the custom motherduck connector, tdk resolves the token from the
# MOTHERDUCK__TOKEN env var and stores it as a secret
MOTHERDUCK_CONNECTION = f"""\
kind: connectionDef
apiVersion: '1.0'
type: tabsdata_motherduck:MotherDuckDestConn
spec:
  token: $secret:MOTHERDUCK__TOKEN
  database: str:{MD["database"]}
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


def connector() -> None:
    # installs the connector locally so tdk can validate the connection and
    # register the subscriber
    run(sys.executable, "-m", "pip", "install", "--quiet", str(CONNECTOR))
    # installs the connector into the server's fn environment where the functions
    # run. on a remote cluster swap the file path for the git url:
    # tabsdata-conn-motherduck @ git+https://github.com/tabsdata/tutorials.git#subdirectory=...
    with tempfile.NamedTemporaryFile("w", suffix="-requirements-fn.txt", delete=False) as requirements:
        requirements.write(f"tabsdata-conn-motherduck @ {CONNECTOR.as_uri()}\n")
    run("tdkserver", "venv", "update", "--instance", TD["instance"], "--name", "fn",
        "--requirements", requirements.name, "--details", "false", "--yes")
    # restarts the instance since venv update stops it
    run("tdkserver", "start", "--instance", TD["instance"], "--yes")


def deploy() -> None:
    os.environ["MOTHERDUCK__TOKEN"] = MD["token"]

    login()
    project = TD["project"]
    tdk("project", "create", "--name", project)
    for group in GROUPS:
        tdk("group", "create", "-P", project, "--name", group)
    connections = {"sources": DATA_CONNECTION, "destinations": MOTHERDUCK_CONNECTION}
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
    pets = len(list(DATA.glob("cases_*.csv")))
    tdk("fn", "trigger", "-P", TD["project"], "--coll", "vet_landing", "--name", "pub_pet_records",
        "--plan-name", f"{pets} pets")


STEPS = {"connector": connector, "deploy": deploy, "load": load}


def main() -> None:
    steps = sys.argv[1:] or list(STEPS)
    unknown = [step for step in steps if step not in STEPS]
    if unknown:
        sys.exit(f"unknown step {unknown}; steps: {', '.join(STEPS)}")
    if any(not value or "?????" in value for value in MD.values()):
        sys.exit("fill in the motherduck section of usecase.json first (copy it from usecase-template.json)")
    for step in steps:
        STEPS[step]()


if __name__ == "__main__":
    main()
