#
# Copyright 2026 Tabsdata Inc.
#

"""script that builds the tabsdata project for this tutorial using the settings
in creds.json

    python tabsdata/run.py               # runs connector, deploy and load
    python tabsdata/run.py connector     # installs the github connector and the jev sdk locally and on the server
    python tabsdata/run.py deploy        # creates the project, group, collections and functions
    python tabsdata/run.py load          # reads the polars issues changed since the last load, which triggers the jev triage
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG_FILE = ROOT / "creds.json"
if not CONFIG_FILE.exists():
    sys.exit("copy creds-template.json to creds.json and fill in the jev section first")
CONFIG = json.loads(CONFIG_FILE.read_text())
TD, JEV, GITHUB = CONFIG["tabsdata"], CONFIG["jev"], CONFIG["github"]

# version of the jev sdk the transformer is written against
TYPESAFE_SDK = "typesafe-sdk==0.7.3"

GROUPS = ["TRIAGE"]

# maps the function folders to their collection and group
COLLECTIONS = {
    "01_source": ("github_landing", "sources"),
    "02_triage": ("issue_triage", "TRIAGE"),
}

# the transformer is registered from a copy with the jev api key filled in, since
# tabsdata has no secret store for transformers
TRANSFORMER = HERE / "functions" / "02_triage" / "tfr_triage_issues.py"
BUILD = HERE / "build"

# connection for the github connector, the token is optional and only raises
# github's rate limit, the secret: prefix makes tdk store it as a secret
GITHUB_CONNECTION = "\n".join(
    [
        "kind: connectionDef",
        "apiVersion: '1.0'",
        "type: tabsdata_github:GitHubSrcConn",
        "spec:",
        f"  token: secret:{GITHUB['token']}" if GITHUB.get("token") else "  api_url: str:https://api.github.com",
        "",
    ]
)


def run(*command: str, stdin: str | None = None, shown: str | None = None) -> None:
    print("$", shown or " ".join(command), flush=True)
    if subprocess.run(command, input=stdin, text=True).returncode != 0:
        sys.exit(f"failed: {shown or ' '.join(command)}")


def tdk(*args: str, stdin: str | None = None) -> None:
    run("tdk", "--no-prompt", *args, stdin=stdin)


def login() -> None:
    run("tdk", "--no-prompt", "login", "--server", TD["server"], "--user", TD["user"], "--password", TD["password"],
        shown=f"tdk login --server {TD['server']} --user {TD['user']}")


# helper function that writes the requirements a server venv should get, the ones
# the instance already holds are kept, like another tutorial's connector, and
# older lines for the github connector or the jev sdk are replaced
def requirements(venv: str) -> str:
    held = pathlib.Path.home() / ".tabsdata" / "instances" / TD["instance"] / "init" / "input" / "assets" / f"requirements-{venv}.txt"
    lines = held.read_text().splitlines() if held.exists() else []
    lines = [line for line in lines if not line.startswith(("tabsdata-conn-github", "typesafe-sdk"))]
    lines += [GITHUB["connector"], TYPESAFE_SDK]
    with tempfile.NamedTemporaryFile("w", suffix=f"-requirements-{venv}.txt", delete=False) as file:
        file.write("\n".join(lines) + "\n")
    return file.name


def connector() -> None:
    # installs the connector and the jev sdk locally so tdk can validate the
    # connection and register the functions
    run(sys.executable, "-m", "pip", "install", "--quiet", GITHUB["connector"], TYPESAFE_SDK)
    # installs them in the server's fn environment where the functions run and in
    # its ag environment where the tabsdata mcp checks connections
    for venv in ["fn", "ag"]:
        run("tdkserver", "venv", "update", "--instance", TD["instance"], "--name", venv,
            "--requirements", requirements(venv), "--details", "false", "--yes")
    # restarts the instance since venv update stops it
    run("tdkserver", "start", "--instance", TD["instance"], "--yes")


# helper function that writes the copy of the transformer with the jev api key
# filled in and returns its path
def transformer_with_key() -> pathlib.Path:
    BUILD.mkdir(exist_ok=True)
    copy = BUILD / TRANSFORMER.name
    copy.write_text(TRANSFORMER.read_text().replace('JEV_API_KEY = "?????"', f"JEV_API_KEY = {JEV['api_key']!r}"))
    return copy


def deploy() -> None:
    login()
    project = TD["project"]
    tdk("project", "create", "--name", project)
    for group in GROUPS:
        tdk("group", "create", "-P", project, "--name", group)
    tdk("collection", "create", "-P", project, "--name", "github_landing", "--group", "sources",
        "--conn-file", "-", stdin=GITHUB_CONNECTION)
    tdk("collection", "create", "-P", project, "--name", "issue_triage", "--group", "TRIAGE")
    tdk("fn", "register", "-P", project, "--coll", "github_landing",
        "--path", f"{HERE / 'functions' / '01_source' / 'pub_issues.py'}::pub_issues")
    tdk("fn", "register", "-P", project, "--coll", "issue_triage",
        "--path", f"{transformer_with_key()}::tfr_triage_issues")


def load() -> None:
    login()
    # the trigger waits for the plan to finish, the publisher's new issues
    # trigger the transformer in the same plan
    tdk("fn", "trigger", "-P", TD["project"], "--coll", "github_landing", "--name", "pub_issues",
        "--plan-name", f"load_{time.strftime('%Y%m%d_%H%M%S')}")


STEPS = {"connector": connector, "deploy": deploy, "load": load}


def main() -> None:
    steps = sys.argv[1:] or list(STEPS)
    unknown = [step for step in steps if step not in STEPS]
    if unknown:
        sys.exit(f"unknown step {unknown}; steps: {', '.join(STEPS)}")
    if "?????" in JEV["api_key"]:
        sys.exit("fill in jev.api_key in creds.json first (copy it from creds-template.json)")
    for step in steps:
        STEPS[step]()


if __name__ == "__main__":
    main()
