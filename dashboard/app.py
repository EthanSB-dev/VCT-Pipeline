"""
VCT Pipeline analytics dashboard.

Reads directly from the dbt-built `analytics.*` marts (dim_teams,
dim_tournaments, fct_matches) — no new transformation logic lives here.
This file is intentionally "dumb": it queries what the pipeline already
produced and renders it. If a number here looks wrong, the bug is in
the pipeline, not the dashboard.
"""
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

st.set_page_config(page_title="VCT Match Analytics", layout="wide")


@st.cache_resource
def get_engine():
    """
    Builds a SQLAlchemy engine from the same environment variables the
    rest of the pipeline (load_matches.py, dbt profiles.yml) already uses,
    so this dashboard can run with the exact same .env file — no separate
    config to keep in sync. @st.cache_resource means this connection pool
    is built once per app run, not re-created on every user interaction.
    """
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", 5432)
    dbname = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


@st.cache_data(ttl=300)
def load_teams() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text("select * from analytics.dim_teams"), conn)


@st.cache_data(ttl=300)
def load_tournaments() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            text(
                """
                select tournament_name, league_name, serie_full_name, serie_year,
                       matches_played, earliest_match_at, latest_match_at
                from analytics.dim_tournaments
                order by latest_match_at desc
                """
            ),
            conn,
        )


@st.cache_data(ttl=300)
def load_recent_matches(limit: int = 25) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            text(
                """
                select end_at, tournament_id, league_name,
                       team_a_name, team_a_score, team_b_name, team_b_score,
                       winner_name, duration_minutes
                from analytics.fct_matches
                where match_status = 'finished'
                order by end_at desc
                limit :limit
                """
            ),
            conn,
            params={"limit": limit},
        )


st.title("VCT Match Analytics")
st.caption("Live view of analytics.* marts, built by the extract → load → dbt pipeline.")

teams_df = load_teams()
tournaments_df = load_tournaments()
recent_df = load_recent_matches()

# --- KPI row -----------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Teams tracked", len(teams_df))
col2.metric("Tournaments tracked", len(tournaments_df))
col3.metric("Finished matches (recent view)", len(recent_df))

st.divider()

# --- Team win rates ------------------------------------------------------
st.subheader("Team win rates")
min_matches = st.slider(
    "Minimum matches played (filters out small sample sizes)",
    min_value=1,
    max_value=int(teams_df["matches_played"].max()) if not teams_df.empty else 1,
    value=1,
)
filtered_teams = teams_df[teams_df["matches_played"] >= min_matches].sort_values(
    "win_rate_pct", ascending=False
)

if filtered_teams.empty:
    st.info("No teams meet that match-count threshold yet.")
else:
    fig = px.bar(
        filtered_teams,
        x="team_name",
        y="win_rate_pct",
        hover_data=["matches_played", "matches_won"],
        labels={"team_name": "Team", "win_rate_pct": "Win rate (%)"},
    )
    st.plotly_chart(fig, width="stretch")

st.divider()

# --- Tournaments ---------------------------------------------------------
st.subheader("Tournaments")
st.dataframe(tournaments_df, width="stretch", hide_index=True)

st.divider()

# --- Recent matches --------------------------------------------------------
st.subheader("Recent finished matches")
st.dataframe(recent_df, width="stretch", hide_index=True)