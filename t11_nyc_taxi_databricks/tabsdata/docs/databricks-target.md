<!-- Copyright 2026 Tabsdata Inc. -->

# The Databricks destination

The `nyc_databricks` collection holds Tabsdata's connection to the warehouse and
the three subscribers that publish gold into it. `tabsdata/run.py deploy`
creates it from the `databricks` section of `usecase.json`; what the workspace
needs is in [SETUP.md, section 6](../../SETUP.md#6-what-databricks-needs).

## The connection

| Connection field | From `usecase.json` | How it is passed |
| --- | --- | --- |
| `host_url` | `databricks.host` | `$secret:DATABRICKS__HOST` |
| `token` | `databricks.token` | `$secret:DATABRICKS__TOKEN` |
| `catalog` | `databricks.catalog` | `str:` |
| `schema` | `databricks.schema` | `str:` |
| `volume` | `databricks.volume` | `str:` |
| `warehouse_id` | `databricks.warehouse_id` | `str:` |

`tabsdata/run.py` puts the host and token into those two environment variables
for the `tdk collection create` call only. `tdk` resolves `$secret:` references
on the client and the server stores the values as secrets; the connection
document keeps only a marker.

`warehouse_id` is required: the write goes through `COPY INTO`, which needs a
SQL warehouse. Without it, the run connects and then fails at write time with
`DATABRICKS_9 ... requires either 'warehouse' (name) or 'warehouse_id'`.

A connection is fixed when its collection is created. To point at a different
workspace or schema, delete the `nyc_databricks` collection and run
`tabsdata/run.py deploy` again against a new project, or recreate the
collection and re-register the three subscribers.

## Write modes

| Subscriber | Tables | Mode | Why |
| --- | --- | --- | --- |
| `sub_gold_dims_to_databricks` | `dim_zone`, `dim_date` | `replace` | both are rebuilt in full on every dimension load |
| `sub_gold_fct_trip_to_databricks` | `fct_trip` | `append` + watermark | each load produces only its own trips |
| `sub_gold_trip_summary_to_databricks` | `trip_summary` | `append` + watermark | built from the same new trips |

`if_table_exists` is a per-subscriber setting, which is why the facts and the
dimensions have separate subscribers.

## Replays and the watermark

`watermark_column="td_trx_id"` stamps every appended row with its Tabsdata
transaction id, so replaying a failed transaction writes nothing twice. It
does not deduplicate two *different* transactions that carry the same trips:
each gets its own id and both append. Before loading a month again by hand,
check:

```sql
SELECT td_trx_id, COUNT(*) FROM fct_trip GROUP BY td_trx_id;
SELECT td_trx_id, COUNT(*) FROM trip_summary GROUP BY td_trx_id;
```

and remove an unwanted batch with `DELETE FROM <table> WHERE td_trx_id = '...'`.

## What does not leave Tabsdata

Columns in the `@td.` namespace, the medallion metadata such as
`@td.medallion.source_ts` and `@td.medallion.date_sk`, stay inside Tabsdata;
the published tables do not carry them. Anything a warehouse consumer needs is
copied into a regular column in gold: `pickup_datetime`, `trip_date`, `date_sk`.
