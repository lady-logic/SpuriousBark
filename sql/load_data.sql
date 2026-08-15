-- Spurious Bark — CSV import template
-- Adjust paths/stage names after you've dropped your CSVs into data/.
--
-- Expected CSV format:
--   dog_tax_revenue.csv        -> jahr,betrag_euro
--   comparison_series.csv      -> jahr,serie_name,wert
--
-- Option A: upload via Snowsight (Data > Add Data > Load into Table) — no SQL needed.
--
-- Option B: upload via SnowSQL / PUT + COPY INTO (example below).

USE DATABASE SPURIOUS_BARK;
USE SCHEMA PUBLIC;

-- 1) Create an internal stage (one-time)
CREATE STAGE IF NOT EXISTS spurious_bark_stage
    FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"');

-- 2) Upload local CSVs (run in the SnowSQL shell, adjust the path)
-- PUT file://data/dog_tax_revenue.csv @spurious_bark_stage AUTO_COMPRESS=TRUE;
-- PUT file://data/comparison_series.csv @spurious_bark_stage AUTO_COMPRESS=TRUE;

-- 3) Load the data into the tables
COPY INTO dog_tax_revenue (jahr, betrag_euro)
    FROM @spurious_bark_stage/dog_tax_revenue.csv.gz
    FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
    ON_ERROR = 'CONTINUE';

COPY INTO comparison_series (jahr, serie_name, wert)
    FROM @spurious_bark_stage/comparison_series.csv.gz
    FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
    ON_ERROR = 'CONTINUE';

-- 4) Sanity check
SELECT * FROM dog_tax_revenue ORDER BY jahr;
SELECT * FROM comparison_series ORDER BY serie_name, jahr;
