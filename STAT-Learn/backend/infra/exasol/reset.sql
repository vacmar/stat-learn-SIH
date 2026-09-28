-- reset.sql
-- Safely drop and recreate schema. Run this to clean the database before seeding.

DROP TABLE IF EXISTS lesson_sessions CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS project_evaluations CASCADE;
DROP TABLE IF EXISTS exercise_results CASCADE;
DROP TABLE IF EXISTS assessment_results CASCADE;
DROP TABLE IF EXISTS assessments CASCADE;
DROP TABLE IF EXISTS learning_progress CASCADE;
DROP TABLE IF EXISTS path_nodes CASCADE;
DROP TABLE IF EXISTS path_instances CASCADE;
DROP TABLE IF EXISTS evidence CASCADE;
DROP TABLE IF EXISTS learner_skills CASCADE;
DROP TABLE IF EXISTS project_skills CASCADE;
DROP TABLE IF EXISTS course_prerequisites CASCADE;
DROP TABLE IF EXISTS course_skills CASCADE;
DROP TABLE IF EXISTS role_skills CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS career_roles CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS learners CASCADE;

-- Optional: Run schema.sql after this script to recreate tables.
