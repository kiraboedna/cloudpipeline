-- =============================================================
-- queries.sql  —  Patent Intelligence SQL Queries (Q1–Q7)
-- =============================================================


-- Q1: Top Inventors — who has the most patents?
SELECT
    i.inventor_id,
    i.full_name                                          AS inventor_name,
    l.country,
    COUNT(pi.patent_id)                                  AS patent_count
FROM inventors         i
JOIN patent_inventor   pi  ON pi.inventor_id  = i.inventor_id
LEFT JOIN locations    l   ON l.location_id   = i.location_id
GROUP BY i.inventor_id, i.full_name, l.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q2: Top Companies — which companies own the most patents?
SELECT
    c.company_id,
    c.name                                               AS company_name,
    c.type,
    COUNT(pa.patent_id)                                  AS patent_count
FROM companies         c
JOIN patent_assignee   pa  ON pa.company_id   = c.company_id
GROUP BY c.company_id, c.name, c.type
ORDER BY patent_count DESC
LIMIT 20;


-- Q3: Countries — which countries produce the most patents?
SELECT
    l.country,
    COUNT(DISTINCT pi.patent_id)                         AS patent_count,
    ROUND(
        COUNT(DISTINCT pi.patent_id) * 100.0
        / NULLIF(SUM(COUNT(DISTINCT pi.patent_id)) OVER (), 0), 2
    )                                                    AS pct_share
FROM locations         l
JOIN inventors         i   ON i.location_id   = l.location_id
JOIN patent_inventor   pi  ON pi.inventor_id  = i.inventor_id
WHERE l.country IS NOT NULL
GROUP BY l.country
ORDER BY patent_count DESC
LIMIT 30;


-- Q4: Trends Over Time — patents per year
SELECT
    EXTRACT(YEAR FROM pd.patent_date)::INT          AS year,
    COUNT(*)                                         AS patents_filed,
    SUM(COUNT(*)) OVER (
        ORDER BY EXTRACT(YEAR FROM pd.patent_date)::INT
    )                                                AS cumulative_total
FROM patent_details pd
WHERE pd.patent_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM pd.patent_date)::INT
ORDER BY year;


-- Q5: JOIN Query — patents with inventors and companies
SELECT
    p.patent_id,
    LEFT(p.abstract, 120)                                AS abstract_preview,
    i.full_name                                          AS inventor_name,
    l_inv.country                                        AS inventor_country,
    c.name                                               AS company_name,
    l_co.country                                         AS company_country
FROM patents           p
JOIN patent_inventor   pi    ON pi.patent_id   = p.patent_id  AND pi.sequence = 1
JOIN inventors         i     ON i.inventor_id  = pi.inventor_id
LEFT JOIN locations    l_inv ON l_inv.location_id = i.location_id
LEFT JOIN patent_assignee pa ON pa.patent_id   = p.patent_id  AND pa.sequence = 1
LEFT JOIN companies    c     ON c.company_id   = pa.company_id
LEFT JOIN locations    l_co  ON l_co.location_id  = c.location_id
LIMIT 1000;


-- Q6: CTE Query — top 5 companies per country
WITH company_country AS (
    -- Step 1: count patents per company, join to country via location
    SELECT
        c.name                                           AS company_name,
        l.country,
        COUNT(pa.patent_id)                              AS patent_count
    FROM companies         c
    JOIN patent_assignee   pa  ON pa.company_id  = c.company_id
    LEFT JOIN locations    l   ON l.location_id  = c.location_id
    WHERE l.country IS NOT NULL
    GROUP BY c.name, l.country
),
ranked AS (
    -- Step 2: rank companies within each country
    SELECT *,
        RANK() OVER (PARTITION BY country ORDER BY patent_count DESC) AS rnk
    FROM company_country
)
-- Step 3: keep top 5 per country
SELECT country, rnk, company_name, patent_count
FROM ranked
WHERE rnk <= 5
ORDER BY country, rnk;


-- Q7: Ranking Query — rank inventors using window functions
SELECT
    i.full_name                                          AS inventor_name,
    l.country,
    COUNT(pi.patent_id)                                  AS patent_count,
    RANK() OVER (
        ORDER BY COUNT(pi.patent_id) DESC
    )                                                    AS global_rank,
    RANK() OVER (
        PARTITION BY l.country
        ORDER BY COUNT(pi.patent_id) DESC
    )                                                    AS country_rank,
    ROUND(
        COUNT(pi.patent_id) * 100.0
        / NULLIF(SUM(COUNT(pi.patent_id)) OVER (), 0), 4
    )                                                    AS pct_of_all_patents
FROM inventors         i
JOIN patent_inventor   pi  ON pi.inventor_id  = i.inventor_id
LEFT JOIN locations    l   ON l.location_id   = i.location_id
GROUP BY i.full_name, l.country
ORDER BY global_rank
LIMIT 100;
