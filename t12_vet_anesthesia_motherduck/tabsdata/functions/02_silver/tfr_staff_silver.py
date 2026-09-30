#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, TableFramesSpec, TablesTrigger, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, concat


# helper function that casts a raw column to string and trims whitespace, blank
# values become null
def text(name: str) -> Expr:
    return col(name).cast(td_types.String).str.extract(r"^\s*(\S.*?)\s*$", 1)


# helper function that concats the raw table versions published since the last
# run into one batch, None when no new csvs landed for that table
def batch(versions: TableFramesSpec) -> TableFrame | None:
    frames = [frame for frame in (versions or []) if frame is not None]
    return concat(frames, how="diagonal_relaxed") if frames else None


# helper function that merges a cleaned batch into the current silver table by
# key, batch rows replace rows with the same key so a corrected csv overwrites
# its earlier version, None when the batch is empty so the table keeps its
# current version
def merge(head: TableFrame | None, new: TableFrame | None, keys: list[str]) -> TableFrame | None:
    if new is None:
        return None
    if head is None:
        return new
    return concat([head.join(new.select(keys).unique(), on=keys, how="anti"), new], how="diagonal_relaxed")


# transformer that dedupes the personnel repeated across pet records, builds the
# case to staff mapping and merges each batch into the silver tables from the
# previous run
@transformer(
    input_tables=[
        "vet_landing/raw_personnel@NEW",
        "vet_landing/raw_case_personnel@NEW",
        "staff@HEAD",
        "case_staff@HEAD",
    ],
    output_tables=["staff", "case_staff"],
    trigger_by=TablesTrigger(tables=["vet_landing/raw_personnel", "vet_landing/raw_case_personnel"]),
)
def tfr_staff_silver(
    raw_personnel: TableFramesSpec,
    raw_case_personnel: TableFramesSpec,
    staff_head: TableFrameSpec,
    case_staff_head: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec]:
    new_staff, new_case_staff = batch(raw_personnel), batch(raw_case_personnel)

    if new_staff is not None:
        new_staff = new_staff.select(
            text("person_id").alias("person_id"),
            text("person_name").alias("person_name"),
        ).unique(subset=["person_id"])

    if new_case_staff is not None:
        new_case_staff = new_case_staff.select(
            text("case_id").alias("case_id"),
            text("person_id").alias("person_id"),
            text("role").alias("role"),
        ).unique()

    return (
        merge(staff_head, new_staff, ["person_id"]),
        merge(case_staff_head, new_case_staff, ["case_id", "person_id", "role"]),
    )
