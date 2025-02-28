import os
import tabsdata as td

@td.publisher(
    # Absolute system path to the file to be imported by the Publisher.
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "persons.csv")),

    # Name of the table created in the Tabsdata collection.
    tables = ["persons_t1"],
)

def publish_t1(tf: td.TableFrame):
    
    # Drop columns from the input file before publishing to Tabsdata.
    tf = tf.drop(["name","surname","first_name","last_name","full_name","phone_number","telephone","email","username","password"])

    return tf