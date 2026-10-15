#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, publisher
from tabsdata_github import GitHubSrc, Issues

# maintainer labels turned into columns, each column holds the first of its labels
# the issue has so jev's answers can be compared with the maintainers' later
MAINTAINER_LABELS = {
    "maintainer_kind": ["bug", "enhancement", "documentation", "performance"],
    "maintainer_severity": ["P-low", "P-medium", "P-high", "P-critical"],
    "maintainer_regression": ["regression"],
    "maintainer_needs_repro": ["needs repro"],
}


# publisher that reads the polars issues opened or updated since the previous
# run through the github connector, the first run starts at since and max_pages
# caps a run at 20 pages of 100, about half of them pull requests the connector
# drops, so a run lands around 1000 issues
@publisher(
    source=GitHubSrc(
        since="2026-07-01T00:00:00Z",
        max_pages=20,
        tables=[Issues("pola-rs/polars", label_columns=MAINTAINER_LABELS)],
    ),
    output_tables=["polars_issues"],
)
def pub_issues(polars_issues: TableFrameSpec) -> TableFrameSpec:
    return polars_issues
