
import streamlit as st


st.set_page_config(
    page_title="NIAT Experiment Simulator",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Parent Decision Brief — Experiment Simulator")

st.warning(
    "Independent demonstration using fictional participants. "
    "No real NIAT leads, enrollment decisions, or conversion "
    "results are represented here."
)

st.write(
    "This simulation demonstrates the proposed 14-day, "
    "200-lead randomized pilot with a seven-day "
    "verified next-step completion metric."
)

st.info(
    "Control: existing follow-up without an AI brief. "
    "Treatment: existing follow-up plus an AI brief."
)

control_conversions = st.slider(
    "Synthetic control conversions",
    min_value=0,
    max_value=100,
    value=20,
)

treatment_conversions = st.slider(
    "Synthetic treatment conversions",
    min_value=0,
    max_value=100,
    value=28,
)

if st.button("Run 200-Lead Simulation", type="primary"):
    import json
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.run_experiment_simulation",
                str(control_conversions),
                str(treatment_conversions),
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=True,
        )

        st.session_state["simulation_metrics"] = json.loads(
            result.stdout
        )

    except Exception as exc:
        st.session_state.pop("simulation_metrics", None)
        st.error(
            "Simulation failed: "
            f"{type(exc).__name__}"
        )

metrics = st.session_state.get("simulation_metrics")

if metrics:
    control = metrics["control"]
    treatment = metrics["treatment"]

    st.subheader("Synthetic Experiment Results")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Control",
        f"{control['matured_conversion_rate']:.1f}%",
    )
    c2.metric(
        "Treatment",
        f"{treatment['matured_conversion_rate']:.1f}%",
    )
    c3.metric(
        "Difference",
        f"{metrics['matured_uplift_percentage_points']:+.1f} pp",
    )

    st.table({
        "Metric": [
            "Assigned participants",
            "Seven-day-matured participants",
            "Verified conversions",
            "Matured conversion rate",
        ],
        "Control": [
            control["assigned"],
            control["matured_leads"],
            control["verified_conversions"],
            f"{control['matured_conversion_rate']:.1f}%",
        ],
        "Treatment": [
            treatment["assigned"],
            treatment["matured_leads"],
            treatment["verified_conversions"],
            f"{treatment['matured_conversion_rate']:.1f}%",
        ],
    })

    st.caption(
        "Synthetic outcomes were selected using the sliders. "
        "The seven-day evaluation clock was advanced for "
        "demonstration purposes. These are not observed "
        "conversion results."
    )

st.divider()

st.subheader("Experiment Design")

st.markdown("""
**Hypothesis:** Increase verified seven-day next-step completion
from an illustrative 20% baseline to 28%.

**Enrollment:** 200 eligible, consented leads.

**Allocation:** 100 control and 100 treatment participants.

**Enrollment period:** 14 days.

**Primary metric:** Verified next-step completion within
seven days of assignment.

**Limitation:** A 100-per-group pilot provides directional
evidence and does not guarantee statistical significance.
""")
