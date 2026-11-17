import hmac
import os

import streamlit as st

from app.services.experiment_metrics_service import (
    get_experiment_metrics,
)
from app.services.experiment_service import (
    create_experiment,
    get_experiment_counts,
)
from app.services.experiment_schedule_service import (
    get_experiment_status,
)

st.set_page_config(
    page_title="NIAT Experiment Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 AI Parent Decision Brief — Experiment")

st.caption(
    "Independent demonstration dashboard. "
    "Not official NIAT experiment results."
)

password = os.getenv("DASHBOARD_PASSWORD", "")

if not password:
    st.error("Dashboard password is not configured.")
    st.stop()

if not st.session_state.get("experiment_authenticated", False):
    entered = st.text_input(
        "Dashboard Password",
        type="password",
    )

    if st.button("Sign In"):
        if hmac.compare_digest(entered, password):
            st.session_state["experiment_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()

if st.button("Log Out"):
    st.session_state["experiment_authenticated"] = False
    st.rerun()

st.divider()

record_type = st.selectbox(
    "Data Classification",
    ["demo", "real"],
    format_func=lambda value: (
        "Demo / Synthetic Data"
        if value == "demo"
        else "Real Data"
    ),
)

try:
    # Ensure a fresh deployment has the experiment definition.
    # This does not start the experiment or create assignments.
    create_experiment()

    status = get_experiment_status()
    counts = get_experiment_counts(
        record_type=record_type,
    )
    metrics = get_experiment_metrics(
        record_type=record_type,
    )
except Exception as exc:
    st.error(
        "Unable to load experiment dashboard. "
        f"Error: {type(exc).__name__}"
    )
    st.stop()

st.subheader("Experiment Overview")

st.write(f"**Experiment status:** {status.replace('_', ' ').title()}")

control = metrics["control"]
treatment = metrics["treatment"]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Control Leads",
    counts["control"],
)

col2.metric(
    "Treatment Leads",
    counts["treatment"],
)

col3.metric(
    "Total Enrolled",
    counts["control"] + counts["treatment"],
)

st.divider()

st.subheader("Seven-Day Verified Next-Step Completion")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Control Conversion",
    f"{control['conversion_rate']:.2f}%",
)

col2.metric(
    "Treatment Conversion",
    f"{treatment['conversion_rate']:.2f}%",
)

col3.metric(
    "Observed Difference",
    f"{metrics['uplift_percentage_points']:+.2f} pp",
)

st.table({
    "Metric": [
        "Assigned Leads",
        "Verified Conversions",
        "Conversion Rate",
        "Seven-Day-Matured Leads",
        "Matured Conversion Rate",
    ],
    "Control": [
        control["assigned"],
        control["verified_conversions"],
        f"{control['conversion_rate']:.2f}%",
        control["matured_leads"],
        f"{control['matured_conversion_rate']:.2f}%",
    ],
    "Treatment": [
        treatment["assigned"],
        treatment["verified_conversions"],
        f"{treatment['conversion_rate']:.2f}%",
        treatment["matured_leads"],
        f"{treatment['matured_conversion_rate']:.2f}%",
    ],
})

st.divider()

st.subheader("Experiment Hypothesis")

st.write(
    "Illustrative baseline: **20%**. "
    "Target: **28%**. "
    "Required improvement: **+8 percentage points**."
)

st.info(
    "These figures are a proposed experiment hypothesis, "
    "not historical NIAT performance."
)

if record_type == "demo":
    st.warning(
        "Demo data must not be presented as real "
        "experiment performance."
    )

if control["matured_leads"] == 0 or treatment["matured_leads"] == 0:
    st.info(
        "Final seven-day conversion comparison is not yet "
        "available because one or both groups have no "
        "fully matured participants."
    )
else:
    st.metric(
        "Matured Cohort Difference",
        f"{metrics['matured_uplift_percentage_points']:+.2f} pp",
    )

st.caption(
    "A 100-per-group pilot is directional and does not "
    "establish statistical significance on its own. "
    "Reviewer authentication and independent verification "
    "are not yet implemented."
)
