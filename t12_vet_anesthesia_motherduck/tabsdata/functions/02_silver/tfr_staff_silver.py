#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col


# helper function that casts a raw column to string and trims whitespace, blank
# values become null
def text(name: str) -> Expr:
    return col(name).cast(td_types.String).str.extract(r"^\s*(\S.*?)\s*$", 1)


# transformer that dedupes the personnel repeated across pet records and builds
# the case to staff mapping
@transformer(
    input_tables=["vet_landing/raw_personnel", "vet_landing/raw_case_personnel"],
    output_tables=["staff", "case_staff"],
)
def tfr_staff_silver(
    raw_personnel: TableFrameSpec,
    raw_case_personnel: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec]:
    staff = raw_personnel.select(
        text("person_id").alias("person_id"),
        text("person_name").alias("person_name"),
    ).unique(subset=["person_id"])

    case_staff = raw_case_personnel.select(
        text("case_id").alias("case_id"),
        text("person_id").alias("person_id"),
        text("role").alias("role"),
    ).unique()

    return staff, case_staff
