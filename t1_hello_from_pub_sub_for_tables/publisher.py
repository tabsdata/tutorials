import os
import tabsdata as td

@td.publisher(
    # Absolute system path to the file to be imported by the Publisher.
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "t1_hello_from_pub_sub_for_tables", "persons.csv")),

    # Name of the table created in the Tabsdata collection.
    tables = ["persons_t2"],
)

def publish_t2(tf:td.TableFrame):
    
    # Drop columns from the input file before publishing to Tabsdata.
    tf = tf.drop("name","surname","first_name","last_name","full_name","phone_number","telephone","email")

    return tf