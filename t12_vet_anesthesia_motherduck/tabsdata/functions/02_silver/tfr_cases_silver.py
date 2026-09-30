#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, TableFramesSpec, TablesTrigger, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, concat, lit


# helper function that casts a raw column to string and trims whitespace, blank
# values become null
def text(name: str) -> Expr:
    return col(name).cast(td_types.String).str.extract(r"^\s*(\S.*?)\s*$", 1)


# helper function that combines the procedure date with an HH:MM time column to
# create a timestamp
def at(date: Expr, time_column: str) -> Expr:
    return date.dt.combine(text(time_column).str.to_time("%H:%M", strict=False))


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


# transformer that casts the new raw cases, patients and owners to their proper
# types, joins owner_id from cases onto patients and merges each batch into the
# silver tables from the previous run
@transformer(
    input_tables=[
        "vet_landing/raw_cases@NEW",
        "vet_landing/raw_patients@NEW",
        "vet_landing/raw_owners@NEW",
        "cases@HEAD",
        "patients@HEAD",
        "owners@HEAD",
    ],
    output_tables=["cases", "patients", "owners"],
    trigger_by=TablesTrigger(
        tables=["vet_landing/raw_cases", "vet_landing/raw_patients", "vet_landing/raw_owners"],
    ),
)
def tfr_cases_silver(
    raw_cases: TableFramesSpec,
    raw_patients: TableFramesSpec,
    raw_owners: TableFramesSpec,
    cases_head: TableFrameSpec,
    patients_head: TableFrameSpec,
    owners_head: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec, TableFrameSpec]:
    new_cases, new_patients, new_owners = batch(raw_cases), batch(raw_patients), batch(raw_owners)
    procedure_date = text("procedure_date").str.to_date("%Y-%m-%d", strict=False)

    if new_cases is not None:
        new_cases = new_cases.select(
            text("case_id").alias("case_id"),
            text("patient_id").alias("patient_id"),
            text("owner_id").alias("owner_id"),
            procedure_date.alias("procedure_date"),
            text("physical_status").alias("physical_status"),
            (text("emergency_flag").str.to_lowercase() == lit("true")).alias("is_emergency"),
            text("recumbency").alias("recumbency"),
            text("sedation_present").alias("sedation_level"),
            text("comments").alias("comments"),
            text("pre_op_eval").alias("pre_op_eval"),
            at(procedure_date, "anesthesia_start").alias("anesthesia_start"),
            at(procedure_date, "anesthesia_end").alias("anesthesia_end"),
            at(procedure_date, "recovery_end").alias("recovery_end"),
            text("anesthesia_duration_min").cast(td_types.Int32, strict=False).alias("anesthesia_minutes"),
            text("recovery_duration_min").cast(td_types.Int32, strict=False).alias("recovery_minutes"),
            text("recovery_quality").alias("recovery_quality"),
        ).unique(subset=["case_id"])
    cases = merge(cases_head, new_cases, ["case_id"])
    all_cases = cases if cases is not None else cases_head

    if new_patients is not None:
        new_patients = new_patients.select(
            text("patient_id").alias("patient_id"),
            text("animal_name").alias("animal_name"),
            text("species").alias("species"),
            text("breed").alias("breed"),
            text("date_of_birth").str.to_date("%Y-%m-%d", strict=False).alias("date_of_birth"),
            text("weight_kg").cast(td_types.Float64, strict=False).alias("weight_kg"),
        ).unique(subset=["patient_id"])
        if all_cases is not None:
            new_patients = new_patients.join(
                all_cases.select("patient_id", "owner_id").unique(), on="patient_id", how="left",
            )
        else:
            new_patients = new_patients.with_columns(lit(None).cast(td_types.String).alias("owner_id"))
    patients = merge(patients_head, new_patients, ["patient_id"])

    if new_owners is not None:
        new_owners = new_owners.select(
            text("owner_id").alias("owner_id"),
            text("owner_name_full").alias("owner_name"),
            text("phone").alias("phone"),
            text("address_line").alias("address_line"),
            text("city").alias("city"),
            text("state").alias("state"),
            text("zip").alias("zip"),
        ).unique(subset=["owner_id"])
    owners = merge(owners_head, new_owners, ["owner_id"])

    return cases, patients, owners
