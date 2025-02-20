# Create a Publisher to import data from a CSV in your local directory

import os
import tabsdata as td

td.publisher(
    source = td.LocalFileSystem(os.path.join(os.getenv("TDX"), "persons.csv")), #Store the path to your working directory in the enviroment variable TDX.
    tables = ["persons_t1"],
)

def publish_t1(tf:td.TableFrame):
    tf = tf.drop("name","surname","first_name","last_name","full_name","phone_number","telephone","email")
    return tf