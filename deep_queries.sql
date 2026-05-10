-- D1: Top 5 Inventors per Country
WITH ranked_inventors AS (
    SELECT
        i.full_name                                     AS inventor_name,
        l.country,
        COUNT(pi.patent_id)                             AS patent_count,
        RANK() OVER (
            PARTITION BY l.country
            ORDER BY COUNT(pi.patent_id) DESC
        )                                               AS country_rank
    FROM inventors i
    JOIN patent_inventor pi ON pi.inventor_id = i.inventor_id
    JOIN locations l        ON l.location_id  = i.location_id
    WHERE l.country IS NOT NULL
    GROUP BY i.full_name, l.country
)
SELECT country, country_rank, inventor_name, patent_count
FROM ranked_inventors
WHERE country_rank <= 5
ORDER BY country, country_rank;


-- D2: Patent Type Breakdown
SELECT
    pd.patent_type,
    COUNT(*)                                            AS patent_count,
    ROUND(COUNT(*) * 100.0 /
          SUM(COUNT(*)) OVER (), 2)                     AS pct_share
FROM patent_details pd
WHERE pd.patent_type IS NOT NULL
GROUP BY pd.patent_type
ORDER BY patent_count DESC;


-- D3: Tech Trends — patent type by year
SELECT
    EXTRACT(YEAR FROM pd.patent_date)::INT              AS year,
    pd.patent_type,
    COUNT(*)                                            AS patent_count
FROM patent_details pd
WHERE pd.patent_date IS NOT NULL
  AND pd.patent_type IS NOT NULL
GROUP BY year, pd.patent_type
ORDER BY year, patent_count DESC;


-- D4: Most Prolific Countries by Decade
WITH decade_country AS (
    SELECT
        l.country,
        (EXTRACT(YEAR FROM pd.patent_date)::INT / 10) * 10 AS decade,
        COUNT(DISTINCT pi.patent_id)                    AS patent_count
    FROM locations l
    JOIN inventors i        ON i.location_id  = l.location_id
    JOIN patent_inventor pi ON pi.inventor_id = i.inventor_id
    JOIN patent_details pd  ON pd.patent_id   = pi.patent_id
    WHERE l.country IS NOT NULL
      AND pd.patent_date IS NOT NULL
    GROUP BY l.country, decade
),
ranked AS (
    SELECT *,
           RANK() OVER (PARTITION BY decade ORDER BY patent_count DESC) AS rnk
    FROM decade_country
)
SELECT decade, rnk, country, patent_count
FROM ranked
WHERE rnk <= 5
ORDER BY decade, rnk;


-- D5: Top Companies by Patent Type
WITH comp_type AS (
    SELECT
        c.name                                          AS company_name,
        pd.patent_type,
        COUNT(*)                                        AS patent_count,
        RANK() OVER (
            PARTITION BY pd.patent_type
            ORDER BY COUNT(*) DESC
        )                                               AS type_rank
    FROM companies c
    JOIN patent_assignee pa ON pa.company_id = c.company_id
    JOIN patent_details pd  ON pd.patent_id  = pa.patent_id
    WHERE pd.patent_type IS NOT NULL
    GROUP BY c.name, pd.patent_type
)
SELECT patent_type, type_rank, company_name, patent_count
FROM comp_type
WHERE type_rank <= 5
ORDER BY patent_type, type_rank;


-- D6: Inventor Collaboration — patents with most inventors
SELECT
    pd.patent_id,
    pd.patent_title,
    pd.patent_type,
    pd.patent_date,
    COUNT(pi.inventor_id)                               AS inventor_count
FROM patent_details pd
JOIN patent_inventor pi ON pi.patent_id = pd.patent_id
GROUP BY pd.patent_id, pd.patent_title, pd.patent_type, pd.patent_date
ORDER BY inventor_count DESC
LIMIT 50;


-- D7: Average Claims by Patent Type
SELECT
    pd.patent_type,
    ROUND(AVG(pd.num_claims), 2)                        AS avg_claims,
    MAX(pd.num_claims)                                  AS max_claims,
    MIN(pd.num_claims)                                  AS min_claims,
    COUNT(*)                                            AS patent_count
FROM patent_details pd
WHERE pd.num_claims IS NOT NULL
  AND pd.patent_type IS NOT NULL
GROUP BY pd.patent_type
ORDER BY avg_claims DESC;


-- D8: Withdrawn Patents by Country
SELECT
    l.country,
    COUNT(*)                                            AS withdrawn_count
FROM patent_details pd
JOIN patent_inventor pi ON pi.patent_id  = pd.patent_id
JOIN inventors i        ON i.inventor_id = pi.inventor_id
JOIN locations l        ON l.location_id = i.location_id
WHERE pd.withdrawn = TRUE
  AND l.country IS NOT NULL
GROUP BY l.country
ORDER BY withdrawn_count DESC
LIMIT 20;