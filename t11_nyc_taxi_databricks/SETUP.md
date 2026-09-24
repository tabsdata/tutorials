<!-- Copyright 2026 Tabsdata Inc. -->

# Setting up Tabsdata

What you need before following the [runbook](README.md): a Python environment
with Tabsdata installed, a local Tabsdata server, and optionally an AI agent
connected to Tabsdata through MCP.

## 1. A Python environment

Tabsdata needs Python 3.12. Use whichever environment manager you prefer; run
the commands from this directory.

**venv**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**conda**

```bash
conda create -y -n tabsdata python=3.12
conda activate tabsdata
```

**pyenv** (with the pyenv-virtualenv plugin)

```bash
pyenv install 3.12
pyenv virtualenv 3.12 tabsdata
pyenv local tabsdata          # activates it whenever you are in this directory
```

## 2. Install Tabsdata

This use case was built and tested with **Tabsdata 2.1.0**; install that
version:

```bash
pip install "tabsdata[all]==2.1.0"
tdk --version
```

This installs the `tdk` client, the `tdkserver` server manager and the Python
API the functions in `tabsdata/functions/` are written against.

## 3. Configure and start a local server

```bash
tdkserver quickstart --provider kminus -y
```

`quickstart` creates and starts a local instance named `tabsdata` on
`http://localhost:2457`.

To use Tabsdata's AI capabilities, such as the agent built into the Tabsdata UI,
give the server an LLM API key when you create the instance:

```bash
tdkserver quickstart --provider kminus --anthropic-key "$ANTHROPIC_API_KEY" -y
# or: --openai-key "$OPENAI_API_KEY"
```

The runbook itself doesn't need a key, and an agent connected over MCP (next
section) uses its own model.

Check the instance and log in as the administrator (default user `admin`,
password `tabsdata`):

```bash
tdkserver list
tdk login --server localhost:2457 --user admin
```

Then create the user that runs the use case, `usecase` with password
`tabsdata`, and let it create projects:

```bash
tdk user create --name usecase --full-name "NYC taxi use case" --password tabsdata
tdk permission grant --user usecase --permission create_projects
```

A new user must change its password at first login; keeping the same one is
fine. Then log in as `usecase`:

```bash
tdk auth password-change localhost:2457 --user usecase --old-password tabsdata --new-password tabsdata
tdk login --server localhost:2457 --user usecase
```

These are the values the `tabsdata` section of `usecase.json` expects
(`localhost:2457`, `usecase`, `tabsdata`). If you change the port, the user or
the password, change them there too.

## 4. Connect an agent through MCP

The Tabsdata MCP server lets an AI agent work with the server: search the
docs and code examples, generate and verify functions, register them, run
them, and query tables. It runs locally and uses the session from `tdk login`, so
the agent works as `usecase`, with that user's permissions.

To install it in your agent (Claude Code, Cursor, Codex, VS Code and others),
follow [Connect an agent](https://docs.tabsdata.com/2.1.0/guide/connect-agent) in the
Tabsdata docs.

If the agent reports that the Tabsdata session is no longer valid, the login
expired or the server restarted: run `tdk login --server localhost:2457 --user usecase` again.

## 5. The Databricks CLI

Only the Databricks half of the runbook uses it:

```bash
brew tap databricks/tap && brew install databricks     # macOS
databricks --version
```

For Linux and Windows, see the
[Databricks CLI install guide](https://docs.databricks.com/aws/en/dev-tools/cli/install).

## 6. What Databricks needs

The use case writes four tables into a Databricks schema and deploys three
dashboards on top of them. The workspace must have Unity Catalog, and one
identity, a user or a service principal, does both.

| Item | What is needed | Goes in `usecase.json` |
| --- | --- | --- |
| Workspace | the workspace URL, e.g. `https://<id>.cloud.databricks.com` | `host` |
| Token | a personal access token for that identity (Settings → Developer → Access tokens); the workspace must allow PATs | `token` |
| SQL warehouse | a running or auto-starting SQL warehouse (serverless is simplest); the identity needs `CAN USE`. Tabsdata writes through it with `COPY INTO`, and the dashboards query through it | `warehouse_id` |
| Catalog | an existing catalog; `USE CATALOG`, plus `CREATE SCHEMA` if the schema does not exist yet | `catalog` |
| Schema | new, or existing and **empty**; `USE SCHEMA`, `CREATE TABLE`, `MODIFY`, `SELECT`, plus `CREATE VOLUME` if the volume does not exist yet | `schema` |
| Volume | a volume in that schema, where Tabsdata stages files before `COPY INTO`; `READ VOLUME`, `WRITE VOLUME` | `volume` |
| Dashboards | permission to create dashboards and workspace files; the bundle deploys under `/Workspace/Users/<identity>/.bundle/` | — |

`python databricks/run.py setup` creates the schema and the volume if they are
missing, so with `USE CATALOG` and `CREATE SCHEMA` on the catalog you only need
to name them. If your admin creates them for you instead, ask for the schema
and volume privileges above.

The warehouse id is in the warehouse's **Connection details**, as the last
part of the HTTP path (`/sql/1.0/warehouses/<warehouse_id>`).

The dashboards are published with the deploying identity's credentials, so
anyone you share them with sees the data without needing access to the schema.
