SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'onboarding_quest_db'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS onboarding_quest_db;

-- CREATE DATABASE onboarding_quest_db;