<!-- Copyright 2026 Tabsdata Inc. -->

# Triage GitHub issues with Jev

This project pulls open issues from the Polars repository, asks Jev to classify each one as a bug, enhancement, documentation issue, or performance problem, estimates severity on a scale from low to critical, and checks whether it's a regression or has a reproducible example.

It then compares Jev's answers to the maintainers' own labels on the same issues. A data quality check tracks how often they agree—how accurate is Jev's triage on real-world issues?

## What's inside

Tabsdata connects to the GitHub API via the `tabsdata-conn-github` connector, fetches issues since a cutoff date, and feeds them to a transformer written with Jev. The transformer runs `.udf()` on each issue title and body, asks Jev four questions, and returns Jev's answers plus confidence scores.

A second data quality layer compares each Jev answer to the maintainer label, calculates agreement rates per criterion, and writes results to `issue_triage_quality_summary`.

| Collection | What happens |
| --- | --- |
| `github_landing` | `pub_issues` fetches open issues from pola-rs/polars since 2026-10-01 into `polars_issues` |
| `issue_triage` | `tfr_triage_issues` asks Jev to classify each issue; a data quality check compares answers to maintainer labels and writes summary stats to `issue_triage_quality_summary` |

## Prerequisites

- Tabsdata 2.2 with a local server running (use `ee7` conda env):

  ```bash
  conda activate ee7
  tdkserver start
  ```

- A Tabsdata API key (`TYPESAFE_API_KEY` in `~/.zshenv`)
- Optionally, a GitHub token for higher rate limits (not required for ~50 issues)

## Run it

### 1. Configure credentials

Copy the example config:

```bash
cp creds-template.json creds.json
```

Set `jev.api_key` from 1Password. The GitHub token is optional.

If your Tabsdata server instance is not named `tabsdata`, also update `tabsdata.instance`.

`creds.json` is in `.gitignore`, so your API keys stay local.

### 2. Build and load the pipeline

Run:

```bash
python tabsdata/run.py
```

This installs the GitHub connector and Jev SDK, creates the Tabsdata project, collections, and functions, then triggers the publisher to fetch issues and run the triage.

Each step can also run separately:

```bash
python tabsdata/run.py connector
python tabsdata/run.py deploy
python tabsdata/run.py load
```

### 3. Check the results

Query the triage in Tabsdata:

```
issue_triage: 53 rows, each with Jev's classification and confidence scores
issue_triage_quality_summary: agreement rates for each criterion (kind, severity, regression, reproducible)
```

Example query to see a few issues and Jev's answers:

```sql
select
    title,
    kind,
    kind_confidence,
    severity,
    kind_matches,
    severity_matches
from issue_triage
limit 5
```

Agreement rates from the quality summary:

- **kind_matches**: 47/53 (89%) — Jev agrees with the maintainers' issue type
- **severity_matches**: 5/53 (9%) — most issues don't have a maintainer severity label
- **regression_matches**: 42/53 (79%) — Jev identifies regressions accurately
- **reproducible_matches**: 48/53 (91%) — Jev detects missing reproducible examples well

## How it works

The transformer calls `ask_jev(title, body)` for each issue. That function creates a TypeSafeClient, sends the issue state and four questions to Jev, parses the response, and returns seven columns: kind and its confidence, severity and its confidence, regression probability, reproducible example probability, and the model name.

Jev runs async; the whole triage finishes in under a minute for 53 issues.

The data quality check runs IsTrue classifiers on four boolean columns (the `*_matches` columns) and writes per-row results to `issue_triage_quality` and aggregate stats to `issue_triage_quality_summary`.

## Adding more issues

To fetch more issues or from a different repo, edit `pub_issues.py`:

```python
GitHubSrc(
    since="2026-10-01T00:00:00Z",
    max_pages=2,  # increase to fetch more pages
    tables=[Issues("pola-rs/polars", label_columns=MAINTAINER_LABELS)]  # or another repo
)
```

Then run:

```bash
python tabsdata/run.py load
```

Loads are incremental. Tabsdata only fetches issues changed since the previous run. The transformer re-asks Jev about new issues and updates the data quality check.
