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


# helper function that combines the procedure date with an HH:MM time column to
# create a timestamp
def at(time_column: str) -> Expr:
    return col("procedure_date").dt.combine(text(time_column).str.to_time("%H:%M", strict=False))


# helper function that extracts the numeric part of a dose string as a float
def amount(name: str) -> Expr:
    return text(name).str.extract(r"^([\d.]+)", 1).cast(td_types.Float64, strict=False)


# helper function that extracts the unit part of a dose string
def unit(name: str) -> Expr:
    return text(name).str.extract(r"^[\d.]+\s*(\S+)$", 1)


# helper function that casts a monitor reading to a float, blank readings become
# null
def reading(name: str) -> Expr:
    return text(name).cast(td_types.Float64, strict=False)


# helper function that parses a monitor timestamp to a datetime, normalizes the
# T separator first since the csv reader can infer the column as a datetime and
# the text cast then uses a space
def timestamp(name: str) -> Expr:
    return text(name).str.replace("T", " ").str.to_datetime("%Y-%m-%d %H:%M:%S%.f", time_unit="us", strict=False)


# transformer that casts the raw event tables to their proper types, renames
# columns to snake_case and uses the case dates to convert clock times to
# timestamps
@transformer(
    input_tables=[
        "vet_landing/raw_med_admin",
        "vet_landing/raw_procedures",
        "vet_landing/raw_labs",
        "vet_landing/raw_case_remarks",
        "vet_landing/raw_vitals",
        "cases",
    ],
    output_tables=["med_admin", "procedures", "labs", "case_remarks", "vitals"],
)
def tfr_case_events_silver(
    raw_med_admin: TableFrameSpec,
    raw_procedures: TableFrameSpec,
    raw_labs: TableFrameSpec,
    raw_case_remarks: TableFrameSpec,
    raw_vitals: TableFrameSpec,
    cases: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec]:
    case_dates = cases.select("case_id", "procedure_date")

    # splits each dose string into a numeric column and a unit column
    med_admin = raw_med_admin.select(
        text("med_admin_id").alias("med_admin_id"),
        text("case_id").alias("case_id"),
        text("drug_name").alias("drug_name"),
        amount("Dispensed").alias("dispensed_amount"),
        unit("Dispensed").alias("dispensed_unit"),
        amount("Dose").alias("dose_amount"),
        unit("Dose").alias("dose_unit"),
        amount("Administered").alias("administered_amount"),
        unit("Administered").alias("administered_unit"),
        amount("Discarded").alias("discarded_amount"),
        unit("Discarded").alias("discarded_unit"),
        text("Reason Given").alias("reason_given"),
    ).unique(subset=["med_admin_id"])

    procedures = raw_procedures.with_columns(text("case_id").alias("case_id")).join(
        case_dates, on="case_id", how="left",
    ).select(
        text("procedure_event_id").alias("procedure_event_id"),
        col("case_id"),
        text("procedure_name").alias("procedure_name"),
        at("start_time").alias("start_time"),
        at("end_time").alias("end_time"),
        text("duration_min").cast(td_types.Int32, strict=False).alias("duration_minutes"),
        text("sequence").cast(td_types.Int32, strict=False).alias("sequence"),
    ).unique(subset=["procedure_event_id"])

    # separates numeric lab results into their own column and keeps the original
    # value as text for non numeric results
    labs = raw_labs.select(
        text("lab_result_id").alias("lab_result_id"),
        text("case_id").alias("case_id"),
        text("test_name").alias("test_name"),
        text("result_value").cast(td_types.Float64, strict=False).alias("result_numeric"),
        text("result_value").alias("result_text"),
        text("unit").alias("unit"),
    ).unique(subset=["lab_result_id"])

    case_remarks = raw_case_remarks.with_columns(text("case_id").alias("case_id")).join(
        case_dates, on="case_id", how="left",
    ).select(
        text("remark_id").alias("remark_id"),
        col("case_id"),
        at("remark_time").alias("remark_time"),
        text("remark_text").alias("remark_text"),
    ).unique(subset=["remark_id"])

    # parses the monitor timestamps and renames the monitor columns to snake_case
    # with their units, readings the monitor didn't take at that time stay null
    vitals = raw_vitals.select(
        text("reading_id").alias("reading_id"),
        text("case_id").alias("case_id"),
        timestamp("timestamp").alias("reading_time"),
        reading("Heart Rate").alias("heart_rate_bpm"),
        reading("Respiratory Rate").alias("respiratory_rate_bpm"),
        reading("Pulse Oximetry").alias("spo2_pct"),
        reading("End Tidal CO2").alias("etco2_mmhg"),
        reading("Expired Agent").alias("expired_agent_pct"),
        reading("Temperature").alias("temperature_f"),
        reading("Non-Invasive Systolic Pressure").alias("nibp_systolic_mmhg"),
        reading("Non-Invasive Diastolic Pressure").alias("nibp_diastolic_mmhg"),
        reading("Non-Invasive Mean Arterial Pressure").alias("nibp_mean_mmhg"),
        reading("Invasive Systolic Pressure").alias("ibp_systolic_mmhg"),
        reading("Invasive Diastolic Pressure").alias("ibp_diastolic_mmhg"),
        reading("Invasive Mean Arterial Pressure").alias("ibp_mean_mmhg"),
        reading("Oxygen").alias("oxygen_flow_lpm"),
        reading("Vaporizer").alias("vaporizer_pct"),
        reading("Medical Air").alias("medical_air_lpm"),
        reading("Central Venous Pressure").alias("cvp_mmhg"),
        reading("Perfusion Index").alias("perfusion_index_pct"),
        reading("Pleth. Variability Index").alias("pvi_pct"),
    ).unique(subset=["reading_id"])

    return med_admin, procedures, labs, case_remarks, vitals
