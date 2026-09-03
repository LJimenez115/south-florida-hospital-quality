-- Why: This query compares the local hospital group with a non-overlapping Florida
-- benchmark, counting only hospitals with a published CMS overall rating.
SELECT
    h.benchmark_group,
    COUNT(*) AS hospital_count,
    COUNT(q.overall_hospital_rating) AS hospitals_with_rating,
    ROUND(AVG(q.overall_hospital_rating), 2) AS average_overall_rating
FROM dim_hospital AS h
JOIN fact_hospital_quality AS q ON h.hospital_key = q.hospital_key
GROUP BY h.benchmark_group
ORDER BY h.benchmark_group;
-- Why: This is the core benchmark result for a Power BI quality overview page.

-- Why: This query lists South Florida hospitals with published overall ratings and
-- their favorable/unfavorable measure counts for a hospital-level detail visual.
SELECT
    h.facility_name,
    h.county_name,
    q.overall_hospital_rating,
    q.safety_measures_better,
    q.safety_measures_worse,
    q.readmission_measures_better,
    q.readmission_measures_worse
FROM dim_hospital AS h
JOIN fact_hospital_quality AS q ON h.hospital_key = q.hospital_key
WHERE h.benchmark_group = 'South Florida'
ORDER BY q.overall_hospital_rating DESC, h.facility_name;
-- Why: Missing ratings remain null and therefore are visible rather than recoded as zero.

-- Why: This query compares standardized HCAHPS patient-experience star ratings by
-- measure, using only numeric CMS star values in the average calculation.
SELECT
    m.hcahps_question,
    h.benchmark_group,
    COUNT(r.patient_survey_star_rating) AS hospitals_with_star_rating,
    ROUND(AVG(r.patient_survey_star_rating), 2) AS average_star_rating
FROM fact_hcahps_rating AS r
JOIN dim_hospital AS h ON r.hospital_key = h.hospital_key
JOIN dim_hcahps_measure AS m ON r.hcahps_measure_key = m.hcahps_measure_key
GROUP BY m.hcahps_question, h.benchmark_group
ORDER BY m.hcahps_question, h.benchmark_group;
-- Why: The result drives a grouped bar chart without mixing HCAHPS measures together.
