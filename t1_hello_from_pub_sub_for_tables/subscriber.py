import os
import tabsdata as td

@td.subscriber(
    # Name of the table to be exported from Tabsdata.
    tables = ["persons_t2"],

    # Absolute system path to the file to be written by the Subscriber.
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "t1_hello_from_pub_sub_for_tables","persons_t2_output.jsonl")), 
)

def subscribe_t2(persons_t2: td.TableFrame):
    return persons_t2