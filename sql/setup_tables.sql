-- Spurious Bark — table setup
-- Run this in Snowflake (e.g. via a Snowsight worksheet or snowsql) before starting the app.

CREATE DATABASE IF NOT EXISTS SPURIOUS_BARK;
USE DATABASE SPURIOUS_BARK;

CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

-- Fixed time series: dog tax revenue per year
CREATE TABLE IF NOT EXISTS dog_tax_revenue (
    jahr        INTEGER NOT NULL,
    betrag_euro NUMBER(18, 2) NOT NULL,
    PRIMARY KEY (jahr)
);

-- Comparison time series (multiple series, distinguished by serie_name),
-- e.g. 'eheschliessungen' (marriages), 'fahrraddiebstaehle' (bicycle thefts),
-- 'lebendgeborene' (live births)
CREATE TABLE IF NOT EXISTS comparison_series (
    jahr       INTEGER NOT NULL,
    serie_name VARCHAR(100) NOT NULL,
    wert       NUMBER(18, 2) NOT NULL,
    PRIMARY KEY (jahr, serie_name)
);

-- Cortex COMPLETE doesn't need its own table — it's called directly via a
-- SQL query in app.py (SNOWFLAKE.CORTEX.COMPLETE(...)).
