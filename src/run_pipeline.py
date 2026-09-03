"""Run Project 2 cleaning and EDA in their required order."""

from clean_hospital_data import main as clean_data
from run_eda import main as run_eda


if __name__ == "__main__":
    # Why: The reports depend on the processed data, so this runner always cleans
    # the CMS raw extracts first and prevents accidental use of a stale clean file.
    clean_data()
    run_eda()
    print("Project 2 pipeline complete: cleaned data and EDA outputs are ready.")
