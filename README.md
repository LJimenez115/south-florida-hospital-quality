# South Florida Hospital Quality & Patient Experience Analysis

This project compares Miami-Dade and Broward hospitals with the rest of Florida using official Centers for Medicare & Medicaid Services (CMS) Hospital General Information and HCAHPS patient-experience data.

## Questions answered

- How do South Florida hospitals’ overall quality ratings compare with the rest of Florida?
- Which hospitals have the most favorable or unfavorable CMS measure-group results?
- How do patient-experience star ratings vary by measure and benchmark group?

## Run the EDA pipeline

```bash
# Why: Create an isolated local environment so package versions are reproducible.
python3 -m venv .venv
# Why: Install the exact analysis libraries declared for this project.
.venv/bin/pip install -r requirements.txt
# Why: Clean CMS extracts first, then generate EDA tables and charts from the validated files.
.venv/bin/python src/run_pipeline.py
```

## Load the PostgreSQL database

This project uses PostgreSQL rather than a local SQLite file. Install and start PostgreSQL first, then run the following from this project folder.

```bash
# Why: Create one isolated database so this project's rebuild never changes another local database.
psql -U your_postgres_user -d postgres -f sql/00_create_database.sql
# Why: Copy the safe template locally; `.env` is ignored so the password cannot be committed.
cp .env.example .env
# Why: After adding your PostgreSQL user/password details to `.env`, this command creates the schema and loads the cleaned CMS data.
.venv/bin/python scripts/build_database.py
```

Power BI connects through **Get Data → PostgreSQL database**. Use `localhost`, the default port `5432`, and the database name `south_florida_hospital_quality`; do not publish the password or `.env` file.

## Data scope and interpretation

- The local group is hospitals whose CMS `countyparish` value is `BROWARD` or `MIAMI-DADE`.
- The benchmark group is the rest of Florida, preventing South Florida from being compared against a total that includes itself.
- Missing or `Not Available` ratings are kept as missing; they are never converted to zero.
- HCAHPS star ratings summarize standardized patient surveys and should not be interpreted as clinical outcomes or causal evidence.
- The PostgreSQL model contains hospital, HCAHPS measure, and survey-period dimensions plus quality and patient-experience fact tables.
