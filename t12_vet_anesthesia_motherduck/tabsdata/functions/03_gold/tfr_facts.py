#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col


# helper function that converts a date to an integer date key in YYYYMMDD format
def date_key(date: Expr) -> Expr:
    return (
        date.dt.year().cast(td_types.Int32) * 10000
        + date.dt.month().cast(td_types.Int32) * 100
        + date.dt.day().cast(td_types.Int32)
    )


# helper function that counts events per case and left joins the count onto the
# case table, missing counts default to 0
def with_count(frame: TableFrame, events: TableFrame, id_column: str, name: str) -> TableFrame:
    counts = events.group_by("case_id").agg(col(id_column).count().alias(name))
    return frame.join(counts, on="case_id", how="left").with_columns(
        col(name).fill_null(0).cast(td_types.Int32)
    )


# transformer that builds the fact tables for the star schema and adds the
# patient, owner and date keys to each event fact for joining to the dimensions
@transformer(
    input_tables=[
        "vet_silver/cases",
        "vet_silver/patients",
        "vet_silver/med_admin",
        "vet_silver/procedures",
        "vet_silver/labs",
        "vet_silver/case_staff",
        "vet_silver/case_remarks",
        "vet_silver/vitals",
    ],
    output_tables=[
        "fct_anesthesia_case",
        "fct_medication",
        "fct_procedure",
        "fct_lab_result",
        "fct_case_staff",
        "fct_case_remark",
        "fct_vital_sign",
    ],
)
def tfr_facts(
    cases: TableFrameSpec,
    patients: TableFrameSpec,
    med_admin: TableFrameSpec,
    procedures: TableFrameSpec,
    labs: TableFrameSpec,
    case_staff: TableFrameSpec,
    case_remarks: TableFrameSpec,
    vitals: TableFrameSpec,
) -> tuple[
    TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec,
]:
    cases = cases.with_columns(date_key(col("procedure_date")).alias("date_key"))
    keys = cases.select("case_id", "patient_id", "owner_id", "date_key")

    # adds weight and age at the time of the procedure from the patient table
    fct_case = cases.join(patients.select("patient_id", "date_of_birth", "weight_kg"), on="patient_id", how="left")
    fct_case = fct_case.with_columns(
        ((col("procedure_date") - col("date_of_birth")).dt.total_days() / 365.25).round(1).alias("age_years"),
    )
    fct_case = with_count(fct_case, procedures, "procedure_event_id", "procedure_count")
    fct_case = with_count(fct_case, med_admin, "med_admin_id", "medication_count")
    fct_case = with_count(fct_case, labs, "lab_result_id", "lab_result_count")
    fct_case = with_count(fct_case, case_staff, "person_id", "staff_count")
    fct_case = with_count(fct_case, case_remarks, "remark_id", "remark_count")
    fct_case = with_count(fct_case, vitals, "reading_id", "vital_sign_count")
    fct_case = fct_case.select(
        "case_id", "patient_id", "owner_id", "date_key", "procedure_date",
        "physical_status", "is_emergency", "recumbency", "sedation_level", "recovery_quality",
        "comments", "pre_op_eval",
        "anesthesia_start", "anesthesia_end", "recovery_end", "anesthesia_minutes", "recovery_minutes",
        "age_years", "weight_kg",
        "procedure_count", "medication_count", "lab_result_count", "staff_count", "remark_count",
        "vital_sign_count",
    )

    fct_medication = med_admin.join(keys, on="case_id", how="left")
    fct_procedure = procedures.join(keys, on="case_id", how="left")
    fct_lab_result = labs.join(keys, on="case_id", how="left")
    fct_case_staff = case_staff.join(keys, on="case_id", how="left")
    fct_case_remark = case_remarks.join(keys, on="case_id", how="left")

    # adds the minutes since anesthesia start to each monitor reading so every
    # case lines up on the same time axis
    fct_vital_sign = vitals.join(
        cases.select("case_id", "patient_id", "owner_id", "date_key", "anesthesia_start"), on="case_id", how="left",
    ).with_columns(
        (col("reading_time") - col("anesthesia_start")).dt.total_minutes(fractional=True).round(1)
        .alias("minutes_since_start"),
    ).drop("anesthesia_start")

    return fct_case, fct_medication, fct_procedure, fct_lab_result, fct_case_staff, fct_case_remark, fct_vital_sign
