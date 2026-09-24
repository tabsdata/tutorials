#
# Copyright 2026 Tabsdata Inc.
#

"""The Databricks part of the use case, configured by usecase.json at the root of this directory.

    python databricks/run.py setup        # schema and staging volume, if missing
    python databricks/run.py dashboards   # the three dashboards, reading trip_summary
"""

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DBX = json.loads((HERE.parent / "usecase.json").read_text())["databricks"]


def run(*command: str, cwd: pathlib.Path | None = None) -> None:
    print("$", " ".join(command), flush=True)
    if subprocess.run(command, cwd=cwd).returncode != 0:
        sys.exit(f"failed: {' '.join(command)}")


def sql(statement: str) -> list[list[str]]:
    print("$ sql:", statement, flush=True)
    body = json.dumps({"statement": statement, "warehouse_id": DBX["warehouse_id"], "wait_timeout": "50s"})
    result = subprocess.run(["databricks", "api", "post", "/api/2.0/sql/statements", "--json", body],
                            text=True, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"failed: {statement}\n{result.stderr}")
    response = json.loads(result.stdout)
    if response["status"]["state"] != "SUCCEEDED":
        sys.exit(f"failed: {statement}\n{response['status']}")
    return response.get("result", {}).get("data_array", [])


def setup() -> None:
    schema = f"`{DBX['catalog']}`.`{DBX['schema']}`"
    sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    sql(f"CREATE VOLUME IF NOT EXISTS {schema}.`{DBX['volume']}`")
    tables = [row[1] for row in sql(f"SHOW TABLES IN {schema}")]
    print(f"{schema} is ready; tables: {tables or 'none'}")


def dashboards() -> None:
    for name in ("warehouse_id", "catalog", "schema"):
        os.environ[f"BUNDLE_VAR_{name}"] = DBX[name]
    run("databricks", "bundle", "deploy", "-t", "dev", cwd=HERE / "dashboards")
    run("databricks", "bundle", "summary", "-t", "dev", cwd=HERE / "dashboards")


STEPS = {"setup": setup, "dashboards": dashboards}


def main() -> None:
    steps = sys.argv[1:] or list(STEPS)
    unknown = [step for step in steps if step not in STEPS]
    if unknown:
        sys.exit(f"unknown step {unknown}; steps: {', '.join(STEPS)}")
    if any(not value or "?????" in value or "<" in value for value in DBX.values()):
        sys.exit("fill in the databricks section of usecase.json first (copy it from usecase-template.json)")
    os.environ["DATABRICKS_HOST"] = DBX["host"]
    os.environ["DATABRICKS_TOKEN"] = DBX["token"]
    for step in steps:
        STEPS[step]()


if __name__ == "__main__":
    main()
