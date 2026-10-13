
import streamlit as st

from bayesian_model import calculate_probability, uncertainty_label
from decision_support import calculate_expected_utility, choose_best_action
from referral_routing import find_referral_route

st.set_page_config(
    page_title="Rural Healthcare AI",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Rural Healthcare AI Assistant")
st.subheader("Uncertainty-Aware Triage & Referral Support")

st.write(
    "An educational AI decision-support prototype "
    "for rural primary healthcare workers in India."
)

st.warning(
    "Educational demonstration only. Probabilities and utilities "
    "are illustrative, not clinically validated. Do not use this "
    "prototype to make real patient-care decisions."
)

st.divider()
st.header("Patient Assessment")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age (years)", 1, 120, 35)
    systolic_bp = st.number_input(
        "Systolic blood pressure (mmHg)", 50, 300, 120
    )
    blood_sugar = st.number_input(
        "Blood sugar (mg/dL)", 20, 600, 100
    )

with col2:
    symptoms = st.multiselect(
        "Reported symptoms",
        [
            "Chest discomfort",
            "Breathlessness",
            "Excessive thirst",
            "Frequent urination",
            "Dizziness"
        ]
    )
    history = st.selectbox(
        "Relevant medical history",
        [
            "Not known",
            "Hypertension",
            "Diabetes",
            "Heart disease",
            "Family history of heart disease"
        ]
    )

if st.button("Submit Assessment", type="primary"):
    st.session_state["assessment"] = {
        "age": age,
        "systolic_bp": systolic_bp,
        "blood_sugar": blood_sugar,
        "symptoms": symptoms,
        "history": history
    }

if "assessment" in st.session_state:
    patient = st.session_state["assessment"]

    st.divider()
    st.header("Assessment Summary")

    a, b, c = st.columns(3)
    a.metric("Age", f'{patient["age"]} years')
    b.metric("Systolic BP", f'{patient["systolic_bp"]} mmHg')
    c.metric("Blood sugar", f'{patient["blood_sugar"]} mg/dL')

    st.write(
        "**Symptoms:**",
        ", ".join(patient["symptoms"]) or "None selected"
    )
    st.write("**Medical history:**", patient["history"])

    st.divider()
    st.header("Illustrative AI Module Demonstrations")

    # Example probabilities are fixed for demonstration.
    # They are NOT derived from the patient's measurements.
    st.subheader("1. Bayesian probability")

    prior = 0.10
    sensitivity = 0.80
    specificity = 0.90

    posterior = calculate_probability(
        prior, sensitivity, specificity, positive=True
    )

    st.metric("Example posterior probability", f"{posterior:.2%}")
    st.write("Probability category:", uncertainty_label(posterior))
    st.caption(
        "This example uses assumed values; it does not estimate "
        "this patient's medical risk."
    )

    st.subheader("2. Expected utility")

    actions = {
        "Routine follow-up": [(0.8, 10), (0.2, -20)],
        "Clinical assessment": [(0.9, 8), (0.1, -5)],
        "Urgent clinical review": [(0.95, 6), (0.05, -2)]
    }

    best_action, scores = choose_best_action(actions)

    for action, score in scores.items():
        st.write(f"**{action}:** {score:.2f}")

    st.info(
        f"Highest-utility action in the hypothetical example: "
        f"{best_action}"
    )
    st.caption(
        "These hypothetical utilities are not medical recommendations."
    )

    st.subheader("3. Referral route demonstration")

    graph = {
        "Village Clinic": {
            "Community Health Centre": 3,
            "Town Hospital": 10
        },
        "Community Health Centre": {
            "Village Clinic": 3,
            "Town Hospital": 4
        },
        "Town Hospital": {
            "Village Clinic": 10,
            "Community Health Centre": 4
        }
    }

    path, cost = find_referral_route(
        graph, "Village Clinic", "Town Hospital"
    )

    if path:
        st.write("**Example route:**", " → ".join(path))
        st.write("**Simulated route cost:**", cost)
    else:
        st.write("No route available in the example graph.")

    st.caption(
        "The route uses a small, simulated graph and does not "
        "represent real hospitals, roads, or travel times."
    )

st.divider()
st.caption("AI Healthcare Case Study | GITAM University")
