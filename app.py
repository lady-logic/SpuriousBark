"""
Spurious Bark 🐾
Compares dog tax revenue against a second time series picked by the user,
then asks Snowflake Cortex to make up a silly "explanation" for the
(purely coincidental) correlation — in the spirit of tylervigen.com.
"""

import os
import random

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Runs in demo mode with sample data when no Snowflake credentials are set,
# so you can preview the app before Snowflake is configured.
DEMO_MODE = not os.environ.get("SNOWFLAKE_ACCOUNT")

if not DEMO_MODE:
    import snowflake.connector

st.set_page_config(
    page_title="Spurious Bark 🐶",
    page_icon="🐾",
    layout="wide",
)

# --------------------------------------------------------------------------
# Style: cheerful, colorful, dogs front and center
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #FFF6E9 0%, #FFE8D6 50%, #FFDDE0 100%);
    }
    h1, h2, h3 {
        color: #6B3F1D;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border-radius: 24px;
        box-shadow: 0 8px 24px rgba(107, 63, 29, 0.12);
        border: 3px dashed #F4A261 !important;
        margin-bottom: 1.5rem;
    }
    .bark-badge {
        display: inline-block;
        background: #F4A261;
        color: white;
        border-radius: 999px;
        padding: 0.2rem 0.9rem;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .paw-divider {
        text-align: center;
        font-size: 1.5rem;
        letter-spacing: 1rem;
        opacity: 0.6;
        margin: 0.5rem 0 1.5rem 0;
    }
    div.stButton > button {
        background: #E76F51;
        color: white;
        border-radius: 999px;
        border: none;
        padding: 0.6rem 1.6rem;
        font-weight: 700;
    }
    div.stButton > button:hover {
        background: #D9552F;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🐕 Spurious Bark")
st.markdown(
    "#### Dog tax meets statistics: two time series, one totally convincing, "
    "totally nonsense explanation 🐾"
)
st.markdown('<div class="paw-divider">🐾 🐾 🐾 🐾 🐾 🐾 🐾</div>', unsafe_allow_html=True)

COMPARISON_LABELS = {
    "eheschliessungen": "💍 Marriages",
    "lebendgeborene": "👶 Live births",
    "bier": "🍺 Beer production (hl)",
}

if DEMO_MODE:
    st.warning(
        "🐾 **Demo mode** — no `.env` with Snowflake credentials found. "
        "Showing sample data instead. Once you fill in `.env` (see "
        "`.env.example`), the app will connect to Snowflake automatically."
    )

# --------------------------------------------------------------------------
# Demo data (used as long as no Snowflake credentials are set in .env)
# --------------------------------------------------------------------------
_DEMO_YEARS = list(range(2016, 2026))


def _demo_dog_tax_df() -> pd.DataFrame:
    random.seed(42)
    values = [330_000_000 + i * 10_000_000 + random.randint(-3_000_000, 3_000_000) for i in range(len(_DEMO_YEARS))]
    return pd.DataFrame({"JAHR": _DEMO_YEARS, "BETRAG_EURO": values})


def _demo_comparison_df(serie_name: str) -> pd.DataFrame:
    random.seed(hash(serie_name) % 1000)
    base = {
        "eheschliessungen": 400_000,
        "lebendgeborene": 700_000,
        "bier": 75_000_000,
    }.get(serie_name, 100_000)
    values = [base - i * random.randint(int(base * 0.002), int(base * 0.01)) + random.randint(int(-base * 0.01), int(base * 0.01)) for i in range(len(_DEMO_YEARS))]
    return pd.DataFrame({"JAHR": _DEMO_YEARS, "WERT": values})


_DEMO_EXPLANATIONS = [
    "Simple: the more dogs a town has, the more excited everyone gets, and excited "
    "people apparently do more of everything else too — get married, lose their "
    "bikes, have kids, you name it. Dogs are basically little hype machines on "
    "leashes. (This is not real science. It's just a fun coincidence.) 🐕",
    "Here's the theory: happy dogs make happy owners, happy owners make happy "
    "neighbors, and happy neighborhoods just happen to see more of everything — "
    "weddings, bikes going missing, babies being born. It's the 'good vibes only' "
    "effect. (Totally made up. Correlation isn't causation.) 🐾",
]


# --------------------------------------------------------------------------
# Snowflake connection
# --------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "SPURIOUS_BARK"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
    )


@st.cache_data(ttl=600)
def load_dog_tax() -> pd.DataFrame:
    if DEMO_MODE:
        return _demo_dog_tax_df()
    conn = get_connection()
    return conn.cursor().execute(
        "SELECT jahr, betrag_euro FROM dog_tax_revenue ORDER BY jahr"
    ).fetch_pandas_all()


@st.cache_data(ttl=600)
def load_comparison_series_names() -> list:
    if DEMO_MODE:
        return list(COMPARISON_LABELS.keys())
    conn = get_connection()
    rows = conn.cursor().execute(
        "SELECT DISTINCT serie_name FROM comparison_series ORDER BY serie_name"
    ).fetchall()
    return [r[0] for r in rows]


@st.cache_data(ttl=600)
def load_comparison_series(serie_name: str) -> pd.DataFrame:
    if DEMO_MODE:
        return _demo_comparison_df(serie_name)
    conn = get_connection()
    return conn.cursor().execute(
        "SELECT jahr, wert FROM comparison_series WHERE serie_name = %s ORDER BY jahr",
        (serie_name,),
    ).fetch_pandas_all()


@st.cache_data(ttl=600)
def compute_correlation(serie_name: str) -> float:
    if DEMO_MODE:
        dog = _demo_dog_tax_df()["BETRAG_EURO"].to_numpy()
        comp = _demo_comparison_df(serie_name)["WERT"].to_numpy()
        return float(np.corrcoef(dog, comp)[0, 1])
    conn = get_connection()
    row = conn.cursor().execute(
        """
        SELECT CORR(d.BETRAG_EURO, c.WERT) AS korrelation
        FROM dog_tax_revenue d
        JOIN comparison_series c ON c.JAHR = d.JAHR
        WHERE c.SERIE_NAME = %s
        """,
        (serie_name,),
    ).fetchone()
    return float(row[0]) if row and row[0] is not None else float("nan")


def generate_explanation(serie_label: str, correlation: float) -> tuple[str, bool]:
    """Returns (explanation, used_cortex)."""
    if DEMO_MODE:
        return random.choice(_DEMO_EXPLANATIONS), False
    conn = get_connection()
    model = os.environ.get("CORTEX_MODEL", "mistral-large2")
    prompt = (
        "You write short, funny, totally made-up explanations for coincidental "
        "statistical correlations, in the style of tylervigen.com/spurious-correlations. "
        "Keep it simple and easy to read — plain everyday English, no jargon, no "
        "academic tone, max 3 short sentences. Explain in a light, silly way why "
        f"'dog tax revenue' and '{serie_label}' have a correlation coefficient of "
        f"{correlation:.3f}. End with a clear, friendly reminder that this is just "
        "a coincidence and correlation isn't causation."
    )
    escaped_prompt = prompt.replace("'", "''")
    try:
        row = conn.cursor().execute(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{escaped_prompt}')"
        ).fetchone()
        return (row[0] if row else "🐕 No explanation received."), True
    except Exception:
        return random.choice(_DEMO_EXPLANATIONS), False


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🐾 Controls")
    available = load_comparison_series_names()
    if not available:
        st.warning("No comparison series found in `comparison_series`.")
        st.stop()

    selected_series = st.selectbox(
        "Choose a comparison time series",
        options=available,
        format_func=lambda s: COMPARISON_LABELS.get(s, s),
    )
    st.caption("Fixed time series: 🐕 Dog tax revenue (Germany)")

dog_tax_df = load_dog_tax()
comparison_df = load_comparison_series(selected_series)
correlation = compute_correlation(selected_series)
series_label = COMPARISON_LABELS.get(selected_series, selected_series)

merged = pd.merge(
    dog_tax_df.rename(columns={"BETRAG_EURO": "Dog tax revenue (€)"}),
    comparison_df.rename(columns={"WERT": series_label}),
    on="JAHR",
    how="inner",
)

with st.container(border=True):
    st.markdown('<span class="bark-badge">📈 Time series comparison</span>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=merged["JAHR"],
                y=merged["Dog tax revenue (€)"],
                name="🐕 Dog tax revenue (€)",
                mode="lines+markers",
                line=dict(color="#E76F51", width=4),
                marker=dict(size=8),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=merged["JAHR"],
                y=merged[series_label],
                name=series_label,
                mode="lines+markers",
                yaxis="y2",
                line=dict(color="#2A9D8F", width=4, dash="dot"),
                marker=dict(size=8),
            )
        )
        fig.update_layout(
            xaxis=dict(title="Year"),
            yaxis=dict(title="🐕 Dog tax (€)", color="#E76F51"),
            yaxis2=dict(title=series_label, overlaying="y", side="right", color="#2A9D8F"),
            legend=dict(orientation="h", y=-0.2),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric(
            label="Correlation coefficient",
            value=f"{correlation:.3f}" if correlation == correlation else "n/a",
        )
        if correlation == correlation:
            if abs(correlation) > 0.8:
                st.markdown("🔥 **Suspiciously strong!**")
            elif abs(correlation) > 0.5:
                st.markdown("🐾 Somewhat strong.")
            else:
                st.markdown("🌱 Pretty weak.")
        st.caption("Computed with `CORR()` in Snowflake.")

with st.container(border=True):
    st.markdown('<span class="bark-badge">🧠 Snowflake Cortex explains</span>', unsafe_allow_html=True)
    st.markdown(f"##### Why do 🐕 dog tax and {series_label} correlate?")

    if st.button("🐶 Woof! Generate explanation"):
        if correlation != correlation:
            st.error("Correlation could not be computed — please check the data.")
        else:
            with st.spinner("Cortex is sniffing around the data... 🐾"):
                explanation, used_cortex = generate_explanation(series_label, correlation)
            st.info(explanation)
            if not used_cortex:
                st.caption(
                    "⚠️ Snowflake Cortex was unreachable, showing a canned example instead."
                )
            st.caption(
                "🐕‍🦺 Disclaimer: this explanation was generated by an AI in the style "
                "of 'Spurious Correlations'. Correlation ≠ causation — this is pure "
                "dog nonsense for fun."
            )

st.markdown('<div class="paw-divider">🐾 🐾 🐾 🐾 🐾 🐾 🐾</div>', unsafe_allow_html=True)
st.caption("Made with ❤️ and 🐾 for the DEV Weekend Challenge: Dog Days Edition")
