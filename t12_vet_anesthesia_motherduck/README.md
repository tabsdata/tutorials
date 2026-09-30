<!-- Copyright 2026 Tabsdata Inc. -->

# Vet anesthesia records to MotherDuck

Anesthesia records from a veterinary study arrive as one CSV per table per dog:
200 files for 20 dogs, covering cases, medications, procedures, labs, remarks
and timestamped vitals. Tabsdata wildcard-matches each table's files,
concatenates them, cleans them into silver tables, models them as a star
schema in gold, and publishes that schema to MotherDuck for querying. All data
in `data/` is dummy data. The full story is in [blog/BLOG.md](blog/BLOG.md).

| Layer | Collection | What happens |
| --- | --- | --- |
| Bronze | `vet_landing` | `pub_pet_records` globs `<table>_*.csv` and concatenates the files added or changed since the last run into a new `raw_<table>` batch |
| Silver | `vet_silver` | types cast, columns renamed to snake_case, doses split into amount and unit, duplicates removed, then each batch merged into the existing tables by id |
| Gold | `vet_gold` | 4 dimension tables and 7 fact tables, including `fct_vital_sign` |
| MotherDuck | `vet_motherduck` | the gold tables are replaced in MotherDuck each time gold updates |

## Prerequisites

- Tabsdata 2.1, with a local server running (`tdkserver start`)
- A MotherDuck account and an access token

## Run it

1. Copy the config and set `motherduck.token`:

   ```bash
   cp usecase-template.json usecase.json
   ```

   If your Tabsdata server instance isn't named `tabsdata`, also change
   `tabsdata.instance`. `usecase.json` is in `.gitignore`, so your token stays
   local.

2. Build and load everything:

   ```bash
   python tabsdata/run.py
   ```

   This installs the MotherDuck connector, creates the project, collections
   and functions, then publishes the CSVs in `data/`. Each step can also run on
   its own: `python tabsdata/run.py connector | deploy | load`.

3. Query the result in MotherDuck, for example the lowest blood pressure per dog:

   ```sql
   select p.animal_name, c.physical_status,
          round(avg(v.heart_rate_bpm)) as avg_heart_rate,
          min(coalesce(v.ibp_mean_mmhg, v.nibp_mean_mmhg)) as lowest_map
   from fct_vital_sign v
   join fct_anesthesia_case c on c.case_id = v.case_id
   join dim_patient p on p.patient_id = c.patient_id
   group by all
   order by lowest_map;
   ```

To add more dogs, drop their CSVs into `data/` and run
`python tabsdata/run.py load`. Loads are incremental: only files added or
changed since the last run are read, and silver merges them into the existing
tables by id, so a corrected CSV replaces its earlier rows. Rows deleted from a
CSV stay in silver.
