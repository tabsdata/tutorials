import os
import tabsdata as td


@td.subscriber(
    tables=["sf_snapshot"],
    destination=td.LocalFileDestination(
        os.path.join(
            os.path.dirname(os.getcwd()),
            "output",
            "sf_snapshot_$EXPORT_TIMESTAMP.jsonl",
        )
    ),
)
def local_sub(tf: td.TableFrame):
    return tf
