#
# Copyright 2026 Tabsdata Inc.
#

from functools import cache

from tabsdatak.api import AllTablesTrigger, TableFrameSpec, transformer
from tabsdatak.dataquality import DataQuality, Enrich, IsTrue, Summary
from tabsdatak.tableframe.datatypes import Float64, String
from tabsdatak.tableframe.functions import col
from tabsdatak.tableframe.udf import on_element
from typesafe_sdk import Choice, Noul, Score, ScoreAnswer, TypeSafeClient

# filled in by run.py from creds.json in the copy of this file it registers,
# tabsdata has no secret store for transformers so the key ships with the code
JEV_API_KEY = "?????"

# issue bodies are cut to this many characters before they're sent to jev
MAX_BODY_LENGTH = 4000

# severity levels jev picks from, in order, the descriptions are what jev reads
SEVERITY_LEVELS = {
    "low": "Cosmetic, or affects very few users.",
    "medium": "A real problem with an easy workaround.",
    "high": "A common workflow is broken or gives wrong results.",
    "critical": "Data loss, or wrong results or a crash in common use without warning.",
}

# questions jev answers about every issue in one call, a Choice picks one of the
# criteria, a Score places the issue on an ordered scale and a Noul is a yes/no
# probability
QUESTIONS: dict[str, Choice | Score | Noul] = {
    "kind": Choice(
        instructions="What kind of GitHub issue of the polars library is this?",
        criteria={
            "bug": "Something does not work as documented or crashes.",
            "enhancement": "A request for a new feature or a change in behaviour.",
            "documentation": "A problem or gap in the documentation.",
            "performance": "It works, but too slowly or with too much memory.",
        },
    ),
    "severity": Score(
        instructions="How severe is this issue for polars users?",
        criteria=list(SEVERITY_LEVELS.values()),
    ),
    "is_regression": Noul(
        instructions="Does the issue say this worked in an earlier version of polars?"
    ),
    "has_reproducible_example": Noul(
        instructions="Does the issue include code that reproduces the problem?"
    ),
}

# probability from which a Noul answer counts as yes
YES = 0.5


# transformer that asks jev to triage each new issue and compares the answers
# with the maintainers' labels, the data quality check counts how often they
# agree and writes the per row result to issue_triage_quality and the totals to
# issue_triage_quality_summary
@transformer(
    input_tables=["github_landing/polars_issues"],
    output_tables=["issue_triage"],
    trigger_by=AllTablesTrigger(),
    on_tables=[
        DataQuality(
            table="issue_triage",
            classifiers=[
                IsTrue(
                    [
                        "kind_matches",
                        "severity_matches",
                        "regression_matches",
                        "reproducible_matches",
                    ]
                )
            ],
            operators=[
                Enrich(to_table="issue_triage_quality"),
                Summary(table="issue_triage_quality_summary", trend=None),
            ],
        )
    ],
)
def tfr_triage_issues(issues: TableFrameSpec) -> TableFrameSpec:
    if issues is None or issues.slice(0, 1).extract_one() is None:
        return None
    return issues.udf(["title", "body"], ask_jev).with_columns(
        kind_matches=col("kind") == col("maintainer_kind"),
        severity_matches=col("severity")
        == col("maintainer_severity").str.strip_prefix("P-").str.to_lowercase(),
        regression_matches=(col("is_regression") >= YES)
        == col("maintainer_regression").is_not_null(),
        reproducible_matches=(col("has_reproducible_example") >= YES)
        == col("maintainer_needs_repro").is_null(),
    )


# udf that tabsdata runs once per issue with its title and body, it asks jev the
# four questions and returns the answers as the new columns declared in the
# decorator, in the same order
@on_element(
    [
        ("kind", String),
        ("kind_confidence", Float64),
        ("severity", String),
        ("severity_confidence", Float64),
        ("is_regression", Float64),
        ("has_reproducible_example", Float64),
        ("jev_model", String),
    ]
)
def ask_jev(title: str, body: str | None) -> list:
    state = {"title": title, "body": (body or "")[:MAX_BODY_LENGTH]}
    response = jev().system_one(state=state, questions=QUESTIONS)
    kind = response.choices["kind"]
    severity = response.scores["severity"]
    return [
        kind.choice,
        kind.confidence,
        severity_level(severity),
        severity.confidence,
        response.nouls["is_regression"].noul,
        response.nouls["has_reproducible_example"].noul,
        response.model,
    ]


# helper function that creates the jev client once per run instead of once per
# issue
@cache
def jev() -> TypeSafeClient:
    return TypeSafeClient(api_key=JEV_API_KEY)


# helper function that turns jev's score into the name of the most likely
# severity level, the levels are matched by position
def severity_level(severity: ScoreAnswer) -> str:
    likeliest = max(severity.probabilities, key=severity.probabilities.__getitem__)
    position = sorted(severity.probabilities).index(likeliest)
    return list(SEVERITY_LEVELS)[position]
