import os
import tabsdata as td


@td.publisher(
    source=td.LocalFileSource(
        "/Users/danieladayev/tabsdata_projects/tutorials_staging/t08_customer_pii_masking/input/customer_data.csv"
    ),
    tables=["input_data"],
)
def mysql_setup_pub(tf: td.TableFrame):
    return tf
