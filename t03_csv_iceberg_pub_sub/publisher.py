import os
import tabsdata as td

@td.publisher(
    # Absolute system path to the file to be imported by the Publisher.
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "input", "customers.csv")),

    # Name of the table created in the Tabsdata collection.
    tables = ["customer_leads"],
)

def publish_customers(tf: td.TableFrame):
    
    # Drop columns from the input file before publishing to Tabsdata.
    output_tf = tf.select(["FIRST_NAME","LAST_NAME","COMPANY_NAME","EMAIL","WEB"])

    return output_tf