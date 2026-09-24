<!-- Copyright 2026 Tabsdata Inc. -->

# NYC Taxi on Tabsdata — runbook

NYC TLC green-taxi trips (January 2026 on) ingested by Tabsdata, taken through
bronze, silver and gold with declarative data quality, and published to
Databricks, where the three dashboards of the
[original use case](https://github.com/Hamza-Bouali/NYC-DATABRICKS) read them.
The story is in [blog/BLOG.md](blog/BLOG.md).

The repository has two parts, and so does this runbook:

| | Directory | What it holds | Run with |
| --- | --- | --- | --- |
| **Tabsdata** | `tabsdata/` | the pipeline: ingestion, medallion layers, data quality, egress to Databricks | `python tabsdata/run.py` |
| **Databricks** | `databricks/` | the target schema, and the dashboards that read what Tabsdata publishes | `python databricks/run.py` |

Both read one configuration file, `usecase.json`.

## 0. Prerequisites

- Tabsdata installed with a local server running: see [SETUP.md](SETUP.md).
- The Databricks CLI (also in SETUP.md).
- A Databricks workspace, identity, token, warehouse, catalog, schema and
  volume, with the privileges listed in [SETUP.md, section 6](SETUP.md#6-what-databricks-needs).

## 1. Configure

Copy the template and replace every `?????` in its `databricks` section:

```bash
cp usecase-template.json usecase.json
```

```json
"databricks": {
  "host": "?????",
  "token": "?????",
  "catalog": "?????",
  "schema": "?????",
  "volume": "?????",
  "warehouse_id": "?????"
}
```

`schema` and `volume` are created in step 2 if they do not exist. The other
sections have working defaults:

| Section | Key | Default | Meaning |
| --- | --- | --- | --- |
| `tabsdata` | `server`, `user`, `password` | `localhost:2457`, `usecase`, `tabsdata` | the local server and user from SETUP.md, section 3 |
| `tabsdata` | `project` | `nyctaxi` | Tabsdata project to create |
| `tlc` | `base_url` | TLC's CloudFront origin | where trip files are downloaded from |
| `tlc` | `first_month`, `last_month` | `2026-01`, `null` | months to load; `null` = latest published |
| `dirs` | `cache`, `landing` | `cache`, `landing` | downloaded files; files handed to Tabsdata |

`usecase.json` holds your token and is in `.gitignore`; only the template is meant to be shared.

## 2. Databricks: prepare the target

```bash
python databricks/run.py setup
```

Creates the schema and the volume if they are missing, and lists the tables
already in the schema. Start from an empty schema: the fact tables are
appended to.

## 3. Tabsdata: run the pipeline

```bash
python tabsdata/run.py
```

This runs three steps in order. Each can also be run on its own:

| Step | What it does | Time |
| --- | --- | --- |
| `python tabsdata/run.py download` | TLC files into `cache/`; a file already there is never fetched again | < 1 min |
| `python tabsdata/run.py deploy` | project, groups, collections (including the Databricks egress connection) and the 16 functions | ~1 min |
| `python tabsdata/run.py load` | the zone lookup once, then one month at a time, each its own transaction | ~2 min per month |

When `load` finishes, `dim_zone`, `dim_date`, `fct_trip` and `trip_summary`
are in the Databricks schema. When TLC publishes a new month, run
`python tabsdata/run.py download load`: only the new file is downloaded and
only the new month is loaded.

## 4. Databricks: deploy the dashboards

```bash
python databricks/run.py dashboards
```

Deploys the three dashboards (Fleet Operations, Financial Performance,
Compliance & Quality) as an asset bundle and prints their URLs. They query
`trip_summary` only, so they pick up each new month on their next refresh.

Every command's exit code is checked; both scripts stop at the first failure.

## 5. Check

In Databricks:

```sql
SELECT td_trx_id, COUNT(*), COUNT(DISTINCT trip_id) FROM trip_summary GROUP BY td_trx_id;  -- one row per month
SELECT COUNT(*) FROM fct_trip;                                                             -- same total
```

In Tabsdata, the rejected trips with each rule's verdict on each row, the
per-rule tallies, and how many passenger, payment and rate values
standardization found invalid (and the quality step then imputed):

```bash
tdk table data -P nyctaxi --coll nyc_silver --name green_taxi_discarded --extra-cols meta
tdk table data -P nyctaxi --coll nyc_silver --name green_taxi_dq_summary
tdk table data -P nyctaxi --coll nyc_silver --name green_taxi_standardized_dq_summary
```

## If something fails

- **A load fails:** `tdk plan list` shows the failed plan. Fix the cause, run
  `tdk plan recover --plan <id>`, then `python tabsdata/run.py load` to
  continue. Do not remove the month from `landing/`: its trips may already be
  committed.
- **Start over:** in Tabsdata, delete the collections (`tdk collection delete
  -P nyctaxi --name <collection>`, `nyc_databricks` first) and then the
  project (`tdk project delete --name nyctaxi`), and `rm -rf landing`. In
  Databricks, drop the four tables. `cache/` can stay.

## Layout

```
usecase-template.json        the configuration to copy to usecase.json
SETUP.md                     installing Tabsdata, the local server, the MCP server
tabsdata/                    ── Tabsdata ──
  run.py                     download, deploy, load
  functions/source/          publishers: trip and zone files, loaded as they are
  functions/bronze/          CDC bronze streams
  functions/silver/          column types + trip_id, data quality, dedup, SCD1 zones
  functions/gold/            dim_zone, dim_date, fct_trip, trip_summary
  functions/destination/     subscribers: gold tables to Databricks
  ARCHITECTURE.md, docs/     design notes
databricks/                  ── Databricks ──
  run.py                     setup, dashboards
  dashboards/                the three Lakeview dashboards, as an asset bundle
blog/                        the write-up
cache/, landing/             downloaded files; files handed to Tabsdata (created by the run)
```
