<!-- Copyright 2026 Tabsdata Inc. -->

# Vet anesthesia records to MotherDuck

This project takes veterinary anesthesia study data spread across hundreds of CSV files and turns it into a clean, queryable data model in MotherDuck.

The source data contains one CSV per table per dog. For 20 dogs, that comes out to roughly 200 files covering anesthesia cases, medications, procedures, labs, remarks, and timestamped vital signs.

Tabsdata handles the pipeline end to end. It wildcard-matches files for each table, combines them into bronze datasets, cleans and standardizes the data in silver, models it into a star schema in gold, and publishes the final tables to MotherDuck.

All data in `data/` is dummy data. The full walkthrough is available in [blog/BLOG.md](blog/BLOG.md).

| Layer | Collection | What happens |
| --- | --- | --- |
| Bronze | `vet_landing` | `pub_pet_records` matches `<table>_*.csv` files and combines files added or changed since the previous run into a new `raw_<table>` batch |
| Silver | `vet_silver` | Columns are renamed to snake case, types are cast, medication doses are split into amount and unit, duplicates are removed, and each batch is merged into the existing tables by id |
| Gold | `vet_gold` | The cleaned data is modeled into 4 dimension tables and 7 fact tables, including `fct_vital_sign` |
| MotherDuck | `vet_motherduck` | Gold tables are published to MotherDuck and replaced whenever the gold layer updates |

## Prerequisites

- Tabsdata 2.1 with a local server running:

  ```bash
  tdkserver start
  ```

- A MotherDuck account
- A MotherDuck access token

## Run it

### 1. Configure MotherDuck

Copy the example config:

```bash
cp usecase-template.json usecase.json
```

Set `motherduck.token` in `usecase.json`.

If your Tabsdata server instance is not named `tabsdata`, also update `tabsdata.instance`.

`usecase.json` is included in `.gitignore`, so your MotherDuck token stays local.

### 2. Build and load the pipeline

Run:

```bash
python tabsdata/run.py
```

This installs the MotherDuck connector, creates the Tabsdata project, collections, and functions, and publishes the CSV files in `data/`.

Each step can also be run separately:

```bash
python tabsdata/run.py connector
python tabsdata/run.py deploy
python tabsdata/run.py load
```

### 3. Query the data in MotherDuck

For example, this query compares average heart rate and the lowest recorded mean arterial pressure for each dog:

```sql
select
    p.animal_name,
    c.physical_status,
    round(avg(v.heart_rate_bpm)) as avg_heart_rate,
    min(coalesce(v.ibp_mean_mmhg, v.nibp_mean_mmhg)) as lowest_map
from fct_vital_sign v
join fct_anesthesia_case c on c.case_id = v.case_id
join dim_patient p on p.patient_id = c.patient_id
group by all
order by lowest_map;
```

## Adding more data

To add more dogs, place their CSV files in `data/` and run:

```bash
python tabsdata/run.py load
```

Loads are incremental. Tabsdata only reads files that were added or changed since the previous run.

The silver layer then merges those records into the existing tables by id. If a CSV is corrected and loaded again, its updated rows replace the previous versions.

Rows that are removed from a source CSV are not automatically deleted from the silver tables.