import streamlit as st

st.set_page_config(
    page_title="NIAT Experiment Walkthrough",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 AI Parent Brief — Experiment Walkthrough")

st.warning(
    "Synthetic demonstration only. All participants, "
    "assignments and outcomes shown here are fictional. "
    "This page does not enroll or contact real NIAT leads."
)

st.markdown(
    "Explore how the proposed 14-day randomized pilot "
    "would give eligible, consenting participants "
    "different experiences."
)

with st.expander("Step 1 — Eligibility and consent", expanded=True):
    eligible = st.checkbox(
        "Fictional participant meets the pilot eligibility criteria",
        value=True,
    )
    consent = st.checkbox(
        "Fictional participant has consented to the experiment",
        value=True,
    )

if not eligible or not consent:
    st.error(
        "Participant cannot be assigned. Both eligibility "
        "and experiment consent are required."
    )
    st.stop()

st.success("Step 2 — Participant is eligible and consented.")

st.caption(
    "Choose a fictional assignment to inspect either journey. "
    "The actual experiment service performs randomized assignment; "
    "this walkthrough does not."
)

group = st.radio(
    "Step 3 — Demonstration assignment",
    ["Control", "Treatment"],
    horizontal=True,
)

st.subheader(f"Step 4 — {group} experience")

if group == "Control":
    st.info(
        "Existing follow-up experience only. "
        "No experimental AI Parent Decision Brief is provided."
    )
    st.markdown(
        "**Journey:** Existing information → "
        "Standard follow-up invitation → "
        "Optional next-step request."
    )
else:
    st.info(
        "Existing follow-up experience plus a "
        "personalized AI Parent Decision Brief."
    )
    st.markdown(
        "**Journey:** Existing information → "
        "AI Parent Decision Brief → "
        "Standard follow-up invitation → "
        "Optional next-step request."
    )
    st.markdown(
        "The live AI brief generator is available on "
        "the application's main page."
    )

st.subheader("Step 5 — Illustrative outcome tracking")

callback = st.checkbox(
    "Fictional participant requested a callback"
)

verified = st.checkbox(
    "Fictional reviewer verified next-step completion"
)

st.write({
    "participant_type": "synthetic",
    "group": group.lower(),
    "callback_requested": callback,
    "next_step_verified": verified,
})

st.caption(
    "These controls illustrate event states only. "
    "They do not write events to the experiment database. "
    "The primary metric is verified next-step completion "
    "within seven days of assignment."
)

st.divider()
st.markdown(
    "**Full synthetic 200-lead simulation:** "
    "Open `/experiment_demo` on this application."
)
