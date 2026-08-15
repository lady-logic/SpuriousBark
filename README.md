# 🐕 Spurious Bark

> Dog tax meets statistics: two German government time series, one totally
> convincing, totally nonsense explanation.

A weekend hackathon project for the **DEV Weekend Challenge: Dog Days Edition**
(category: **Best use of Snowflake**).

## What is this?

**Spurious Bark** compares dog tax revenue collected by German municipalities
against a second time series picked from a dropdown (e.g. marriages, beer
production, live births). The app computes the statistical correlation between
the two series and asks **Snowflake Cortex** (`COMPLETE`) to make up a silly,
completely fake explanation for it — in the style of
[tylervigen.com/spurious-correlations](https://tylervigen.com/spurious-correlations).

Obviously the "explanation" is nonsense. Correlation is not causation —
that's the whole joke. 🐾

## Tech stack

- **Python + Streamlit** — runs locally (not Streamlit-in-Snowflake)
- **snowflake-connector-python** — connects to a Snowflake trial account
- **Snowflake tables**: `dog_tax_revenue` (jahr, betrag_euro), `comparison_series` (jahr, serie_name, wert)
- **SNOWFLAKE.CORTEX.COMPLETE()** — generates the fake explanation
- **Plotly** — dual-axis line chart
- Credentials loaded from `.env` (not committed)

## Project structure

```
SpuriousBark/
├── app.py                  # Streamlit app
├── sql/
│   ├── setup_tables.sql    # create the tables
│   └── load_data.sql       # CSV import template
├── data/                   # put your own CSVs here (not committed)
├── requirements.txt
├── .env.example             # placeholder credentials
├── .gitignore
└── README.md
```

## Setup

### 1. Prepare Snowflake

Run [`sql/setup_tables.sql`](sql/setup_tables.sql) in Snowsight (or SnowSQL)
to create the database, schema, and the two tables.

Then upload your CSV data (e.g. via the Snowsight upload UI, or using the
template in [`sql/load_data.sql`](sql/load_data.sql)). Expected format:

- `dog_tax_revenue.csv` → `jahr,betrag_euro`
- `comparison_series.csv` → `jahr,serie_name,wert` (with `serie_name` values
  like `eheschliessungen`, `bier`, `lebendgeborene`)

> ℹ️ `SNOWFLAKE.CORTEX.COMPLETE()` requires Cortex to be available in your
> Snowflake region/edition (e.g. AWS us-west-2; trial accounts usually work).

### 2. Python environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
copy .env.example .env
```

Fill in your Snowflake credentials in `.env` (account, user, password,
warehouse, database, schema, Cortex model).

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

Note: without a `.env` file, the app runs in **demo mode** with sample data,
so you can preview it before Snowflake is set up.

## How to use it

1. Pick the second time series in the sidebar (e.g. 💍 Marriages)
2. The line chart compares both time series across the years
3. The correlation coefficient is computed live with `CORR()` in Snowflake
4. Click "🐶 Woof! Generate explanation" → Snowflake Cortex delivers the
   fake explanation

## Screenshots / Demo

<!-- TODO: add a screenshot or GIF of the running app here -->

![Spurious Bark Screenshot](docs/screenshot-placeholder.png)

## Hackathon context

Built for the [DEV Weekend Challenge: Dog Days Edition](https://dev.to/challenges/weekend-2026-08-13)
(submission deadline: August 17, 2026, 06:59 UTC).

- **Prize category:** Best use of Snowflake
- **Theme:** build something for, about, or inspired by dogs 🐕

## License / data sources

Data sources are official German government statistics (e.g. Federal
Statistical Office / municipal statistics offices). Please add proper
attribution depending on the datasets you use.
