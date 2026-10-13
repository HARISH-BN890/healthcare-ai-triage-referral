
import streamlit as st

from bayesian_model import bayes_posterior, uncertainty_label
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
    "Educational demonstration only. Outputs are simulated, "
    "not clinical advice or a validated diagnostic tool. "
    "Do not use them to make real patient-care decisions."
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
    st.header("AI Module Integration")

    st.info(
        "The modules are imported below. Their outputs will only "
        "be displayed after their function interfaces and assumptions "
        "have been verified."
    )

    st.caption(
        "AI Healthcare Case Study | GITAM University"
    )
