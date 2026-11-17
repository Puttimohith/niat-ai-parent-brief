import streamlit as st

from app.services.brief_sharing_service import (
    get_shared_brief,
)

from app.services.brief_experiment_bridge import (
    record_brief_experiment_event,
)

st.set_page_config(
    page_title="Shared Parent Decision Brief",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Shared Parent Decision Brief")

st.caption(
    "Independent educational decision-support prototype. "
    "Not an official NIAT admission document."
)

token = st.query_params.get("token", "")

if not isinstance(token, str) or not token:
    st.info(
        "This page requires a valid sharing link."
    )
    st.stop()

# Streamlit reruns frequently. Count a view only once
# per browser session and token.
view_key = f"shared_brief_viewed_{token}"

try:
    brief = get_shared_brief(
        token,
        count_view=not st.session_state.get(
            view_key, False
        ),
    )
except Exception:
    st.error(
        "Unable to load this decision brief. "
        "Please try again later."
    )
    st.stop()

if brief is None:
    st.warning(
        "This sharing link is invalid, expired, "
        "or has been revoked."
    )
    st.stop()

if not st.session_state.get(view_key, False):
    record_brief_experiment_event(
        brief["lead_id"],
        "brief_viewed",
    )

st.session_state[view_key] = True

st.success("Decision brief loaded successfully.")

st.divider()

st.markdown(brief["brief_content"])

st.divider()

st.download_button(
    "Download Decision Brief",
    data=brief["brief_content"],
    file_name="Shared_Parent_Decision_Brief.md",
    mime="text/markdown",
)

st.caption(
    "This link provides access to the brief only. "
    "Do not forward it without the family's permission."
)
