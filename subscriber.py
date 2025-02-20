import os
import tabsdata as td

@td.subscriber(
    ["persons_t1"], # Name of the table to be exported from Tabsdata.
    td.LocalFileDestination(os.path.join(os.getenv("TDX"), "persons_t1_output.jsonl")), # Absolute system path to the file to be written by the Subscriber.
)

def subsribe_t1(persons_t1: td.TableFrame):
    return persons_t1