-- Why: Run this once while connected to PostgreSQL's default `postgres` database
-- to create a dedicated project database that is separate from other local work.
CREATE DATABASE south_florida_hospital_quality;
-- Why: Database creation is separated from the loader because PostgreSQL does not
-- allow CREATE DATABASE inside the transactional data-load workflow.
