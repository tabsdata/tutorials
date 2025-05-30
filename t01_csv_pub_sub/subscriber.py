import os
import tabsdata as td

@td.subscriber(
    # Name of the table to be exported from Tabsdata.
    tables = ["customer_leads"],

    # Absolute system path to the file to be written by the Subscriber.
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "output", "customer_leads.jsonl")),
)

def subscribe_customers(tf: td.TableFrame):
    return tf
