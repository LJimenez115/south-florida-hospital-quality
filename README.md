# South Florida Hospital Quality and Patient Experience

**Raw CMS CSVs → PostgreSQL cleaning and analysis in DataGrip → Tableau**

This project compares hospitals in Broward, Miami-Dade, and Palm Beach counties
with Florida benchmarks. Data preparation happens in SQL. No Python installation,
script, or dependency is required for this project.

## Questions

- How are overall quality stars distributed across local acute care hospitals?
- Which hospitals score above or below Florida on nurse communication, doctor
  communication, and willingness to recommend?
- How much usable data is available for each measure and reporting period?

## 1 Download the original data

Download the full CSV from each official CMS page, selecting the same release:

| CMS dataset | File | Destination table |
| --- | --- | --- |
| [Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u) | `Hospital_General_Information.csv` | `raw_cms.hospital_general` |
| [HCAHPS Hospital](https://data.cms.gov/provider-data/dataset/dgck-syfz) | `HCAHPS-Hospital.csv` | `raw_cms.hcahps_hospital` |
| [HCAHPS State](https://data.cms.gov/provider-data/dataset/84jm-wiui) | `HCAHPS-State.csv` | `raw_cms.hcahps_state` |

Save files under `data/raw/`. Record each source URL, release date, download date,
and filename in your notes. Download date and measurement period are different.
The schema matches the official August 2026 CSV headers; compare new headers
before importing a future release.

Excel is optional for inspection. Import the original CSV, not an Excel-resaved
copy that might change identifiers or dates. Facility IDs must remain text.

## 2 Create raw tables and import with DataGrip

1. Connect DataGrip to PostgreSQL. If needed, run `sql/00_create_database.sql`
   once from a connection to `postgres`, outside a transaction. Then connect to
   `south_florida_hospital_quality`.
2. Run `sql/01_create_schema.sql`. It creates raw text tables in `raw_cms` and
   the separate `hospital_analysis` schema. It does not drop existing tables.
3. Right-click each destination table and choose **Import/Export → Import Data
   from File(s)**. Select the original CSV, enable the header row, use UTF-8 and
   comma delimiters, and map the quoted source names exactly. Treat empty fields
   as NULL. Import once per table; repeated imports create duplicates.
4. Check imported row counts against the source files.

Keep one CMS release per database. For another snapshot, use a separate database
and repeat setup rather than mixing releases. If the raw tables already exist,
do not blindly import another copy over them.

## 3 Clean and validate in SQL

Run these scripts in DataGrip:

1. `sql/02_clean_data.sql` — creates reusable cleaned views and checks the data.
2. `sql/04_quality_checks.sql` — inspect counts, missing values, keys, and coverage.
3. `sql/03_analysis_queries.sql` — answer the project questions.

Cleaning preserves raw data, trims text, retains identifiers, parses dates,
converts valid scores, and separates unavailable scores from zero. It rejects
missing keys, duplicate keys, unmatched facilities, invalid periods, and missing
state-period matches for the selected measures. A failed run rolls back its
changes. If your SQL client leaves a transaction open after an error, execute
`ROLLBACK;`, investigate the raw rows, and rerun.

Views reflect their source tables. After any raw-data change, rerun cleaning and
quality checks before using results. Raw staging tables intentionally have no
business-key constraints so original source problems can be inspected.

## 4 Build the Tableau dashboard

In Tableau Desktop, connect to PostgreSQL and select `hospital_analysis` views.
If your Tableau edition lacks the connector, export query results from DataGrip
as CSVs and open them in Tableau. Dashboard construction is the next step; the
current repository does not contain a completed Tableau dashboard.

Suggested pages:

- **Regional overview:** hospital counts, rating distribution, and missing-rating counts.
- **Patient experience:** hospital percentages, matching Florida scores,
  percentage-point gaps, and filters for measure, county, hospital, and period.

Use `patient_experience_comparison` for survey comparisons. It joins by facility
ID, measure, and period. Avoid joins on hospital name or pooling different periods.

## Metric definitions and limits

- South Florida means **Broward, Miami-Dade, and Palm Beach**. Example queries
  restrict comparisons to **Acute Care Hospitals**.
- Overall hospital quality stars and HCAHPS patient-experience stars are distinct.
  A common release does not imply identical underlying quality and survey periods.
- Nurse communication (`H_COMP_1_A_P`), doctor communication (`H_COMP_2_A_P`), and
  definite recommendation (`H_RECMND_DY`) use favorable-response percentages.
  Hospital minus state score is a gap in **percentage points**.
- Published Florida benchmarks include local hospitals. The optional rest-of-Florida
  star comparison excludes local hospitals and uses an **unweighted facility
  average**, not a CMS-published benchmark.
- Missing and suppressed scores remain NULL. Original values, footnotes, and
  survey-count ranges remain available. Never invent exact counts from ranges.
- These comparisons do not establish why scores differ or rank clinical
  effectiveness. Inspect coverage and footnotes before interpreting gaps.

## Repository contents

- `sql/` — setup, raw schema, cleaning views, analysis, and validation.
- `archive/` — historical outputs from the retired Python workflow, clearly labeled.
- `VALIDATION.md` — checks performed for the SQL migration.

The earlier executable Python files remain in Git history. The companion
[Miami 311 project](https://github.com/LJimenez115/miami-311-service-operations)
retains the Python → SQL → Tableau workflow.
