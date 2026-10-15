<!-- Copyright 2026 Tabsdata Inc. -->

# Checkout logs from five sources to Apache Doris

A customer writes in: "I tried to check out at 2:14 PM, got charged, but the
order never completed." Answering that means reading the logs of every system
the checkout touched: the browser, the API gateway, the backend services, the
payment provider and the orders database. Each one logs in its own format, with
its own field names, id formats and timestamps.

Tabsdata reads all five sources, normalizes them into one event model and
correlates each checkout across them. It then loads the result into Apache
Doris, where an inverted index on the log text makes full-text search and
aggregation fast. All data in `data/` is dummy data from `data/generate.py`:
six hours of traffic on 2026-09-30, with a migration that locks the orders table
from 14:08 to 14:22 UTC.

## The sources

In this MVP every source is a folder of files read with `LocalFileSrc`. The
"stands in for" column is where these logs usually live.

| Folder | Format | Stands in for | Request id | User id | Time |
| --- | --- | --- | --- | --- | --- |
| `frontend/` | NDJSON | Kafka topic of browser events | `requestId` | `userId` | epoch milliseconds |
| `gateway/` | nginx access log text | S3 bucket of gateway logs | `req_id=` in the line | `uid=` in the line | `30/Sep/2026:14:14:28 +0000` |
| `services/` | NDJSON | service logs in CloudWatch or Kafka | `request_id` | `user_id` as text | `2026-09-30T14:14:21.916Z` |
| `payments/` | CSV | payment provider webhooks stored in Postgres | inside `transaction_request` | inside `customer_ref` | `09/30/26 14:14:23` |
| `infra/` | NDJSON CloudWatch export | orders database Postgres logs | none | none | epoch milliseconds, plus the Postgres line prefix |

## The pipeline

| Layer | Collection | What happens |
| --- | --- | --- |
| Bronze | `logs_landing` | one publisher per source picks up the files added or changed since the last run into `raw_<source>` |
| Silver | `logs_silver` | `tfr_log_events` groks the text logs, parses the four timestamp formats to UTC, pulls ids out of prefixed fields, maps each source's levels to `INFO`/`WARN`/`ERROR`, and dedupes against the events already loaded. It writes `log_events` (everything), `new_log_events` (this run only) and `payments` (typed payment events) |
| Gold | `logs_gold` | `tfr_checkout_requests` groups each checkout's events across sources into one row with its outcome: `completed`, `charged_without_order`, `payment_declined` or `failed_before_payment` |
| Doris | `logs_doris` | `new_log_events` is appended to `log_events` and `checkout_requests` is replaced, both through the custom Doris connector |

The common event model:

| Column | Type | Notes |
| --- | --- | --- |
| `event_time` | datetime, ms, UTC | |
| `source` | text | `frontend`, `gateway`, `services`, `payments`, `infra` |
| `service` | text | `web`, `api-gateway`, `auth`, `cart`, `catalog`, `checkout`, `orders`, `payments`, `orders-db` |
| `host` | text | pod name or log stream, where the source has one |
| `level` | text | `INFO`, `WARN`, `ERROR` |
| `event` | text | normalized event name |
| `request_id` | text | null for database logs |
| `user_id` | integer | null for anonymous and database logs |
| `http_status`, `duration_ms` | integer, float | where the source has them |
| `message` | text | the searchable log text, inverted index in Doris |
| `event_id` | text | the source's own id, or a hash of the record when it has none |

## Prerequisites

- Tabsdata 2.1, with a local server running (`tdkserver start`)
- Apache Doris 2.1 or later with its MySQL port (9030) and a stream load HTTP
  port reachable, for example the
  [Docker quick start](https://doris.apache.org/docs/gettingStarted/quick-start)

## Run it

1. Fill in `creds.json`. If it isn't there, copy the template first:

   ```bash
   cp creds-template.json creds.json
   ```

   Set `doris.password`; the quick start's `root` user has an empty password,
   so use `""`. If your Tabsdata instance isn't named `tabsdata`, change
   `tabsdata.instance`. `creds.json` is in `.gitignore`.

   `doris.http_port` is where stream loads go. The Doris frontend (8030)
   redirects each load to a backend. On Docker Desktop the backend's internal
   address isn't reachable from your machine, so the template points at the
   backend's own port, 8040. On a real cluster use the frontend's 8030.

2. Build and load everything:

   ```bash
   python tabsdata/run.py
   ```

   This runs four steps:

   - `connector` installs the Doris connector locally and in the server's function
     environment, keeping any connectors already installed there. This restarts
     the server.
   - `doris` creates the database and the tables in `doris/schema.sql`.
   - `deploy` creates the project, collections and functions.
   - `load` triggers the five publishers one at a time and waits for each
     plan to finish.

   Each step also runs on its own: `python tabsdata/run.py connector | doris | deploy | load`.

3. Query Doris, for example with `mysql -h 127.0.0.1 -P 9030 -u root checkout_logs`.
   `doris/queries.sql` walks through the investigation from the ticket to the
   refund list. The first query is the customer's own timeline:

   ```sql
   SELECT event_time, source, service, level, event, message
   FROM log_events
   WHERE user_id = 48291
     AND event_time BETWEEN '2026-09-30 14:10:00' AND '2026-09-30 14:20:00'
   ORDER BY event_time;
   ```

   It shows the card charged at 14:14:23, then the orders service failing to insert
   the order five seconds later. Full-text search then finds the same timeout in the
   database log, which has no request id at all:

   ```sql
   SELECT event_time, source, service, message
   FROM log_events
   WHERE message MATCH_ANY 'timeout'
   ORDER BY event_time
   LIMIT 20;
   ```

To add more logs, drop files into the source folders and run
`python tabsdata/run.py load`. Only files added or changed since the last load are
read. Events already loaded are dropped by `event_id`, so a log file that grew
only adds its new lines. To regenerate the dummy data, run `python data/generate.py`.

## The Doris connector

`doris_connector/` is a custom Tabsdata destination connector, installed the same
way as the MotherDuck connector in t12. It follows the structure of the built-in
StarRocks connector: a connection, a destination, a plugin and error codes. Each
subscriber picks one of two load methods with `DorisDest(load_method=...)`:

| `load_method` | How the data gets in | Needs |
| --- | --- | --- |
| `stream_load` (default) | each parquet file is sent straight to Doris [stream load](https://doris.apache.org/docs/data-operate/import/import-way/stream-load-manual) over HTTP | the Doris HTTP port |
| `s3` | the file is uploaded to S3 with the Tabsdata transporter, then `INSERT INTO ... SELECT ... FROM S3(...)` reads it back | a `staging` bucket on the connection that the Doris backends can reach |

Stream load suits small, frequent batches like these log appends. S3 staging
suits large loads, since every Doris backend reads the staged file in parallel.
This tutorial stream loads both tables.

To try S3 staging:

1. Fill in `doris.staging` in `creds.json` with a bucket, its region and an
   access key pair.
2. Set `load_method="s3"` in `tabsdata/functions/04_destination/sub_logs_to_doris.py`.
3. Run `python tabsdata/run.py deploy`.

The S3 method replicates the StarRocks connector's staging:

- Files are uploaded under `<base_path>/<upload_id>/<table>/<file>`, with one
  `upload_id` per subscriber run.
- The upload goes through the same transporter.
- Staged files are left in the bucket, so add a lifecycle rule that expires them.

It differs from StarRocks in three ways:

- It reads with Doris's `S3()` table function instead of StarRocks's `FILES()`.
- The insert carries a load label.
- Only S3 is supported, not Azure or GCS.

Rules that apply to both methods:

- The target tables must exist, like with StarRocks. The key model,
  partitioning and inverted indexes can't be inferred from the data.
- Parquet columns are matched to table columns by name. A column the table
  doesn't have fails the load, instead of being dropped.
- A load commits as one Doris transaction, and strict mode fails the whole load
  on any row that doesn't fit the table.
- `append` labels each load with a hash of the file. If the same file is
  retried, Doris sees the same label and skips the load instead of writing
  duplicate rows.
- `replace` truncates the table, then loads. A failed load leaves the table
  empty until the next run.
- With `s3`, the S3 keys are part of the `INSERT` statement sent to Doris,
  the same way the StarRocks connector passes them to `FILES()`.
