import os
import tabsdata as td


@td.publisher(
    source=td.LocalFileSource(
        os.path.join(os.path.dirname(os.getcwd()), "output", "customer_data.csv")
    ),
    tables=["input_data"],
)
def mysql_setup_pub(tf: td.TableFrame):
    return tf
