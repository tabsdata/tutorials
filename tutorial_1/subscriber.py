import os
import tabsdata as td

@td.subscriber(
    # Name of the table to be exported from Tabsdata.
    tables = ["persons_t1"],

    # Absolute system path to the file to be written by the Subscriber.
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "persons_t1_output.jsonl")),
)

def subscribe_t1(tf: td.TableFrame):
    return tf