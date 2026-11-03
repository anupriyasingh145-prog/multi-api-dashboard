import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Multi-API Dashboard", layout="wide")
st.title("Multi-API Dashboard")
st.caption("Weather from Open-Meteo and repository stats from the GitHub API")

CITIES = {"Amsterdam": (52.37, 4.89), "Almere": (52.35, 5.26), "Utrecht": (52.09, 5.12)}


@st.cache_data(ttl=600)
def get_weather(lat, lon):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
        },
        timeout=10,
    )
    r.raise_for_status()
    return pd.DataFrame(r.json()["daily"])


@st.cache_data(ttl=600)
def get_repos(user):
    headers = {}
    token = os.getenv("GITHUB_TOKEN")  # optional, raises the rate limit
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(
        f"https://api.github.com/users/{user}/repos",
        headers=headers,
        params={"per_page": 100},
        timeout=10,
    )
    r.raise_for_status()
    return pd.DataFrame(r.json())


left, right = st.columns(2)

with left:
    st.subheader("7-day weather")
    city = st.selectbox("City", list(CITIES))
    try:
        weather = get_weather(*CITIES[city])
        st.line_chart(weather.set_index("time")[["temperature_2m_max", "temperature_2m_min"]])
        st.metric("Rain this week (mm)", round(weather["precipitation_sum"].sum(), 1))
    except requests.RequestException as e:
        st.error(f"Weather API failed: {e}")

with right:
    st.subheader("GitHub repositories")
    user = st.text_input("GitHub username", "anupriyasingh145-prog")
    try:
        repos = get_repos(user)
        if repos.empty:
            st.info("No public repositories found.")
        else:
            st.dataframe(repos[["name", "language", "stargazers_count", "updated_at"]])
            st.bar_chart(repos["language"].fillna("Unknown").value_counts())
    except requests.RequestException as e:
        st.error(f"GitHub API failed: {e}")