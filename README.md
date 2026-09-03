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

## Data scope and interpretation

- The local group is hospitals whose CMS `countyparish` value is `BROWARD` or `MIAMI-DADE`.
- The benchmark group is the rest of Florida, preventing South Florida from being compared against a total that includes itself.
- Missing or `Not Available` ratings are kept as missing; they are never converted to zero.
- HCAHPS star ratings summarize standardized patient surveys and should not be interpreted as clinical outcomes or causal evidence.
