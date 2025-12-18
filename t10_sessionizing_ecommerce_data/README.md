# Tutorial 10: Sessionizing E-commerce Log Data (`t10_sessionizing_ecommerce_data`)

This tutorial walks through the workflow featured in the “Sessionizing E-Commerce Data with Tabsdata” blog post. You will ingest three log streams (web views, cart activity, and purchases), parse them with Grok patterns, stitch them into a single timeline, assign shopper sessions based on a 30-minute inactivity threshold, aggregate metrics, and optionally subscribe the results to Snowflake.

If you get stuck, check our [Troubleshooting](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) guide or reach out on [Slack](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

For more background on Tabsdata basics, review our earlier tutorials ([1](https://github.com/tabsdata/tutorials/tree/main/t01_csv_pub_sub), [2](https://github.com/tabsdata/tutorials/tree/main/t02_postgres_pub_sub), [3](https://github.com/tabsdata/tutorials/tree/main/t03_csv_iceberg_pub_sub), [4](https://github.com/tabsdata/tutorials_staging/tree/main/t04_gsheet_neon), [5](https://github.com/tabsdata/tutorials_staging/tree/main/t05_oracle_cdc)).

## Prerequisites

- Python 3.12 or higher
- Tabsdata 1.3.0+ (use `tabsdata[all]` if unsure)
- Optional Snowflake account if you plan to run the subscriber that publishes `sessionized_logs` and `aggregated_sessions`
- The `logs/` folder from this repo (run `python ../generate_logs.py` if you want to regenerate synthetic data)

## 1. Clone the GitHub repository

```sh
git clone https://github.com/tabsdata/tutorials
cd tutorials/t10_sessionizing_ecommerce_data/functions
```

> The synthetic event streams already live under `../logs`. They contain ~1K events per stream split across three rotated log files.

## 2. Configure environment variables

Update `../source.sh` with the Snowflake credentials you want to use for Subscribing your data. Then source the script to populate your shell:

```sh
. ../source.sh
```

This file defines `TD_SERVER`, `TD_USER`, `TD_PASSWORD`, and `TD_ROLE`. When Snowflake is enabled, the subscriber reads `SNOWFLAKE_*` variables and the `SNOWFLAKE_PAT` secret.

## 3. Set up the Tabsdata instance

### 3.1 Install Tabsdata and extras

```sh
pip install 'tabsdata[all]' --upgrade
pip install 'tabsdata[snowflake]' --upgrade
```

### 3.2 [OPTIONAL] Quickstart script

Prefer a one-liner setup? Use the helper script to create the `session_analysis` instance, register every function, and trigger the workflow.

```sh
# Local-only run (results stay in Tabsdata)
../setup-tabsdata.sh

# Include the Snowflake subscriber
../setup-tabsdata.sh snowflake
```

If you run the quickstart you can skip to [step 4](#4-trigger-the-publisher).

### 3.3 Start the server

```sh
tdserver start --instance session_analysis
```

### 3.4 Login

```sh
td login --server localhost --user admin --role sys_admin --password tabsdata
```

### 3.5 Create a collection

```sh
td collection create --name session_analysis
```

### 3.6 Register the functions

Register the publisher, transformers, and optional subscriber so the workflow mirrors the blog.

**Publisher**

1. `01_publish_logs.py::publish_logs` – Reads local log files, applies Grok patterns to extract structured columns, and publishes `cart_log`, `purchase_log`, and `web_log`.

```sh
td fn register --coll session_analysis --path 01_publish_logs.py::publish_logs
```

**Transformers**

1. `02_create_unified_log.py::create_unified_log` – Normalizes the three streams, concatenates them, sorts by `user_id`/`timestamp`, and adds a human-readable `time_pretty` column → `joined_logs`.
2. `03_sessionize_log_data.py::sessionize_log_data` – Implements the 30-minute inactivity threshold and hash-based user change detection to assign session IDs → `sessionized_logs`.
3. `04_aggregate_sessions.py::aggregate_sessions` – Aggregates event counts and duration metrics per session, formatting durations as `Xm Ys` strings → `aggregated_sessions`.

```sh
td fn register --coll session_analysis --path 02_create_unified_log.py::create_unified_log
td fn register --coll session_analysis --path 03_sessionize_log_data.py::sessionize_log_data
td fn register --coll session_analysis --path 04_aggregate_sessions.py::aggregate_sessions
```

**Subscriber (optional)**

1. `05_subscribe_sessions_snowflake.py::subscribe_sessions` – Writes both analysis tables to Snowflake using the connection defined in `source.sh`.

```sh
td fn register --coll session_analysis --path 05_subscribe_sessions_snowflake.py::subscribe_sessions
```

## 4. Trigger the publisher

Once registrations are complete, a single publisher trigger kicks off the entire DAG—Tabsdata automatically orchestrates downstream transformers.

```sh
td fn trigger --coll session_analysis --name publish_logs
```

## 5. Inspect the results

### 5.1 Tabsdata UI

Visit [http://localhost:2457](http://localhost:2457) and log in using the credentials from `source.sh`. Sample `joined_logs`, `sessionized_logs`, or `aggregated_sessions` under the `session_analysis` collection and explore their version history.

### 5.2 Tabsdata CLI

```sh
td table sample --coll session_analysis --name aggregated_sessions
```

### 5.3 Snowflake destination

If you registered the Snowflake subscriber, query `aggregated_sessions` and `sessionized_logs` in your warehouse once the workflow finishes. Tables are replaced on each run per the configuration in `05_subscribe_sessions_snowflake.py`.

## Need help?

Check the [Troubleshooting Guide](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) or ask in our [Slack Community](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).
