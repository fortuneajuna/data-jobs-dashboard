-- =============================================================================
-- Data Jobs Platform — Analytics Queries
-- Target: DuckDB
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Top Paying Job Roles
-- ---------------------------------------------------------------------------
-- Which short job titles offer the highest average annual salary?
SELECT
    job_title_short,
    COUNT(*)              AS job_count,
    ROUND(AVG(salary_year_avg), 0) AS avg_salary,
    ROUND(MEDIAN(salary_year_avg), 0) AS median_salary
FROM jobs
WHERE salary_year_avg IS NOT NULL
GROUP BY job_title_short
ORDER BY avg_salary DESC;

-- ---------------------------------------------------------------------------
-- 2. Top Paying Countries
-- ---------------------------------------------------------------------------
-- Which countries have the highest average salaries?
SELECT
    job_country,
    COUNT(*)              AS job_count,
    ROUND(AVG(salary_year_avg), 0) AS avg_salary,
    ROUND(MEDIAN(salary_year_avg), 0) AS median_salary
FROM jobs
WHERE salary_year_avg IS NOT NULL
GROUP BY job_country
ORDER BY avg_salary DESC;

-- ---------------------------------------------------------------------------
-- 3. Most Demanded Skills
-- ---------------------------------------------------------------------------
-- Which skills appear most frequently across all job postings?
SELECT
    s.skill,
    COUNT(*)                     AS demand_count,
    COUNT(DISTINCT s.job_id)     AS unique_jobs
FROM skills s
GROUP BY s.skill
ORDER BY demand_count DESC
LIMIT 30;

-- ---------------------------------------------------------------------------
-- 4. Remote vs Onsite Salary Comparison
-- ---------------------------------------------------------------------------
-- Do remote jobs pay more or less than onsite roles?
SELECT
    CASE WHEN is_remote = 1 THEN 'Remote' ELSE 'Onsite' END AS work_type,
    COUNT(*)              AS job_count,
    ROUND(AVG(salary_year_avg), 0) AS avg_salary,
    ROUND(MEDIAN(salary_year_avg), 0) AS median_salary
FROM jobs
WHERE salary_year_avg IS NOT NULL
GROUP BY is_remote
ORDER BY avg_salary DESC;

-- ---------------------------------------------------------------------------
-- 5. Skill Salary Premium
-- ---------------------------------------------------------------------------
-- Salary uplift associated with each skill compared to overall average.
WITH overall_avg AS (
    SELECT AVG(salary_year_avg) AS overall FROM jobs WHERE salary_year_avg IS NOT NULL
)
SELECT
    s.skill,
    COUNT(*)                     as job_count,
    ROUND(AVG(j.salary_year_avg), 0) AS avg_salary_with_skill,
    ROUND((SELECT overall FROM overall_avg), 0) AS overall_avg_salary,
    ROUND(AVG(j.salary_year_avg) - (SELECT overall FROM overall_avg), 0) AS premium
FROM skills s
JOIN jobs j ON s.job_id = j.job_id
WHERE j.salary_year_avg IS NOT NULL
GROUP BY s.skill
HAVING COUNT(*) >= 3
ORDER BY premium DESC;

-- ---------------------------------------------------------------------------
-- 6. Top Paying Companies
-- ---------------------------------------------------------------------------
-- Which companies offer the highest average salaries?
SELECT
    company_name,
    COUNT(*)              AS job_count,
    ROUND(AVG(salary_year_avg), 0) AS avg_salary,
    ROUND(MEDIAN(salary_year_avg), 0) AS median_salary
FROM jobs
WHERE salary_year_avg IS NOT NULL
GROUP BY company_name
ORDER BY avg_salary DESC;

-- ---------------------------------------------------------------------------
-- 7. Role Rankings
-- ---------------------------------------------------------------------------
-- Rank individual job postings within each role by salary.
-- RANK() allows ties with gaps; DENSE_RANK() allows ties without gaps.
SELECT
    job_title_short,
    job_title,
    company_name,
    salary_year_avg,
    RANK()       OVER (PARTITION BY job_title_short ORDER BY salary_year_avg DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (PARTITION BY job_title_short ORDER BY salary_year_avg DESC) AS dense_rank
FROM jobs
WHERE salary_year_avg IS NOT NULL
ORDER BY job_title_short, rank_with_gaps;

-- ---------------------------------------------------------------------------
-- 8. Salary Trends Over Time
-- ---------------------------------------------------------------------------
-- Compare average salary month-over-month using LAG / LEAD.
WITH monthly_salaries AS (
    SELECT
        DATE_TRUNC('month', job_posted_date) AS month,
        ROUND(AVG(salary_year_avg), 0)       AS avg_salary,
        COUNT(*)                             AS job_count
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
    GROUP BY DATE_TRUNC('month', job_posted_date)
)
SELECT
    month,
    avg_salary,
    job_count,
    LAG(avg_salary)  OVER (ORDER BY month) AS prev_month_avg,
    LEAD(avg_salary) OVER (ORDER BY month) AS next_month_avg,
    ROUND(avg_salary - LAG(avg_salary) OVER (ORDER BY month), 0) AS mom_change
FROM monthly_salaries
ORDER BY month;
