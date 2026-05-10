CREATE TABLE IF NOT EXISTS locations (
    location_id  TEXT PRIMARY KEY,
    city         TEXT,
    state        TEXT,
    country      TEXT,
    county       TEXT
);

CREATE TABLE IF NOT EXISTS patents (
    patent_id  TEXT PRIMARY KEY,
    abstract   TEXT
);

CREATE TABLE IF NOT EXISTS patent_details (
    patent_id    TEXT PRIMARY KEY REFERENCES patents(patent_id),
    patent_type  TEXT,
    patent_date  DATE,
    patent_title TEXT,
    wipo_kind    TEXT,
    num_claims   INT,
    withdrawn    BOOLEAN,
    filename     TEXT
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id  TEXT PRIMARY KEY,
    name_first   TEXT,
    name_last    TEXT,
    full_name    TEXT,
    gender_code  TEXT,
    location_id  TEXT REFERENCES locations(location_id)
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT PRIMARY KEY,
    name         TEXT,
    type         TEXT,
    location_id  TEXT REFERENCES locations(location_id)
);

CREATE TABLE IF NOT EXISTS patent_inventor (
    patent_id    TEXT NOT NULL REFERENCES patents(patent_id),
    inventor_id  TEXT NOT NULL REFERENCES inventors(inventor_id),
    sequence     INT,
    PRIMARY KEY (patent_id, inventor_id)
);

CREATE TABLE IF NOT EXISTS patent_assignee (
    patent_id   TEXT NOT NULL REFERENCES patents(patent_id),
    company_id  TEXT NOT NULL REFERENCES companies(company_id),
    sequence    INT,
    PRIMARY KEY (patent_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_inventors_location ON inventors(location_id);
CREATE INDEX IF NOT EXISTS idx_companies_location ON companies(location_id);
CREATE INDEX IF NOT EXISTS idx_pi_inventor        ON patent_inventor(inventor_id);
CREATE INDEX IF NOT EXISTS idx_pi_patent          ON patent_inventor(patent_id);
CREATE INDEX IF NOT EXISTS idx_pa_company         ON patent_assignee(company_id);
CREATE INDEX IF NOT EXISTS idx_pa_patent          ON patent_assignee(patent_id);