import json
from pathlib import Path

KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "niat_knowledge.json"
)


def load_knowledge():
    """Load verified NIAT knowledge from the local JSON file."""
    with KNOWLEDGE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_relevant_knowledge(lead_data):
    """Return the knowledge relevant to a parent's preferences."""
    knowledge = load_knowledge()

    preferred_state = lead_data.get("preferred_state", "")
    preferred_institution = lead_data.get(
        "preferred_institution", ""
    ).strip().lower()

    matching_institutions = []

    for institution in knowledge.get("institutions", []):
        name = institution["name"].lower()
        location = institution["location"].lower()

        if (
            preferred_institution
            and preferred_institution in name
        ) or (
            not preferred_institution
            and preferred_state.lower() in location
        ):
            matching_institutions.append(institution)

    return {
        "program": knowledge["program"],
        "nat": knowledge["nat"],
        "eligibility": knowledge["eligibility"],
        "matching_institutions": matching_institutions,
        "unverified_information": knowledge[
            "unverified_information"
        ],
        "source": knowledge["source"],
    }
