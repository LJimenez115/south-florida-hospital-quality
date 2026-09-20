-- Import a single matching CMS release first. This leaves the raw tables unchanged.
BEGIN;
CREATE OR REPLACE FUNCTION hospital_analysis.cms_date(value text)
RETURNS date LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE parsed date;
BEGIN
 IF btrim(value) !~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}$' THEN RETURN NULL; END IF;
 parsed := to_date(btrim(value), 'MM/DD/YYYY');
 IF to_char(parsed, 'MM/DD/YYYY') <> btrim(value) THEN RETURN NULL; END IF;
 RETURN parsed;
EXCEPTION WHEN datetime_field_overflow OR invalid_datetime_format THEN RETURN NULL;
END;
$$;
CREATE OR REPLACE FUNCTION hospital_analysis.cms_percent(value text)
RETURNS numeric LANGUAGE sql IMMUTABLE AS $$
 SELECT CASE WHEN btrim(value) ~ '^[0-9]{1,3}([.][0-9]{1,3})?$'
             THEN CASE WHEN btrim(value)::numeric BETWEEN 0 AND 100
                       THEN btrim(value)::numeric END END;
$$;

-- Validate business keys before any joins can multiply rows.
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM raw_cms.hospital_general WHERE upper(btrim("State")) = 'FL')
 OR NOT EXISTS (SELECT 1 FROM raw_cms.hcahps_hospital WHERE upper(btrim("State")) = 'FL')
 OR NOT EXISTS (SELECT 1 FROM raw_cms.hcahps_state WHERE upper(btrim("State")) = 'FL') THEN
  RAISE EXCEPTION 'Import all three CSVs, including Florida rows, first.';
 END IF;
 IF EXISTS (SELECT 1 FROM raw_cms.hospital_general WHERE upper(btrim("State")) = 'FL'
            AND nullif(btrim("Facility ID"), '') IS NULL)
 OR EXISTS (SELECT 1 FROM raw_cms.hcahps_hospital WHERE upper(btrim("State")) = 'FL'
            AND (nullif(btrim("Facility ID"), '') IS NULL OR nullif(btrim("HCAHPS Measure ID"), '') IS NULL))
 OR EXISTS (SELECT 1 FROM raw_cms.hcahps_state WHERE upper(btrim("State")) = 'FL'
            AND nullif(btrim("HCAHPS Measure ID"), '') IS NULL) THEN
  RAISE EXCEPTION 'Missing facility or measure IDs; inspect the raw data.';
 END IF;
 IF EXISTS (SELECT 1 FROM raw_cms.hospital_general WHERE upper(btrim("State")) = 'FL'
            GROUP BY btrim("Facility ID") HAVING count(*) > 1)
 OR EXISTS (SELECT 1 FROM raw_cms.hcahps_hospital WHERE upper(btrim("State")) = 'FL'
            GROUP BY btrim("Facility ID"), replace(upper(btrim("HCAHPS Measure ID")), '-', '_'),
            hospital_analysis.cms_date("Start Date"), hospital_analysis.cms_date("End Date") HAVING count(*) > 1)
 OR EXISTS (SELECT 1 FROM raw_cms.hcahps_state WHERE upper(btrim("State")) = 'FL'
            GROUP BY replace(upper(btrim("HCAHPS Measure ID")), '-', '_'),
            hospital_analysis.cms_date("Start Date"), hospital_analysis.cms_date("End Date") HAVING count(*) > 1) THEN
  RAISE EXCEPTION 'Duplicate business keys. Check repeated imports or mixed releases.';
 END IF;
END;
$$;

CREATE OR REPLACE VIEW hospital_analysis.hospitals AS
SELECT btrim("Facility ID") AS facility_id, nullif(btrim("Facility Name"), '') AS facility_name,
 nullif(btrim("City/Town"), '') AS city, upper(btrim("State")) AS state,
 upper(btrim("County/Parish")) AS county, btrim("Hospital Type") AS hospital_type,
 btrim("Hospital Ownership") AS ownership,
 upper(btrim("County/Parish")) IN ('BROWARD', 'MIAMI-DADE', 'PALM BEACH') AS is_south_florida,
 CASE WHEN btrim("Hospital overall rating") ~ '^[1-5]$'
      THEN btrim("Hospital overall rating")::integer END AS overall_quality_stars,
 "Hospital overall rating" AS overall_quality_stars_raw,
 "Hospital overall rating footnote" AS overall_quality_footnote
FROM raw_cms.hospital_general WHERE upper(btrim("State")) = 'FL';

CREATE OR REPLACE VIEW hospital_analysis.hospital_measures AS
SELECT btrim("Facility ID") AS facility_id,
 replace(upper(btrim("HCAHPS Measure ID")), '-', '_') AS measure_id,
 btrim("HCAHPS Question") AS question, btrim("HCAHPS Answer Description") AS answer_description,
 hospital_analysis.cms_percent("HCAHPS Answer Percent") AS answer_percent,
 "HCAHPS Answer Percent" AS answer_percent_raw,
 "HCAHPS Answer Percent Footnote" AS answer_percent_footnote,
 CASE WHEN btrim("Patient Survey Star Rating") ~ '^[1-5]$'
      THEN btrim("Patient Survey Star Rating")::integer END AS patient_experience_stars,
 "Patient Survey Star Rating" AS patient_experience_stars_raw,
 "Patient Survey Star Rating Footnote" AS patient_experience_stars_footnote,
 "Number of Completed Surveys" AS completed_surveys_raw,
 "Number of Completed Surveys Footnote" AS completed_surveys_footnote,
 hospital_analysis.cms_percent("Survey Response Rate Percent") AS response_rate_percent,
 "Survey Response Rate Percent" AS response_rate_raw,
 "Survey Response Rate Percent Footnote" AS response_rate_footnote,
 hospital_analysis.cms_date("Start Date") AS period_start,
 hospital_analysis.cms_date("End Date") AS period_end
FROM raw_cms.hcahps_hospital WHERE upper(btrim("State")) = 'FL';

CREATE OR REPLACE VIEW hospital_analysis.florida_benchmarks AS
SELECT 'FL'::text AS state, replace(upper(btrim("HCAHPS Measure ID")), '-', '_') AS measure_id,
 btrim("HCAHPS Question") AS question,
 hospital_analysis.cms_percent("HCAHPS Answer Percent") AS answer_percent,
 "HCAHPS Answer Percent" AS answer_percent_raw, "Footnote" AS footnote,
 hospital_analysis.cms_date("Start Date") AS period_start,
 hospital_analysis.cms_date("End Date") AS period_end
FROM raw_cms.hcahps_state WHERE upper(btrim("State")) = 'FL';

DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM hospital_analysis.hospital_measures m
            LEFT JOIN hospital_analysis.hospitals h USING (facility_id) WHERE h.facility_id IS NULL) THEN
  RAISE EXCEPTION 'Survey facility missing from hospital file; check matching releases.';
 END IF;
 IF EXISTS (SELECT 1 FROM hospital_analysis.hospital_measures
            WHERE period_start IS NULL OR period_end IS NULL OR period_start > period_end)
 OR EXISTS (SELECT 1 FROM hospital_analysis.florida_benchmarks
            WHERE period_start IS NULL OR period_end IS NULL OR period_start > period_end) THEN
  RAISE EXCEPTION 'Invalid measurement dates. Inspect raw Start Date and End Date.';
 END IF;
 IF EXISTS (SELECT 1 FROM hospital_analysis.hospital_measures m
            LEFT JOIN hospital_analysis.florida_benchmarks b
             ON b.measure_id=m.measure_id AND b.period_start=m.period_start AND b.period_end=m.period_end
            WHERE m.measure_id IN ('H_COMP_1_A_P', 'H_COMP_2_A_P', 'H_RECMND_DY') AND b.measure_id IS NULL) THEN
  RAISE EXCEPTION 'Selected hospital measures lack a matching Florida period. Check releases.';
 END IF;
END;
$$;

CREATE OR REPLACE VIEW hospital_analysis.patient_experience_comparison AS
SELECT h.facility_id, h.facility_name, h.county, h.hospital_type, h.is_south_florida,
 m.measure_id, m.question, m.period_start, m.period_end,
 m.answer_percent AS hospital_percent, b.answer_percent AS florida_percent,
 m.answer_percent - b.answer_percent AS gap_percentage_points,
 m.completed_surveys_raw, m.answer_percent_footnote, b.footnote AS florida_footnote
FROM hospital_analysis.hospitals h
JOIN hospital_analysis.hospital_measures m USING (facility_id)
LEFT JOIN hospital_analysis.florida_benchmarks b
 ON b.state=h.state AND b.measure_id=m.measure_id AND b.period_start=m.period_start AND b.period_end=m.period_end
WHERE m.measure_id IN ('H_COMP_1_A_P', 'H_COMP_2_A_P', 'H_RECMND_DY');
COMMIT;
