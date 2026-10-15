<!-- Copyright 2026 Tabsdata Inc. -->

# Triage GitHub issues with Jev

This project pulls issues from the Polars GitHub repository and asks Jev, TypeSafe's System 1 model, four questions about each one: what kind of issue it is, how severe it is, whether it's a regression, and whether it includes code that reproduces the problem.

A data quality check then compares Jev's answers with the labels the Polars maintainers gave the same issues.

| Collection | What happens |
| --- | --- |
| `github_landing` | `pub_issues` reads pola-rs/polars issues updated since July 1, 2026 through the GitHub connector and writes them to `polars_issues`, with the maintainers' labels as columns |
| `issue_triage` | `tfr_triage_issues` sends each issue's title and body to Jev and writes the answers to `issue_triage`. A data quality check scores them against the maintainers' labels in `issue_triage_quality_summary` |

The full walkthrough is in the [blog post](https://tabsdata.com/blog/supercharging-github-issue-classification-with-tabsdata-and-jev).

## Prerequisites

- Tabsdata 2.2 with a local server running:

  ```bash
  tdkserver start
  ```

  If you don't have a server yet, the [server quickstart](https://docs.tabsdata.com/server-admin/quickstart) has instructions on how to create one.

- A Jev API key from [TypeSafe](https://typesafe.ai)
- A GitHub token is optional. Without one GitHub allows 60 requests an hour, which covers one load

## Run it

### 1. Add your Jev key

Copy the example config:

```bash
cp creds-template.json creds.json
```

Set `jev.api_key` in `creds.json`. Add a GitHub token under `github.token` if you have one.

If your Tabsdata server instance is not named `tabsdata`, also update `tabsdata.instance`.

`creds.json` is included in `.gitignore`, so your keys stay local.

### 2. Build and load the pipeline

Run:

```bash
python tabsdata/run.py
```

This installs the GitHub connector and the TypeSafe SDK, creates the Tabsdata project, collections and functions, and runs the publisher, which triggers the triage.

Each step can also be run separately:

```bash
python tabsdata/run.py connector
python tabsdata/run.py deploy
python tabsdata/run.py load
```

Tabsdata has no secret store for transformers yet, so `run.py` registers a copy of the transformer with your Jev key filled in. The copy is written to `tabsdata/build/`, which is also in `.gitignore`.

### 3. Check the results

Open `issue_triage` in the Tabsdata UI. Each issue has Jev's answers next to the maintainers' labels, and the data quality summary shows how often they agree.

On 688 issues the check came out like this:

| Check | Passed | Failed | No label |
| --- | --- | --- | --- |
| `kind_matches` | 503 | 74 | 111 |
| `severity_matches` | 55 | 160 | 473 |
| `regression_matches` | 639 | 49 | 0 |
| `reproducible_matches` | 470 | 218 | 0 |

Most Polars issues have no severity label, so the severity check has little to compare against.

## Loading more issues

`pub_issues` reads 20 pages of 100 items per run. GitHub returns issues and pull requests together and the connector drops the pull requests, so a run lands a few hundred issues.

To read more, raise `max_pages` in `tabsdata/functions/01_source/pub_issues.py`. To triage another repository, change `"pola-rs/polars"`.

Then run:

```bash
python tabsdata/run.py load
```

Loads are incremental. Each run picks up where the previous one stopped, and Jev only sees issues that are new or changed.
