-- Run after cleaning and after every raw-data change.
SELECT 'raw_hospitals' AS dataset, count(*) AS rows FROM raw_cms.hospital_general
UNION ALL SELECT 'raw_hospital_surveys', count(*) FROM raw_cms.hcahps_hospital
UNION ALL SELECT 'raw_state_surveys', count(*) FROM raw_cms.hcahps_state
UNION ALL SELECT 'florida_hospitals', count(*) FROM hospital_analysis.hospitals
UNION ALL SELECT 'south_florida_hospitals', count(*) FROM hospital_analysis.hospitals WHERE is_south_florida;

-- Each duplicate query must return no rows.
SELECT facility_id, count(*) FROM hospital_analysis.hospitals GROUP BY 1 HAVING count(*) > 1;
SELECT facility_id, measure_id, period_start, period_end, count(*)
FROM hospital_analysis.hospital_measures GROUP BY 1, 2, 3, 4 HAVING count(*) > 1;
SELECT state, measure_id, period_start, period_end, count(*)
FROM hospital_analysis.florida_benchmarks GROUP BY 1, 2, 3, 4 HAVING count(*) > 1;

-- Missing/suppressed values are visible, with their original footnotes.
SELECT answer_percent_raw, answer_percent_footnote, count(*) AS rows
FROM hospital_analysis.hospital_measures WHERE answer_percent IS NULL
GROUP BY 1, 2 ORDER BY rows DESC;

-- Must be zero.
SELECT count(*) AS unmatched_facilities FROM hospital_analysis.hospital_measures m
LEFT JOIN hospital_analysis.hospitals h USING (facility_id) WHERE h.facility_id IS NULL;

SELECT measure_id, period_start, period_end, count(*) AS comparison_rows,
 count(hospital_percent) AS available_hospital_scores, count(florida_percent) AS available_florida_scores
FROM hospital_analysis.patient_experience_comparison
WHERE is_south_florida GROUP BY 1, 2, 3 ORDER BY 1, 2;

-- Must return no rows: verify that all three selected measures exist locally.
SELECT expected.measure_id AS missing_measure
FROM (VALUES ('H_COMP_1_A_P'), ('H_COMP_2_A_P'), ('H_RECMND_DY')) AS expected(measure_id)
WHERE NOT EXISTS (SELECT 1 FROM hospital_analysis.patient_experience_comparison actual
 WHERE actual.is_south_florida AND actual.measure_id = expected.measure_id);
