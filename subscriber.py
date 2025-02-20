import os
import tabsdata as td

@td.subscriber(
    ["persons_t2"], # Name of the table to be exported from Tabsdata.
    td.LocalFileDestination(os.path.join(os.getenv("TDX"), "persons_t2_output.jsonl")), # Absolute system path to the file to be written by the Subscriber.
)

def subscribe_t2(persons_t2: td.TableFrame):
    return persons_t2