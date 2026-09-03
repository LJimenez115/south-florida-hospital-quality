"""Build the normalized PostgreSQL database for CMS hospital quality analysis."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, make_url


# Why: These paths are derived from the project location so the build works from
# VS Code and from a cloned GitHub repository without machine-specific edits.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
HOSPITAL_FILE = PROCESSED_DIR / "florida_hospital_quality_clean.csv"
HCAHPS_FILE = PROCESSED_DIR / "florida_hcahps_star_ratings_clean.csv"
SCHEMA_FILE = PROJECT_ROOT / "sql" / "01_create_schema.sql"
DATABASE_DIR = PROJECT_ROOT / "database"
BUILD_REPORT = DATABASE_DIR / "database_build_report.json"
DATABASE_NAME = "south_florida_hospital_quality"


def get_database_url() -> str:
    """Read and validate the local PostgreSQL connection string."""
    # Why: Loading `.env` makes the local connection easy to configure without
    # putting a database password in the repository or a Power BI screenshot.
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is missing. Copy .env.example to .env and add your password.")
    parsed_url = make_url(database_url)
    # Why: The schema clears only project tables on a rebuild, so this check avoids
    # accidentally using a connection string for a different PostgreSQL database.
    if parsed_url.database != DATABASE_NAME:
        raise ValueError(f"DATABASE_URL must use the dedicated `{DATABASE_NAME}` database.")
    return database_url


def make_dimension(
    frame: pd.DataFrame,
    columns: list[str],
    key_column: str,
    table_name: str,
    connection: Connection,
) -> pd.DataFrame:
    """Create a surrogate-key dimension and keep its source-column mapping."""
    # Why: Surrogate keys shrink the fact tables and make the model resilient if a
    # hospital name or CMS question label changes after a future source refresh.
    dimension = frame[columns].drop_duplicates().sort_values(columns).reset_index(drop=True)
    dimension.insert(0, key_column, range(1, len(dimension) + 1))
    dimension.to_sql(table_name, connection, if_exists="append", index=False)
    return dimension


def main() -> None:
    """Create the database, load dimensions/facts, and validate relationships."""
    # Why: The database is built only from cleaned data, keeping the source extracts
    # separate and ensuring the same cleaning logic is used in EDA and SQL.
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    hospitals = pd.read_csv(HOSPITAL_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    hcahps = pd.read_csv(HCAHPS_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    hospitals = hospitals.rename(columns={
        "countyparish": "county_name", "citytown": "city_name", "state": "state_code",
        "meets_criteria_for_birthing_friendly_designation": "birthing_friendly_designation",
    })
    if hospitals["facility_id"].duplicated().any():
        raise ValueError("Hospital source must have one row per facility ID.")

    # Why: PostgreSQL is managed outside the repository, while the schema file
    # recreates only the tables in this dedicated project database on every load.
    engine = create_engine(get_database_url())
    with engine.begin() as connection:
        for statement in SCHEMA_FILE.read_text(encoding="utf-8").split(";"):
            if statement.strip():
                connection.exec_driver_sql(statement)

        hospital_columns = [
            "facility_id", "facility_name", "county_name", "city_name", "state_code", "zip_code",
            "hospital_type", "hospital_ownership", "emergency_services",
            "birthing_friendly_designation", "benchmark_group",
        ]
        hospital_dimension = make_dimension(
            hospitals, hospital_columns, "hospital_key", "dim_hospital", connection
        )
        measure_dimension = make_dimension(
            hcahps, ["hcahps_measure_id", "hcahps_question"], "hcahps_measure_key",
            "dim_hcahps_measure", connection,
        )
        # Why: The clean-file column names are short, while the database names make
        # the survey period's meaning explicit; rename only at the load boundary.
        period_dimension = (
            hcahps[["start_date", "end_date"]]
            .drop_duplicates()
            .sort_values(["start_date", "end_date"])
            .reset_index(drop=True)
        )
        period_dimension.insert(0, "survey_period_key", range(1, len(period_dimension) + 1))
        period_dimension_for_database = period_dimension.rename(columns={
            "start_date": "survey_start_date", "end_date": "survey_end_date",
        }).copy()
        # Why: CMS provides reporting-window dates as text; converting them before
        # insertion lets PostgreSQL store true DATE values and reject invalid periods.
        for column in ["survey_start_date", "survey_end_date"]:
            period_dimension_for_database[column] = pd.to_datetime(
                period_dimension_for_database[column], errors="raise"
            ).dt.date
        period_dimension_for_database.to_sql("dim_survey_period", connection, if_exists="append", index=False)

        # Why: The hospital quality source is one row per facility, so it maps to a
        # fact table with exactly one current snapshot row for each hospital key.
        quality_fact = hospitals.merge(
            hospital_dimension[["facility_id", "hospital_key"]], on="facility_id", how="left"
        )
        quality_fact.insert(0, "hospital_quality_key", range(1, len(quality_fact) + 1))
        quality_fact = quality_fact.rename(columns={
            "hospital_overall_rating": "overall_hospital_rating",
            "mort_group_measure_count": "mortality_measures_reported",
            "count_of_mort_measures_better": "mortality_measures_better",
            "count_of_mort_measures_worse": "mortality_measures_worse",
            "safety_group_measure_count": "safety_measures_reported",
            "count_of_safety_measures_better": "safety_measures_better",
            "count_of_safety_measures_worse": "safety_measures_worse",
            "readm_group_measure_count": "readmission_measures_reported",
            "count_of_readm_measures_better": "readmission_measures_better",
            "count_of_readm_measures_worse": "readmission_measures_worse",
            "pt_exp_group_measure_count": "patient_experience_measures_reported",
            "te_group_measure_count": "timely_effective_measures_reported",
        })
        quality_columns = [
            "hospital_quality_key", "hospital_key", "overall_hospital_rating", "mortality_measures_reported",
            "mortality_measures_better", "mortality_measures_worse", "safety_measures_reported",
            "safety_measures_better", "safety_measures_worse", "readmission_measures_reported",
            "readmission_measures_better", "readmission_measures_worse", "patient_experience_measures_reported",
            "timely_effective_measures_reported",
        ]
        quality_fact[quality_columns].to_sql("fact_hospital_quality", connection, if_exists="append", index=False)

        # Why: Each HCAHPS row receives the three dimension keys that define its
        # grain: one hospital, one patient-experience measure, and one survey period.
        hcahps_fact = hcahps.merge(
            hospital_dimension[["facility_id", "hospital_key"]], on="facility_id", how="left"
        ).merge(
            measure_dimension, on=["hcahps_measure_id", "hcahps_question"], how="left"
        ).merge(period_dimension, on=["start_date", "end_date"], how="left")
        if hcahps_fact[["hospital_key", "hcahps_measure_key", "survey_period_key"]].isna().any().any():
            raise ValueError("A HCAHPS rating could not be mapped to every required dimension.")
        if hcahps_fact.duplicated(["hospital_key", "hcahps_measure_key", "survey_period_key"]).any():
            raise ValueError("HCAHPS source contains duplicate hospital-measure-period rows.")
        hcahps_fact.insert(0, "hcahps_rating_key", range(1, len(hcahps_fact) + 1))
        hcahps_fact = hcahps_fact.rename(columns={
            "number_of_completed_surveys": "completed_survey_count",
        })
        hcahps_columns = [
            "hcahps_rating_key", "hospital_key", "hcahps_measure_key", "survey_period_key",
            "patient_survey_star_rating", "completed_survey_count", "survey_response_rate_percent",
        ]
        hcahps_fact[hcahps_columns].to_sql("fact_hcahps_rating", connection, if_exists="append", index=False)

        # Why: Counts and the built-in foreign-key audit confirm the two facts and
        # their dimensions were loaded completely before the database is delivered.
        table_names = [
            "dim_hospital", "dim_hcahps_measure", "dim_survey_period", "fact_hospital_quality",
            "fact_hcahps_rating",
        ]
        counts = {
            name: connection.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            for name in table_names
        }
        # Why: PostgreSQL enforces every foreign key as rows are inserted, so a
        # successful transaction confirms the declared relationships are valid.
        foreign_key_check = "passed (PostgreSQL constraints enforced during insert)"

    engine.dispose()

    # Why: The build report documents successful row counts for the README and
    # makes it easy to verify a later rebuild against this completed database.
    BUILD_REPORT.write_text(
        json.dumps({"database_platform": "PostgreSQL", "database_name": DATABASE_NAME,
                    "table_row_counts": counts, "foreign_key_check": foreign_key_check}, indent=2),
        encoding="utf-8",
    )
    print(f"Loaded PostgreSQL database: {DATABASE_NAME}")
    print(f"Created build report: {BUILD_REPORT}")


if __name__ == "__main__":
    # Why: The guard allows database helper code to be imported without triggering
    # a rebuild that would replace the dedicated PostgreSQL project tables.
    main()
