-- Why: PostgreSQL is the portfolio database platform because it is production-ready
-- and Power BI provides a native connector for importing its relational tables.
DROP TABLE IF EXISTS fact_hcahps_rating CASCADE;
DROP TABLE IF EXISTS fact_hospital_quality CASCADE;
DROP TABLE IF EXISTS dim_survey_period CASCADE;
DROP TABLE IF EXISTS dim_hcahps_measure CASCADE;
DROP TABLE IF EXISTS dim_hospital CASCADE;
-- Why: These drops make a rebuild deterministic inside the dedicated project database;
-- the loader refuses to run if DATABASE_URL names a different database.

-- Why: Hospital attributes are stored once because one facility can have one CMS
-- quality snapshot and many HCAHPS measure ratings.
CREATE TABLE IF NOT EXISTS dim_hospital (
    hospital_key INTEGER PRIMARY KEY,
    facility_id TEXT NOT NULL UNIQUE,
    facility_name TEXT NOT NULL,
    county_name TEXT NOT NULL,
    city_name TEXT,
    state_code TEXT NOT NULL,
    zip_code TEXT,
    hospital_type TEXT,
    hospital_ownership TEXT,
    emergency_services TEXT,
    birthing_friendly_designation TEXT,
    benchmark_group TEXT NOT NULL
);
-- Why: This dimension provides the hospital filters used by both fact tables.

-- Why: HCAHPS measure identifiers and questions repeat across hospitals, so they
-- are modeled once and referenced from each patient-experience observation.
CREATE TABLE IF NOT EXISTS dim_hcahps_measure (
    hcahps_measure_key INTEGER PRIMARY KEY,
    hcahps_measure_id TEXT NOT NULL UNIQUE,
    hcahps_question TEXT NOT NULL
);
-- Why: This enables measure-level comparisons without duplicating long question text.

-- Why: Survey periods are shared metadata and ensure users do not accidentally
-- compare HCAHPS scores from different reporting windows as if they were identical.
CREATE TABLE IF NOT EXISTS dim_survey_period (
    survey_period_key INTEGER PRIMARY KEY,
    survey_start_date DATE NOT NULL,
    survey_end_date DATE NOT NULL,
    UNIQUE (survey_start_date, survey_end_date)
);
-- Why: This dimension preserves the period reported by CMS for each survey rating.

-- Why: This fact table stores one current CMS quality snapshot per hospital and
-- holds the numeric counts that contribute to dashboard quality comparisons.
CREATE TABLE IF NOT EXISTS fact_hospital_quality (
    hospital_quality_key INTEGER PRIMARY KEY,
    hospital_key INTEGER NOT NULL UNIQUE,
    overall_hospital_rating NUMERIC,
    mortality_measures_reported INTEGER,
    mortality_measures_better INTEGER,
    mortality_measures_worse INTEGER,
    safety_measures_reported INTEGER,
    safety_measures_better INTEGER,
    safety_measures_worse INTEGER,
    readmission_measures_reported INTEGER,
    readmission_measures_better INTEGER,
    readmission_measures_worse INTEGER,
    patient_experience_measures_reported INTEGER,
    timely_effective_measures_reported INTEGER,
    FOREIGN KEY (hospital_key) REFERENCES dim_hospital(hospital_key)
);
-- Why: The unique hospital key enforces the intended one-snapshot-per-hospital grain.

-- Why: This fact table stores one hospital, HCAHPS measure, and survey-period rating
-- per row, keeping patient experience distinct from the hospital-quality snapshot.
CREATE TABLE IF NOT EXISTS fact_hcahps_rating (
    hcahps_rating_key INTEGER PRIMARY KEY,
    hospital_key INTEGER NOT NULL,
    hcahps_measure_key INTEGER NOT NULL,
    survey_period_key INTEGER NOT NULL,
    patient_survey_star_rating NUMERIC,
    completed_survey_count INTEGER,
    survey_response_rate_percent NUMERIC,
    UNIQUE (hospital_key, hcahps_measure_key, survey_period_key),
    FOREIGN KEY (hospital_key) REFERENCES dim_hospital(hospital_key),
    FOREIGN KEY (hcahps_measure_key) REFERENCES dim_hcahps_measure(hcahps_measure_key),
    FOREIGN KEY (survey_period_key) REFERENCES dim_survey_period(survey_period_key)
);
-- Why: The composite uniqueness rule prevents duplicate ratings for the same facility,
-- measure, and reporting window while allowing later CMS periods to be appended.

-- Why: These indexes speed the dimensions and filters most likely to be selected in
-- Power BI, without changing the fact-table grain or duplicating data.
CREATE INDEX IF NOT EXISTS idx_hospital_county ON dim_hospital(county_name);
CREATE INDEX IF NOT EXISTS idx_hospital_benchmark ON dim_hospital(benchmark_group);
CREATE INDEX IF NOT EXISTS idx_quality_hospital ON fact_hospital_quality(hospital_key);
CREATE INDEX IF NOT EXISTS idx_hcahps_hospital ON fact_hcahps_rating(hospital_key);
CREATE INDEX IF NOT EXISTS idx_hcahps_measure ON fact_hcahps_rating(hcahps_measure_key);
-- Why: These indexes keep local-versus-state comparisons responsive as data grows.
