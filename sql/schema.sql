CREATE TABLE IF NOT EXISTS jobs (
    job_id              BIGINT,
    job_title_short     VARCHAR,
    job_title           VARCHAR,
    job_location        VARCHAR,
    job_via             VARCHAR,
    job_schedule_type   VARCHAR,
    job_country         VARCHAR,
    company_name        VARCHAR,
    search_location     VARCHAR,
    salary_rate         VARCHAR,
    salary_year_avg     DOUBLE,
    salary_hour_avg     DOUBLE,
    salary_log          DOUBLE,
    is_remote           BOOLEAN,
    requires_degree     BOOLEAN,
    offers_health_insurance BOOLEAN,
    job_work_from_home  BOOLEAN,
    job_no_degree_mention BOOLEAN,
    job_health_insurance BOOLEAN,
    job_posted_date     TIMESTAMP WITH TIME ZONE,
    days_since_posted   INTEGER,
    skill_count         INTEGER,
    loaded_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    job_id  BIGINT,
    skill   VARCHAR
);
