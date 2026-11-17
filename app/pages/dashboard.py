import pandas as pd
import streamlit as st

from app.services.tracking_service import get_dashboard_metrics

st.set_page_config(
    page_title="NIAT Growth Analytics",
    page_icon="📊",
    layout="wide",
)


# DASHBOARD_AUTH_V1
import os
import hmac
from dotenv import load_dotenv

load_dotenv()

dashboard_password = os.getenv("DASHBOARD_PASSWORD")

if not dashboard_password:
    st.error("Dashboard authentication is not configured.")
    st.stop()

if not st.session_state.get("dashboard_authenticated", False):
    st.title("🔐 Dashboard Login")

    with st.form("dashboard_login"):
        entered_password = st.text_input(
            "Dashboard Password",
            type="password",
        )
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if hmac.compare_digest(
            entered_password,
            dashboard_password,
        ):
            st.session_state["dashboard_authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid dashboard password.")

    st.stop()

if st.button("Logout"):
    st.session_state["dashboard_authenticated"] = False
    st.rerun()

st.title("📊 NIAT Growth Analytics Dashboard")

st.caption(
    "Independent prototype | Local demonstration analytics"
)

st.info(
    "Metrics represent events recorded by this prototype. "
    "They do not represent official NIAT admissions or sales."
)

if st.button("Refresh Analytics"):
    st.rerun()

st.subheader("Analytics Data Filter")

filter_label = st.radio(
    "Select Lead Category",
    ["Demo", "Real", "All"],
    horizontal=True,
    index=0,
    help="Demo records are test data. Real records are actual user submissions.",
)

record_type = filter_label.lower()

metrics = get_dashboard_metrics(record_type)

st.caption(
    f"Currently displaying: {filter_label} records"
)

st.subheader("Growth Funnel Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Leads", metrics["total_leads"])
col2.metric("AI Briefs Generated", metrics["briefs_generated"])
col3.metric("Follow-up Requests", metrics["followups"])

col4, col5 = st.columns(2)

col4.metric(
    "Brief Generation Rate",
    f'{metrics["brief_generation_rate"]}%',
)

col5.metric(
    "Follow-up Request Rate",
    f'{metrics["followup_rate"]}%',
)

st.divider()

st.subheader("Lead Conversion Funnel")

funnel = pd.DataFrame({
    "Stage": [
        "Submitted Leads",
        "Generated AI Briefs",
        "Follow-up Requests",
    ],
    "Count": [
        metrics["total_leads"],
        metrics["briefs_generated"],
        metrics["followups"],
    ],
})

if metrics["total_leads"] == 0:
    st.info(
        "No leads are available for the selected category. "
        "The conversion funnel will appear when records are added."
    )
else:
    st.bar_chart(
        funnel.set_index("Stage"),
        horizontal=True,
    )

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Language Preferences")

    if metrics["languages"]:
        df = pd.DataFrame(metrics["languages"])
        st.bar_chart(
            df.set_index("language")["count"]
        )
    else:
        st.info("No language preference data available.")

with right:
    st.subheader("Institution Interest")

    if metrics["institutions"]:
        df = pd.DataFrame(metrics["institutions"])
        st.bar_chart(
            df.set_index("preferred_institution")["count"],
            horizontal=True,
        )
    else:
        st.info("No institution interest data available.")

st.divider()

st.subheader("Growth Experiment Metrics")

st.write(
    "**Primary KPI:** Percentage of submitted leads "
    "that request a follow-up after receiving an AI brief."
)

st.write(
    "**Supporting KPI:** Percentage of submitted leads "
    "that successfully generate a personalized decision brief."
)

st.warning(
    "The current database may contain synthetic test events. "
    "Clear or isolate test records before reporting real results."
)
