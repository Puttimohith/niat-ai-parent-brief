import os
from app.services.ai_service import generate_parent_brief
from app.services.brief_sharing_service import create_shared_brief
from app.services.brief_experiment_bridge import record_brief_experiment_event
from app.services.tracking_service import (
    save_lead,
    mark_brief_generated,
    mark_followup_requested,
)
import streamlit as st
from datetime import datetime, timezone

st.set_page_config(
    page_title="NIAT AI Parent Decision Brief",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 NIAT AI Parent Decision Brief")

st.caption(
    "Independent growth-hack prototype | "
    "Not an official NIAT application or admission portal"
)

st.info(
    "Get a personalised decision brief to understand "
    "NIAT upskilling, university admission, costs, "
    "and questions to discuss with a counsellor."
)

st.subheader("Student and Parent Information")

with st.form("parent_intake_form"):

    student_name = st.text_input(
        "Student Name",
        placeholder="Enter student name",
    )

    parent_name = st.text_input(
        "Parent / Guardian Name",
        placeholder="Enter parent name",
    )

    preferred_state = st.selectbox(
        "Preferred State",
        [
            "Andhra Pradesh",
            "Telangana",
            "Tamil Nadu",
            "Karnataka",
            "Maharashtra",
            "Other",
        ],
    )

    preferred_institution = st.text_input(
        "Preferred University / Institution",
        placeholder="Enter institution name, if known",
    )

    language = st.selectbox(
        "Preferred Language",
        ["English", "Telugu", "Hindi"],
    )

    budget = st.selectbox(
        "Annual Education Budget",
        [
            "Not decided",
            "Below ₹1 lakh",
            "₹1–2 lakhs",
            "₹2–3 lakhs",
            "Above ₹3 lakhs",
        ],
    )

    concerns = st.multiselect(
        "What are your main concerns?",
        [
            "Total education fees",
            "University admission process",
            "NIAT upskilling program",
            "Degree recognition",
            "Placements and career opportunities",
            "Hostel and transportation",
            "Scholarships and financial support",
        ],
    )

    additional_questions = st.text_area(
        "Additional Questions",
        placeholder="What would you like to clarify?",
    )

    consent = st.checkbox(
        "I agree to use the entered information "
        "to generate a demonstration decision brief."
    )

    sharing_consent = st.checkbox(
        "I separately agree to create a shareable "
        "decision brief link. Anyone with the link "
        "can read the shared brief for up to 7 days."
    )

    submitted = st.form_submit_button(
        "Continue to Decision Brief",
        type="primary",
    )

if submitted:
    if not student_name.strip():
        st.error("Please enter the student's name.")
    elif not parent_name.strip():
        st.error("Please enter the parent / guardian name.")
    elif not consent:
        st.error("Please provide consent to continue.")
    else:
        lead_data = {
            "student_name": student_name.strip(),
            "parent_name": parent_name.strip(),
            "preferred_state": preferred_state,
            "preferred_institution": preferred_institution.strip(),
            "language": language,
            "annual_budget": budget,
            "concerns": concerns,
            "additional_questions": additional_questions.strip(),
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # Clear the previous result before processing new input.
        st.session_state.pop("generated_brief", None)
        st.session_state.pop("lead_id", None)
        st.session_state.pop("share_token", None)

        try:
            record_type = os.getenv(
                "LEAD_RECORD_TYPE", "demo"
            ).strip().lower()

            if record_type not in ("demo", "real"):
                raise ValueError(
                    "Invalid LEAD_RECORD_TYPE configuration"
                )

            lead_id = save_lead(
                lead_data,
                record_type=record_type,
            )
            st.session_state["lead_id"] = lead_id
        except Exception:
            st.error("Unable to save your information. Please retry.")
            st.stop()

        st.success("Information captured successfully!")

        st.subheader("Your Submitted Preferences")
        st.json(lead_data)

        st.subheader("Your AI Parent Decision Brief")

        with st.spinner("Generating your personalised decision brief..."):
            try:
                brief = generate_parent_brief(lead_data)

                if not isinstance(brief, str) or not brief.strip():
                    raise ValueError("AI returned an empty decision brief.")

                mark_brief_generated(lead_id)
                st.session_state["generated_brief"] = brief

                if sharing_consent:
                    safe_preferences = {
                        "preferred_state": preferred_state,
                        "preferred_institution": preferred_institution.strip(),
                        "language": language,
                        "annual_budget": budget,
                        "concerns": concerns,
                        "additional_questions": "",
                    }

                    share_safe_brief = generate_parent_brief(
                        safe_preferences
                    )

                    if (
                        not isinstance(share_safe_brief, str)
                        or not share_safe_brief.strip()
                    ):
                        raise ValueError(
                            "Share-safe brief generation failed"
                        )

                    token = create_shared_brief(
                        lead_id,
                        share_safe_brief,
                        sharing_consent=True,
                    )

                    st.session_state["share_token"] = token

                    # Demo handoff event only. This does not
                    # prove external delivery to a recipient.
                    record_brief_experiment_event(
                        lead_id,
                        "brief_delivered",
                    )

            except Exception as exc:
                st.error(
                    "Unable to generate the decision brief. "
                    "Please try again."
                )
                st.caption(
                    f"Error type: {type(exc).__name__}"
                )

if (
    st.session_state.get("generated_brief")
    and st.session_state.get("lead_id")
):
    st.subheader("Your Generated Decision Brief")
    st.markdown(st.session_state["generated_brief"])

    if st.session_state.get("share_token"):
        st.divider()
        st.subheader("Shareable Decision Brief")

        token = st.session_state["share_token"]

        share_url = (
            "http://localhost:8501/shared_brief?token="
            + token
        )

        st.success("Shareable brief created.")

        st.code(share_url, language=None)

        st.caption(
            "This link works only while the local "
            "Streamlit server is running. "
            "Public deployment is not yet configured."
        )

    st.download_button(
        "Download Decision Brief",
        data=st.session_state["generated_brief"],
        file_name="NIAT_Parent_Decision_Brief.md",
        mime="text/markdown",
    )

    st.divider()
    st.subheader("Request a Follow-up")

    st.write(
        "Would you like to register your interest "
        "in speaking with an admissions counsellor?"
    )

    if st.session_state.get("followup_lead_id") == st.session_state["lead_id"]:
        st.success("Your follow-up interest has been recorded.")
    elif st.button(
        "Request Follow-up",
        type="primary",
        key="followup_button",
    ):
        try:
            mark_followup_requested(
                st.session_state["lead_id"]
            )
            st.session_state["followup_lead_id"] = (
                st.session_state["lead_id"]
            )
            st.success(
                "Your follow-up interest has been recorded "
                "in this demonstration system."
            )
            st.info(
                "This prototype does not automatically "
                "send your request to NIAT or a counsellor."
            )
        except Exception:
            st.error("Unable to record your request. Please retry.")
