"""Clean CMS hospital and HCAHPS extracts for South Florida benchmarking."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


# Why: Project-relative paths make the pipeline portable across VS Code, terminal,
# and future GitHub clones without manual path edits.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
HOSPITAL_RAW_FILE = RAW_DIR / "cms_hospital_general_information_florida_raw.csv"
HCAHPS_RAW_FILE = RAW_DIR / "cms_patient_survey_hcahps_florida_raw.csv"
HOSPITAL_CLEAN_FILE = PROCESSED_DIR / "florida_hospital_quality_clean.csv"
HCAHPS_CLEAN_FILE = PROCESSED_DIR / "florida_hcahps_star_ratings_clean.csv"
QUALITY_REPORT = PROCESSED_DIR / "cleaning_quality_report.json"

# Why: These two counties define the local project scope while all other Florida
# records remain available as a non-overlapping state benchmark.
SOUTH_FLORIDA_COUNTIES = {"BROWARD", "MIAMI-DADE"}

# Why: CMS supplies these figures as text. Converting only known numeric measures
# makes calculations reliable without altering labels such as ownership or type.
NUMERIC_HOSPITAL_COLUMNS = [
    "hospital_overall_rating", "mort_group_measure_count", "count_of_facility_mort_measures",
    "count_of_mort_measures_better", "count_of_mort_measures_no_different",
    "count_of_mort_measures_worse", "safety_group_measure_count",
    "count_of_facility_safety_measures", "count_of_safety_measures_better",
    "count_of_safety_measures_no_different", "count_of_safety_measures_worse",
    "readm_group_measure_count", "count_of_facility_readm_measures",
    "count_of_readm_measures_better", "count_of_readm_measures_no_different",
    "count_of_readm_measures_worse", "pt_exp_group_measure_count",
    "count_of_facility_pt_exp_measures", "te_group_measure_count",
    "count_of_facility_te_measures",
]


def normalize_text(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim source text and represent blanks with pandas missing values."""
    # Why: Blank strings would behave like valid categories in group-by results,
    # so normalizing them prevents misleading "empty" labels in charts and SQL.
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].astype("string").str.strip().replace("", pd.NA)
    return frame


def add_benchmark_group(frame: pd.DataFrame) -> pd.DataFrame:
    """Label South Florida and non-overlapping Rest of Florida records."""
    # Why: Comparing South Florida against the rest of Florida avoids a benchmark
    # that includes the same hospitals being evaluated.
    frame["benchmark_group"] = frame["countyparish"].isin(SOUTH_FLORIDA_COUNTIES).map(
        {True: "South Florida", False: "Rest of Florida"}
    )
    frame["is_south_florida"] = (frame["benchmark_group"] == "South Florida").astype(int)
    return frame


def clean_hospital_information() -> pd.DataFrame:
    """Clean hospital-level operational and overall-quality fields."""
    # Why: Facility IDs and ZIP codes are identifiers, so strings preserve leading
    # zeroes and make later joins to HCAHPS precise.
    frame = pd.read_csv(HOSPITAL_RAW_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    required = {"facility_id", "facility_name", "countyparish", "state", "hospital_overall_rating"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Hospital source is missing required columns: {sorted(missing)}")
    frame = normalize_text(frame)
    for column in NUMERIC_HOSPITAL_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = add_benchmark_group(frame)

    # Why: The source must have one record per CMS facility before it can serve as
    # a hospital dimension for patient-experience records and later SQL modeling.
    if frame["facility_id"].duplicated().any():
        raise ValueError("Hospital General Information has duplicate facility IDs.")
    return frame


def clean_hcahps_star_ratings() -> pd.DataFrame:
    """Keep hospital-level HCAHPS star-rating records and convert their measures."""
    # Why: The source includes response percentages, linear scores, and star rows.
    # Keeping star-rating rows gives a consistent, compact comparison measure.
    frame = pd.read_csv(HCAHPS_RAW_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    required = {"facility_id", "countyparish", "hcahps_measure_id", "patient_survey_star_rating"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"HCAHPS source is missing required columns: {sorted(missing)}")
    frame = normalize_text(frame)
    frame = frame[frame["hcahps_measure_id"].str.endswith("_STAR_RATING", na=False)].copy()
    frame["patient_survey_star_rating"] = pd.to_numeric(
        frame["patient_survey_star_rating"], errors="coerce"
    )
    frame["number_of_completed_surveys"] = pd.to_numeric(
        frame["number_of_completed_surveys"], errors="coerce"
    )
    frame["survey_response_rate_percent"] = pd.to_numeric(
        frame["survey_response_rate_percent"], errors="coerce"
    )
    frame["start_date"] = pd.to_datetime(frame["start_date"], format="%m/%d/%Y", errors="coerce")
    frame["end_date"] = pd.to_datetime(frame["end_date"], format="%m/%d/%Y", errors="coerce")
    frame = add_benchmark_group(frame)
    return frame


def main() -> None:
    """Write clean hospital and patient-experience datasets plus quality evidence."""
    # Why: Processed outputs are separate from raw CMS downloads, preserving the
    # original public files for inspection and reproducibility.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    hospitals = clean_hospital_information()
    hcahps = clean_hcahps_star_ratings()
    hospitals.to_csv(HOSPITAL_CLEAN_FILE, index=False, encoding="utf-8-sig")
    hcahps.to_csv(HCAHPS_CLEAN_FILE, index=False, encoding="utf-8-sig")

    # Why: The quality report exposes the amount of usable information before EDA
    # charts summarize only hospitals or measures with published CMS ratings.
    report = {
        "florida_hospital_count": int(len(hospitals)),
        "south_florida_hospital_count": int(hospitals["is_south_florida"].sum()),
        "hospitals_with_overall_rating": int(hospitals["hospital_overall_rating"].notna().sum()),
        "florida_hcahps_star_rows": int(len(hcahps)),
        "south_florida_hcahps_star_rows": int(hcahps["is_south_florida"].sum()),
        "hcahps_rows_with_numeric_star_rating": int(hcahps["patient_survey_star_rating"].notna().sum()),
    }
    QUALITY_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Created cleaned hospital file: {HOSPITAL_CLEAN_FILE}")
    print(f"Created cleaned HCAHPS file: {HCAHPS_CLEAN_FILE}")
    print(f"Created cleaning quality report: {QUALITY_REPORT}")


if __name__ == "__main__":
    # Why: The guard makes the module safe to import in a future database builder
    # or test file without automatically writing output files.
    main()
