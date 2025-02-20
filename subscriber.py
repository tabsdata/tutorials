import os
import tabsdata as td

@td.subscriber(
    ["persons_t1"],
    td.LocalFileDestination(os.path.join(os.getenv("TDX"), "persons_t1_output.jsonl")),
)

def subsribe_t1(persons_t1: td.TableFrame):
    return persons_t1