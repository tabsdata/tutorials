#
# Copyright 2026 Tabsdata Inc.
#

from tabsdata_motherduck import MotherDuckDest
from tabsdatak.api import TableFrameSpec, subscriber

TABLES = [
    "dim_patient",
    "dim_owner",
    "dim_staff",
    "dim_date",
    "fct_anesthesia_case",
    "fct_medication",
    "fct_procedure",
    "fct_lab_result",
    "fct_case_staff",
    "fct_case_remark",
    "fct_vital_sign",
]


# subscriber that writes the gold tables to motherduck through the custom
# connector, replacing them each time the gold tables update
@subscriber(
    input_tables=[f"vet_gold/{table}" for table in TABLES],
    destination=MotherDuckDest(tables=TABLES, if_table_exists="replace"),
)
def sub_gold_to_motherduck(
    dim_patient: TableFrameSpec,
    dim_owner: TableFrameSpec,
    dim_staff: TableFrameSpec,
    dim_date: TableFrameSpec,
    fct_anesthesia_case: TableFrameSpec,
    fct_medication: TableFrameSpec,
    fct_procedure: TableFrameSpec,
    fct_lab_result: TableFrameSpec,
    fct_case_staff: TableFrameSpec,
    fct_case_remark: TableFrameSpec,
    fct_vital_sign: TableFrameSpec,
) -> tuple[
    TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec,
    TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec,
]:
    return (
        dim_patient, dim_owner, dim_staff, dim_date,
        fct_anesthesia_case, fct_medication, fct_procedure, fct_lab_result, fct_case_staff, fct_case_remark,
        fct_vital_sign,
    )
