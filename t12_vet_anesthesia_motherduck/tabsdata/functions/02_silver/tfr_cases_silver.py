#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, lit


# helper function that casts a raw column to string and trims whitespace, blank
# values become null
def text(name: str) -> Expr:
    return col(name).cast(td_types.String).str.extract(r"^\s*(\S.*?)\s*$", 1)


# helper function that combines the procedure date with an HH:MM time column to
# create a timestamp
def at(date: Expr, time_column: str) -> Expr:
    return date.dt.combine(text(time_column).str.to_time("%H:%M", strict=False))


# transformer that casts the raw cases, patients and owners tables to their
# proper types and joins owner_id from cases onto patients
@transformer(
    input_tables=[
        "vet_landing/raw_cases",
        "vet_landing/raw_patients",
        "vet_landing/raw_owners",
    ],
    output_tables=["cases", "patients", "owners"],
)
def tfr_cases_silver(
    raw_cases: TableFrameSpec,
    raw_patients: TableFrameSpec,
    raw_owners: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec, TableFrameSpec]:
    procedure_date = text("procedure_date").str.to_date("%Y-%m-%d", strict=False)

    cases = raw_cases.select(
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

    patients = raw_patients.select(
        text("patient_id").alias("patient_id"),
        text("animal_name").alias("animal_name"),
        text("species").alias("species"),
        text("breed").alias("breed"),
        text("date_of_birth").str.to_date("%Y-%m-%d", strict=False).alias("date_of_birth"),
        text("weight_kg").cast(td_types.Float64, strict=False).alias("weight_kg"),
    ).unique(subset=["patient_id"])
    patients = patients.join(cases.select("patient_id", "owner_id").unique(), on="patient_id", how="left")

    owners = raw_owners.select(
        text("owner_id").alias("owner_id"),
        text("owner_name_full").alias("owner_name"),
        text("phone").alias("phone"),
        text("address_line").alias("address_line"),
        text("city").alias("city"),
        text("state").alias("state"),
        text("zip").alias("zip"),
    ).unique(subset=["owner_id"])

    return cases, patients, owners
