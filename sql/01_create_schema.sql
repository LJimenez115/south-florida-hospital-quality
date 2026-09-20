-- Run once in your project database, then import the original CMS CSVs in DataGrip.

-- Exact source headers are quoted, so CSV columns can be mapped by name.

-- All raw columns are text to preserve IDs, footnotes, and unavailable values.

BEGIN;

CREATE SCHEMA IF NOT EXISTS raw_cms;

CREATE SCHEMA IF NOT EXISTS hospital_analysis;

-- Import Hospital_General_Information.csv
CREATE TABLE raw_cms.hospital_general (
    "Facility ID" text,
    "Facility Name" text,
    "Address" text,
    "City/Town" text,
    "State" text,
    "ZIP Code" text,
    "County/Parish" text,
    "Telephone Number" text,
    "Hospital Type" text,
    "Hospital Ownership" text,
    "Emergency Services" text,
    "Meets criteria for birthing friendly designation" text,
    "Hospital overall rating" text,
    "Hospital overall rating footnote" text,
    "MORT Group Measure Count" text,
    "Count of Facility MORT Measures" text,
    "Count of MORT Measures Better" text,
    "Count of MORT Measures No Different" text,
    "Count of MORT Measures Worse" text,
    "MORT Group Footnote" text,
    "Safety Group Measure Count" text,
    "Count of Facility Safety Measures" text,
    "Count of Safety Measures Better" text,
    "Count of Safety Measures No Different" text,
    "Count of Safety Measures Worse" text,
    "Safety Group Footnote" text,
    "READM Group Measure Count" text,
    "Count of Facility READM Measures" text,
    "Count of READM Measures Better" text,
    "Count of READM Measures No Different" text,
    "Count of READM Measures Worse" text,
    "READM Group Footnote" text,
    "Pt Exp Group Measure Count" text,
    "Count of Facility Pt Exp Measures" text,
    "Pt Exp Group Footnote" text,
    "TE Group Measure Count" text,
    "Count of Facility TE Measures" text,
    "TE Group Footnote" text
);

-- Import HCAHPS-Hospital.csv
CREATE TABLE raw_cms.hcahps_hospital (
    "Facility ID" text,
    "Facility Name" text,
    "Address" text,
    "City/Town" text,
    "State" text,
    "ZIP Code" text,
    "County/Parish" text,
    "Telephone Number" text,
    "HCAHPS Measure ID" text,
    "HCAHPS Question" text,
    "HCAHPS Answer Description" text,
    "Patient Survey Star Rating" text,
    "Patient Survey Star Rating Footnote" text,
    "HCAHPS Answer Percent" text,
    "HCAHPS Answer Percent Footnote" text,
    "HCAHPS Linear Mean Value" text,
    "Number of Completed Surveys" text,
    "Number of Completed Surveys Footnote" text,
    "Survey Response Rate Percent" text,
    "Survey Response Rate Percent Footnote" text,
    "Start Date" text,
    "End Date" text
);

-- Import HCAHPS-State.csv
CREATE TABLE raw_cms.hcahps_state (
    "State" text,
    "HCAHPS Measure ID" text,
    "HCAHPS Question" text,
    "HCAHPS Answer Description" text,
    "HCAHPS Answer Percent" text,
    "Footnote" text,
    "Start Date" text,
    "End Date" text
);

COMMIT;
