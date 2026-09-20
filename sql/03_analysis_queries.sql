-- Run quality checks before using these results in Tableau.
-- Scope: acute care hospitals; local = Broward, Miami-Dade, Palm Beach.
SELECT CASE WHEN is_south_florida THEN 'South Florida' ELSE 'Rest of Florida' END AS region,
 overall_quality_stars, count(*) AS hospitals
FROM hospital_analysis.hospitals WHERE hospital_type = 'Acute Care Hospitals'
GROUP BY 1, 2 ORDER BY 1, 2 NULLS LAST;

SELECT facility_id, facility_name, county, overall_quality_stars, overall_quality_footnote
FROM hospital_analysis.hospitals
WHERE is_south_florida AND hospital_type = 'Acute Care Hospitals'
ORDER BY county, facility_name;

-- Higher is favorable for these three top-box percentage measures.
-- Hospital minus CMS-published state percentage is a gap in percentage points.
SELECT * FROM hospital_analysis.patient_experience_comparison
WHERE is_south_florida AND hospital_type = 'Acute Care Hospitals'
ORDER BY measure_id, gap_percentage_points DESC NULLS LAST;

-- Optional unweighted facility averages, NOT CMS-published state benchmarks.
-- Keep different survey measures AND periods separate.
SELECT m.measure_id, m.period_start, m.period_end,
 CASE WHEN h.is_south_florida THEN 'South Florida' ELSE 'Rest of Florida' END AS region,
 count(*) AS facility_measure_rows, count(m.patient_experience_stars) AS hospitals_with_stars,
 round(avg(m.patient_experience_stars), 2) AS unweighted_average_stars
FROM hospital_analysis.hospital_measures m
JOIN hospital_analysis.hospitals h USING (facility_id)
WHERE h.hospital_type = 'Acute Care Hospitals' AND m.measure_id LIKE '%_STAR_RATING'
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 4;
