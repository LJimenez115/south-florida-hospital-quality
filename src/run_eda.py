"""Create quality and patient-experience EDA outputs for Project 2."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Why: EDA reads only processed data, ensuring raw source rows stay unchanged and
# the same cleaning decisions are used consistently in every chart and table.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
HOSPITAL_FILE = PROCESSED_DIR / "florida_hospital_quality_clean.csv"
HCAHPS_FILE = PROCESSED_DIR / "florida_hcahps_star_ratings_clean.csv"

# Why: A consistent, accessible theme makes generated PNGs suitable for a README,
# portfolio case study, or later comparison against Power BI visuals.
sns.set_theme(style="whitegrid", palette="colorblind")


def read_clean_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the two validated datasets needed for quality and experience analysis."""
    # Why: Facility IDs remain text so any leading zeroes survive if the datasets
    # are joined or used as database keys in the next project stage.
    hospitals = pd.read_csv(HOSPITAL_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    hcahps = pd.read_csv(HCAHPS_FILE, dtype={"facility_id": "string", "zip_code": "string"})
    return hospitals, hcahps


def export_summary_tables(hospitals: pd.DataFrame, hcahps: pd.DataFrame) -> None:
    """Export Power BI-ready benchmark and hospital-level tables."""
    # Why: This treats missing CMS ratings as missing instead of zero, so the
    # average rating represents only hospitals with an actually published rating.
    quality_summary = (
        hospitals.groupby("benchmark_group")
        .agg(
            hospital_count=("facility_id", "size"),
            hospitals_with_rating=("hospital_overall_rating", "count"),
            average_overall_rating=("hospital_overall_rating", "mean"),
            median_overall_rating=("hospital_overall_rating", "median"),
            emergency_service_hospitals=("emergency_services", lambda values: (values == "Yes").sum()),
        )
        .reset_index()
    )
    quality_summary["rated_hospital_percent"] = (
        100 * quality_summary["hospitals_with_rating"] / quality_summary["hospital_count"]
    ).round(1)
    quality_summary["average_overall_rating"] = quality_summary["average_overall_rating"].round(2)
    quality_summary.to_csv(REPORT_DIR / "quality_benchmark_summary.csv", index=False)

    # Why: The local hospital table supports a Power BI detail page or searchable
    # table visual while retaining only official facility-level public attributes.
    south_florida_hospitals = hospitals.loc[
        hospitals["benchmark_group"] == "South Florida",
        ["facility_id", "facility_name", "countyparish", "citytown", "zip_code", "hospital_type",
         "hospital_ownership", "emergency_services", "hospital_overall_rating",
         "count_of_mort_measures_better", "count_of_mort_measures_worse",
         "count_of_safety_measures_better", "count_of_safety_measures_worse",
         "count_of_readm_measures_better", "count_of_readm_measures_worse"],
    ].sort_values(["countyparish", "hospital_overall_rating", "facility_name"], ascending=[True, False, True])
    south_florida_hospitals.to_csv(REPORT_DIR / "south_florida_hospital_overview.csv", index=False)

    # Why: This compares the same standardized HCAHPS measure in non-overlapping
    # groups, avoiding a local-versus-total benchmark that double-counts local hospitals.
    experience_summary = (
        hcahps.groupby(["benchmark_group", "hcahps_measure_id", "hcahps_question"], dropna=False)
        .agg(
            hospitals_with_rating=("facility_id", "nunique"),
            average_star_rating=("patient_survey_star_rating", "mean"),
            median_star_rating=("patient_survey_star_rating", "median"),
            average_completed_surveys=("number_of_completed_surveys", "mean"),
        )
        .reset_index()
    )
    experience_summary["average_star_rating"] = experience_summary["average_star_rating"].round(2)
    experience_summary["average_completed_surveys"] = experience_summary["average_completed_surveys"].round(0)
    experience_summary.to_csv(REPORT_DIR / "hcahps_experience_benchmark.csv", index=False)


def create_charts(hospitals: pd.DataFrame, hcahps: pd.DataFrame) -> None:
    """Render the main rating, local-hospital, and HCAHPS comparison charts."""
    # Why: This count chart shows both rating distribution and reporting gaps before
    # readers infer that an average score represents every hospital in a group.
    rating_data = hospitals.copy()
    rating_data["rating_label"] = rating_data["hospital_overall_rating"].fillna("Not Available").astype(str)
    rating_order = ["1.0", "2.0", "3.0", "4.0", "5.0", "Not Available"]
    figure, axis = plt.subplots(figsize=(10, 5.5))
    sns.countplot(data=rating_data, x="rating_label", hue="benchmark_group", order=rating_order, ax=axis)
    axis.set(title="CMS Overall Hospital Rating Distribution", xlabel="Overall rating", ylabel="Hospitals")
    axis.legend(title="Benchmark group")
    figure.tight_layout()
    figure.savefig(REPORT_DIR / "overall_rating_distribution.png", dpi=180)
    plt.close(figure)

    # Why: A sorted local view makes the public hospital-level comparison readable
    # without hiding missing ratings or implying that the values are causal rankings.
    south = hospitals[hospitals["benchmark_group"] == "South Florida"].copy()
    south = south.dropna(subset=["hospital_overall_rating"]).sort_values("hospital_overall_rating")
    figure, axis = plt.subplots(figsize=(10, 9))
    sns.barplot(data=south, x="hospital_overall_rating", y="facility_name", hue="countyparish",
                dodge=False, palette="colorblind", ax=axis)
    axis.set(title="South Florida Hospitals with Published CMS Overall Ratings", xlabel="CMS overall rating", ylabel="Hospital")
    axis.set(xlim=(0, 5.2))
    axis.legend(title="County")
    figure.tight_layout()
    figure.savefig(REPORT_DIR / "south_florida_hospital_ratings.png", dpi=180)
    plt.close(figure)

    # Why: HCAHPS star rows use standardized 1–5 ratings; averaging them by the
    # same measure exposes differences in patient experience without mixing measures.
    experience = hcahps.dropna(subset=["patient_survey_star_rating"]).copy()
    measure_order = (
        experience.groupby("hcahps_question")["patient_survey_star_rating"].mean()
        .sort_values().index
    )
    figure, axis = plt.subplots(figsize=(12, 7))
    sns.barplot(data=experience, x="patient_survey_star_rating", y="hcahps_question",
                hue="benchmark_group", order=measure_order, errorbar=None, ax=axis)
    axis.set(title="Average HCAHPS Star Rating by Patient-Experience Measure", xlabel="Average star rating", ylabel="HCAHPS measure")
    axis.set(xlim=(0, 5.2))
    axis.legend(title="Benchmark group")
    figure.tight_layout()
    figure.savefig(REPORT_DIR / "hcahps_experience_comparison.png", dpi=180)
    plt.close(figure)


def main() -> None:
    """Run all Project 2 EDA exports and charts."""
    # Why: A dedicated reports folder keeps Power BI-ready outputs separate from
    # source data and makes it obvious which files document the EDA results.
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    hospitals, hcahps = read_clean_data()
    export_summary_tables(hospitals, hcahps)
    create_charts(hospitals, hcahps)
    print(f"Created EDA tables and charts in: {REPORT_DIR}")


if __name__ == "__main__":
    # Why: The guard prevents report generation from starting merely because a
    # future script imports one of these reusable EDA helper functions.
    main()
