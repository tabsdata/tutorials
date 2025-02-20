import os
import tabsdata as td

td.publisher(
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "persons.csv")), # Absolute system path to the file to be imported by the Publisher.
    tables = ["persons_t2"], # Name of the table created in the Tabsdata collection.
)

def publish_t2(tf:td.TableFrame):
    tf = tf.drop("name","surname","first_name","last_name","full_name","phone_number","telephone","email") # Drop columns from the input file before publishing to Tabsdata.
    return tf