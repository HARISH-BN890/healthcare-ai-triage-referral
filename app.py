import hashlib
import json
import math
from datetime import datetime, timezone

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

# ============================================================
# AAROGYA MARG — Rural Healthcare AI Assistant
# Educational prototype; not a clinically validated system.
# ============================================================

st.set_page_config(
    page_title="Rural Healthcare AI Assistant",
    page_icon="🏥",
    layout="wide",
)

APP_VERSION = "1.0.0"
DISCLAIMER = (
    "Educational prototype only. This is not a diagnosis or a validated "
    "medical decision system. Do not use it to delay emergency care. "
    "A qualified clinician must make clinical decisions."
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1450px; padding-top: 1.4rem; padding-bottom: 2rem;}
    .hero {padding: 24px 28px; border-radius: 18px; color: white;
           background: linear-gradient(115deg,#073b5c,#087f8c 72%,#11998e);
           margin-bottom: 15px;}
    .hero h1 {color:white !important; margin:0 0 7px 0;}
    .hero p {color:#e5f6f7 !important; margin:0;}
    .small-muted {color:#6b7280; font-size:.86rem;}
    div[data-testid="stMetric"] {border:1px solid #e0e7ed; padding:12px; border-radius:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🏥 Rural Healthcare AI Assistant</h1>
      <p>Aarogya Marg · Rural triage and referral support</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.info(DISCLAIMER)


# ----------------------------- Helpers -----------------------------

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def haversine_km(lat1, lon1, lat2, lon2):
    """Approximate straight-line distance, not road distance."""
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


def geocode_place(place):
    """Resolve a place name using OpenStreetMap Nominatim."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
        headers={"User-Agent": "RuralHealthcareAIAssistant-StudentProject/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    item = results[0]
    return {
        "name": item.get("display_name", place),
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
    }


def find_nearby_facilities(location, radius_km):
    """Find mapped healthcare facilities via OpenStreetMap Overpass."""
    radius_m = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"hospital|clinic|doctors|health_post"](around:{radius_m},{location['lat']},{location['lon']});
      way["amenity"~"hospital|clinic|doctors|health_post"](around:{radius_m},{location['lat']},{location['lon']});
      relation["amenity"~"hospital|clinic|doctors|health_post"](around:{radius_m},{location['lat']},{location['lon']});
    );
    out center tags;
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    last_error = None
    for endpoint in endpoints:
        try:
            response = requests.post(endpoint, data={"data": query}, timeout=35,
                                     headers={"User-Agent": "RuralHealthcareAIAssistant/1.0"})
            response.raise_for_status()
            elements = response.json().get("elements", [])
            facilities = []
            for element in elements:
                tags = element.get("tags", {})
                center = element.get("center", {})
                lat = element.get("lat", center.get("lat"))
                lon = element.get("lon", center.get("lon"))
                if lat is None or lon is None:
                    continue
                lat, lon = float(lat), float(lon)
                facilities.append({
                    "name": tags.get("name", tags.get("amenity", "Unnamed healthcare facility")),
                    "type": tags.get("amenity", "healthcare"),
                    "lat": lat,
                    "lon": lon,
                    "address": tags.get("addr:full", tags.get("addr:street", "Not listed")),
                    "phone": tags.get("phone", "Not listed"),
                    "distance_km": round(
                        haversine_km(location["lat"], location["lon"], lat, lon), 2
                    ),
                })
            facilities.sort(key=lambda f: f["distance_km"])
            return facilities, None
        except (requests.RequestException, ValueError, KeyError) as exc:
            last_error = str(exc)
    return [], last_error or "Facility service unavailable."


def get_driving_route(origin, destination):
    """Get an estimated driving route using the public OSRM demo service."""
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
    )
    try:
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson"},
            timeout=25,
            headers={"User-Agent": "RuralHealthcareAIAssistant/1.0"},
        )
        response.raise_for_status()
        routes = response.json().get("routes", [])
        if not routes:
            return None, "No road route was returned."
        route = routes[0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
            "coordinates": route["geometry"]["coordinates"],
        }, None
    except (requests.RequestException, ValueError, KeyError) as exc:
        return None, str(exc)


def create_facility_map(location, facilities, route=None):
    map_object = folium.Map(
        location=[location["lat"], location["lon"]],
        zoom_start=12,
        control_scale=True,
    )
    folium.Marker(
        [location["lat"], location["lon"]],
        tooltip="Search location",
        popup=location.get("name", "Search location"),
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(map_object)
    for facility in facilities:
        folium.Marker(
            [facility["lat"], facility["lon"]],
            tooltip=facility["name"],
            popup=(
                f"{facility['name']}<br>Type: {facility['type']}<br>"
                f"Straight-line distance: {facility['distance_km']} km"
            ),
            icon=folium.Icon(color="red", icon="plus-sign"),
        ).add_to(map_object)
    if route and route.get("coordinates"):
        points = [[lat, lon] for lon, lat in route["coordinates"]]
        folium.PolyLine(points, color="green", weight=5, opacity=0.8,
                        tooltip="Estimated driving route").add_to(map_object)
    return map_object


def default_patient():
    return {
        "age": 35,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "glucose": 100,
        "bmi": 23.0,
        "smoker": "No",
        "family_history": "No",
        "headache": "No",
        "thirst": "No",
        "tiredness": "No",
        "chest_discomfort": "No",
        "breathlessness": "No",
        "dizziness": "No",
        "symptoms": [],
        "history": "Not known",
    }


def risk_estimates(patient):
    """
    Arbitrary educational scores for UI demonstration only.
    These values are NOT clinical probabilities or validated predictions.
    """
    age = patient["age"]
    sbp = patient["systolic_bp"]
    dbp = patient["diastolic_bp"]
    glucose = patient["glucose"]
    bmi = patient["bmi"]

    hypertension = 0.10 + max(0, sbp - 110) * 0.006
    hypertension += max(0, dbp - 75) * 0.004
    hypertension += max(0, age - 35) * 0.002
    hypertension += 0.07 if patient["headache"] == "Yes" else 0
    hypertension += 0.04 if patient["smoker"] == "Yes" else 0

    diabetes = 0.08 + max(0, glucose - 90) * 0.006
    diabetes += max(0, bmi - 23) * 0.018
    diabetes += 0.13 if patient["thirst"] == "Yes" else 0
    diabetes += 0.12 if patient["tiredness"] == "Yes" else 0
    diabetes += 0.08 if patient["family_history"] == "Yes" else 0
    diabetes += 0.03 if age > 45 else 0

    heart = 0.04 + max(0, sbp - 120) * 0.004
    heart += max(0, age - 35) * 0.003
    heart += 0.22 if patient["chest_discomfort"] == "Yes" else 0
    heart += 0.20 if patient["breathlessness"] == "Yes" else 0
    heart += 0.08 if patient["smoker"] == "Yes" else 0
    heart += 0.07 if patient["family_history"] == "Yes" else 0

    return {
        "Hypertension score": max(0.0, min(0.99, hypertension)),
        "Diabetes score": max(0.0, min(0.99, diabetes)),
        "Heart-related score": max(0.0, min(0.99, heart)),
    }


def urgent_red_flags(patient):
    flags = []
    symptoms = patient.get("symptoms", [])
    chest = patient.get("chest_discomfort") == "Yes" or "Chest discomfort" in symptoms
    breathless = patient.get("breathlessness") == "Yes" or "Breathlessness" in symptoms
    dizzy = patient.get("dizziness") == "Yes" or "Dizziness" in symptoms
    if chest:
        flags.append("Chest discomfort")
    if breathless:
        flags.append("Breathlessness")
    if patient["systolic_bp"] >= 180 or patient["diastolic_bp"] >= 120:
        flags.append("Very high blood-pressure reading")
    if patient["glucose"] >= 300:
        flags.append("High entered glucose value")
    if dizzy and breathless:
        flags.append("Breathlessness together with dizziness")
    return flags


def display_patient_summary(patient):
    st.subheader("Saved Assessment")
    a, b, c = st.columns(3)
    a.metric("Age", f"{patient['age']} years")
    b.metric("Systolic BP", f"{patient['systolic_bp']} mmHg")
    c.metric("Blood glucose", f"{patient['glucose']} mg/dL")
    st.write("**Reported symptoms:**", ", ".join(patient.get("symptoms", [])) or "None selected")
    st.write("**Medical history:**", patient.get("history", "Not known"))


def export_patient_assessment(patient):
    payload = {
        "application": "Rural Healthcare AI Assistant / Aarogya Marg",
        "exported_at_utc": utc_now(),
        "educational_demo": True,
        "assessment": patient,
        "disclaimer": DISCLAIMER,
    }
    st.download_button(
        "Download assessment (JSON)",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="rural_healthcare_assessment.json",
        mime="application/json",
    )


def initialize_session():
    defaults = {
        "patient": None,
        "assessment_history": [],
        "decision_log": [],
        "location": None,
        "facilities": [],
        "selected_facility": None,
        "route": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# ----------------------------- Navigation -----------------------------

pages = [
    "Dashboard",
    "Patient Assessment",
    "What-if Analysis",
    "Nearby Healthcare",
    "Decision & Audit Log",
    "Model Evaluation",
    "Demo Scenarios",
    "About & Limitations",
]
with st.sidebar:
    st.title("🏥 Aarogya Marg")
    st.caption("Rural Healthcare AI Assistant")
    page = st.radio("Navigation", pages)
    st.divider()
    st.caption(f"Version {APP_VERSION}")
    st.caption("Educational prototype; no validated medical model.")


# ----------------------------- Dashboard -----------------------------

if page == "Dashboard":
    st.header("Rural Healthcare Dashboard")
    st.write(
        "Explore patient assessment, nearby mapped facilities, "
        "what-if analysis, and session audit tools."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Saved assessment", "Yes" if st.session_state["patient"] else "No")
    c2.metric("Mapped facilities", len(st.session_state["facilities"]))
    c3.metric("Audit entries", len(st.session_state["decision_log"]))
    st.info(
        "Start with Patient Assessment. Facility data depends on public "
        "OpenStreetMap services and may be incomplete or unavailable."
    )
    if st.session_state["patient"]:
        display_patient_summary(st.session_state["patient"])


# ----------------------------- Patient Assessment -----------------------------

elif page == "Patient Assessment":
    st.header("🩺 Patient Assessment")
    st.write("Use fictional/demo data only. This form does not diagnose illness.")

    with st.form("patient_assessment_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Age (years)", 1, 120, 35)
            systolic_bp = st.number_input("Systolic BP (mmHg)", 50, 300, 120)
            diastolic_bp = st.number_input("Diastolic BP (mmHg)", 20, 200, 80)
            glucose = st.number_input("Blood glucose (mg/dL)", 20, 600, 100)
            bmi = st.number_input("BMI (optional)", 10.0, 80.0, 23.0, 0.1)
        with c2:
            symptoms = st.multiselect(
                "Reported symptoms",
                [
                    "Chest discomfort",
                    "Breathlessness",
                    "Dizziness",
                    "Severe headache",
                    "Excessive thirst",
                    "Frequent urination",
                    "Fever",
                    "Unusual tiredness",
                ],
            )
            history = st.selectbox(
                "Relevant medical history",
                [
                    "Not known",
                    "Hypertension",
                    "Diabetes",
                    "Heart disease",
                    "Family history of heart disease",
                ],
            )
            smoker = st.selectbox("Smoking history", ["Not known", "No", "Yes"])
            family_history = st.selectbox("Family history of diabetes/heart disease", ["No", "Yes", "Not known"])
        submitted = st.form_submit_button("Save Assessment", type="primary")

    if submitted:
        patient = default_patient()
        patient.update({
            "age": int(age),
            "systolic_bp": int(systolic_bp),
            "diastolic_bp": int(diastolic_bp),
            "glucose": int(glucose),
            "bmi": float(bmi),
            "symptoms": list(symptoms),
            "history": history,
            "smoker": smoker,
            "family_history": "Yes" if family_history == "Yes" else "No",
            "headache": "Yes" if "Severe headache" in symptoms else "No",
            "thirst": "Yes" if ("Excessive thirst" in symptoms or "Frequent urination" in symptoms) else "No",
            "tiredness": "Yes" if "Unusual tiredness" in symptoms else "No",
            "chest_discomfort": "Yes" if "Chest discomfort" in symptoms else "No",
            "breathlessness": "Yes" if "Breathlessness" in symptoms else "No",
            "dizziness": "Yes" if "Dizziness" in symptoms else "No",
            "created_at_utc": utc_now(),
        })
        st.session_state["patient"] = patient
        st.session_state["assessment_history"].append({
            "time_utc": patient["created_at_utc"],
            "age": patient["age"],
            "systolic_bp": patient["systolic_bp"],
            "diastolic_bp": patient["diastolic_bp"],
            "glucose": patient["glucose"],
            "symptoms": ", ".join(patient["symptoms"]),
        })
        st.success("Assessment saved in this session.")

    patient = st.session_state["patient"]
    if patient:
        display_patient_summary(patient)
        export_patient_assessment(patient)

        flags = urgent_red_flags(patient)
        if flags:
            st.warning(
                "Safety prompt: " + ", ".join(flags) +
                ". Seek appropriate professional assessment. Severe or sudden "
                "symptoms may require emergency services. Do not wait for this app."
            )
        st.subheader("Illustrative scores (not medical probabilities)")
        scores = risk_estimates(patient)
        cols = st.columns(len(scores))
        for col, (name, score) in zip(cols, scores.items()):
            col.metric(name, f"{score * 100:.0f}/100")
        st.caption("Scores are arbitrary educational values and must not guide real patient care.")


# ----------------------------- What-if Analysis -----------------------------

elif page == "What-if Analysis":
    st.header("🔎 What-if Analysis")
    patient = st.session_state["patient"]
    if not patient:
        st.info("Save a demo assessment first in Patient Assessment.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            changed_sbp = st.slider("Hypothetical systolic BP", 50, 250, int(patient["systolic_bp"]))
        with col2:
            changed_glucose = st.slider("Hypothetical glucose (mg/dL)", 20, 600, int(patient["glucose"]))
        before, after = st.columns(2)
        before.metric("Saved systolic BP", f"{patient['systolic_bp']} mmHg")
        after.metric("Hypothetical systolic BP", f"{changed_sbp} mmHg", delta=changed_sbp - patient["systolic_bp"])
        before.metric("Saved glucose", f"{patient['glucose']} mg/dL")
        after.metric("Hypothetical glucose", f"{changed_glucose} mg/dL", delta=changed_glucose - patient["glucose"])
        if changed_sbp >= 180 or changed_glucose >= 300:
            st.warning("These hypothetical values trigger a demonstration safety prompt. Real measurements require professional interpretation.")
        else:
            st.info("No specific high-value prompt was triggered by these two values. This does not mean the person is healthy.")


# ----------------------------- Nearby Healthcare -----------------------------

elif page == "Nearby Healthcare":
    st.header("🗺️ Find Nearby Healthcare Facilities")
    st.write("Enter an Indian village, town, district, or area. Results depend on OpenStreetMap data.")

    with st.form("facility_search_form"):
        place = st.text_input("Village / town / district", placeholder="e.g., Pavagada, Karnataka")
        radius_km = st.select_slider("Search radius", options=[2, 5, 10, 15, 25, 50], value=10)
        search_clicked = st.form_submit_button("Find Facilities", type="primary")

    if search_clicked:
        if not place.strip():
            st.error("Enter a place name.")
        else:
            try:
                with st.spinner("Finding location..."):
                    location = geocode_place(place.strip())
                if not location:
                    st.warning("Location not found. Include the district and state.")
                else:
                    st.session_state["location"] = location
                    with st.spinner("Searching mapped healthcare facilities..."):
                        facilities, error = find_nearby_facilities(location, radius_km)
                    st.session_state["facilities"] = facilities
                    st.session_state["selected_facility"] = None
                    st.session_state["route"] = None
                    if error:
                        st.warning("The facility service may be busy. " + error[:300])
                    st.success(f"Found {len(facilities)} mapped facilities.")
            except requests.RequestException as exc:
                st.error("The location service is unavailable. Please retry later.")
                st.caption(str(exc))

    location = st.session_state["location"]
    facilities = st.session_state["facilities"]
    if location:
        st.write("**Search location:**", location["name"])
        if facilities:
            table = pd.DataFrame([
                {
                    "Facility": f["name"],
                    "Type": f["type"],
                    "Straight-line distance (km)": f["distance_km"],
                    "Address": f["address"],
                    "Phone": f["phone"],
                }
                for f in facilities
            ])
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.download_button(
                "Download facility list (CSV)",
                table.to_csv(index=False).encode("utf-8"),
                "aarogya_marg_facilities.csv",
                "text/csv",
            )
            fmap = create_facility_map(location, facilities, st.session_state["route"])
            st_folium(fmap, use_container_width=True, height=520, key="facility_map")
            labels = [
                f"{f['name']} — {f['distance_km']} km straight-line"
                for f in facilities
            ]
            selected_label = st.selectbox("Choose a facility for road-route estimate", labels)
            if st.button("Estimate Driving Route"):
                selected_index = labels.index(selected_label)
                selected = facilities[selected_index]
                st.session_state["selected_facility"] = selected
                route, route_error = get_driving_route(location, selected)
                st.session_state["route"] = route
                if route:
                    st.success(
                        f"Estimated road distance: {route['distance_km']} km · "
                        f"Estimated drive: {route['duration_min']} minutes"
                    )
                else:
                    st.warning("Road route unavailable: " + str(route_error))
        else:
            st.info("No mapped facilities currently available for this search. Try a larger radius or nearby town.")
    st.caption("Straight-line distance is not road distance. Confirm facility name, services, phone number and availability independently.")


# ----------------------------- Decision & Audit Log -----------------------------

elif page == "Decision & Audit Log":
    st.header("⚖️ Human Decision & Audit Log")
    patient = st.session_state["patient"]
    if not patient:
        st.info("Save an assessment first.")
    else:
        st.write("Record a human review decision for this educational demonstration.")
        decision = st.radio(
            "Decision",
            ["Request clinician review", "Reviewed; follow local protocol", "Other / override educational prompt"],
        )
        reason = st.text_area("Reason / notes (do not enter identifying patient details)")
        if st.button("Save decision", type="primary"):
            event = {
                "time_utc": utc_now(),
                "assessment_time_utc": patient.get("created_at_utc"),
                "decision": decision,
                "reason": reason.strip(),
            }
            previous_hash = st.session_state["decision_log"][-1]["hash"] if st.session_state["decision_log"] else "GENESIS"
            event["previous_hash"] = previous_hash
            event["hash"] = hashlib.sha256(
                json.dumps(event, sort_keys=True).encode("utf-8")
            ).hexdigest()
            st.session_state["decision_log"].append(event)
            st.success("Decision saved to the current session.")
    if st.session_state["decision_log"]:
        audit_df = pd.DataFrame(st.session_state["decision_log"])
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download audit log (CSV)",
            audit_df.to_csv(index=False).encode("utf-8"),
            "aarogya_marg_audit_log.csv",
            "text/csv",
        )
        st.caption("This session-only hash-linked log is not tamper-proof and is not a secure clinical record.")


# ----------------------------- Model Evaluation -----------------------------

elif page == "Model Evaluation":
    st.header("📊 Educational Model Evaluation")
    st.warning("This is a demonstration using synthetic labels and arbitrary scores, not a trained or clinically evaluated model.")
    n = st.slider("Number of synthetic examples", 50, 500, 150, 50)
    threshold = st.slider("Illustrative threshold", 0.1, 0.9, 0.5, 0.05)
    # Deterministic synthetic data for repeatable demonstration only.
    synthetic = pd.DataFrame({
        "score": [((i * 37) % 100) / 100 for i in range(n)],
        "label": [1 if ((i * 17) % 100) < 25 else 0 for i in range(n)],
    })
    synthetic["prediction"] = (synthetic["score"] >= threshold).astype(int)
    tp = int(((synthetic["prediction"] == 1) & (synthetic["label"] == 1)).sum())
    tn = int(((synthetic["prediction"] == 0) & (synthetic["label"] == 0)).sum())
    fp = int(((synthetic["prediction"] == 1) & (synthetic["label"] == 0)).sum())
    fn = int(((synthetic["prediction"] == 0) & (synthetic["label"] == 1)).sum())
    accuracy = (tp + tn) / n
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    brier = float(((synthetic["score"] - synthetic["label"]) ** 2).mean())
    a, b, c, d = st.columns(4)
    a.metric("Synthetic accuracy", f"{accuracy:.2%}")
    b.metric("Synthetic sensitivity", f"{sensitivity:.2%}")
    c.metric("Synthetic specificity", f"{specificity:.2%}")
    d.metric("Synthetic Brier score", f"{brier:.3f}")
    st.line_chart(synthetic.set_index("score")["label"].sort_index())
    st.caption("These metrics describe only the synthetic demonstration data; they say nothing about real-world medical performance.")


# ----------------------------- Demo Scenarios -----------------------------

elif page == "Demo Scenarios":
    st.header("🧪 Fictional Demo Scenarios")
    st.write("Load fictional examples to demonstrate the interface. Do not use these as real clinical guidance.")
    scenarios = {
        "Routine fictional example": {
            "age": 28, "systolic_bp": 115, "diastolic_bp": 75, "glucose": 95,
            "bmi": 22.0, "symptoms": [], "history": "Not known", "smoker": "No",
            "family_history": "No", "headache": "No", "thirst": "No", "tiredness": "No",
            "chest_discomfort": "No", "breathlessness": "No", "dizziness": "No",
        },
        "Fictional elevated readings": {
            "age": 52, "systolic_bp": 165, "diastolic_bp": 100, "glucose": 180,
            "bmi": 28.0, "symptoms": ["Unusual tiredness"], "history": "Hypertension",
            "smoker": "No", "family_history": "Yes", "headache": "Yes", "thirst": "Yes",
            "tiredness": "Yes", "chest_discomfort": "No", "breathlessness": "No", "dizziness": "No",
        },
        "Fictional urgent-symptom example": {
            "age": 60, "systolic_bp": 150, "diastolic_bp": 95, "glucose": 130,
            "bmi": 26.0, "symptoms": ["Chest discomfort", "Breathlessness"],
            "history": "Heart disease", "smoker": "No", "family_history": "Yes",
            "headache": "No", "thirst": "No", "tiredness": "No",
            "chest_discomfort": "Yes", "breathlessness": "Yes", "dizziness": "No",
        },
    }
    chosen = st.selectbox("Choose scenario", list(scenarios.keys()))
    if st.button("Load fictional scenario", type="primary"):
        patient = dict(scenarios[chosen])
        patient["created_at_utc"] = utc_now()
        st.session_state["patient"] = patient
        st.session_state["assessment_history"].append({
            "time_utc": patient["created_at_utc"],
            "age": patient["age"],
            "systolic_bp": patient["systolic_bp"],
            "diastolic_bp": patient["diastolic_bp"],
            "glucose": patient["glucose"],
            "symptoms": ", ".join(patient["symptoms"]),
            "scenario": chosen,
        })
        st.success("Fictional scenario loaded. Open Patient Assessment or Dashboard to review it.")
    if st.session_state["patient"]:
        display_patient_summary(st.session_state["patient"])


# ----------------------------- About & Limitations -----------------------------

elif page == "About & Limitations":
    st.header("ℹ️ About & Limitations")
    st.markdown(
        """
        **Project:** Rural Healthcare AI Assistant — Aarogya Marg

        **Purpose:** Educational demonstration of patient-information entry,
        safety prompts, nearby facility discovery, mapping, and human review logging.

        **Included features**
        - Patient assessment form and session history.
        - Clearly labelled arbitrary educational scores.
        - What-if exploration of entered values.
        - OpenStreetMap facility search and an optional OSRM driving route.
        - CSV and JSON downloads.
        - Session-only human decision log.
        - Synthetic-data evaluation demonstration and fictional scenarios.

        **Limitations**
        - No trained or clinically validated medical model is included.
        - Scores are arbitrary and are not clinical probabilities.
        - OpenStreetMap data may be incomplete or outdated.
        - Public geocoding, facility and routing services can fail or rate-limit requests.
        - Distances, estimated routes and travel times are approximate.
        - Session information can disappear when the session restarts.
        - Do not enter names, phone numbers, addresses or other identifiable patient data.
        - A qualified clinician must make clinical decisions.
        """
    )
    st.warning(DISCLAIMER)
    st.caption(f"Version {APP_VERSION} · Rendered at {utc_now()}")


# ----------------------------- Footer -----------------------------

st.divider()
st.caption(
    "Rural Healthcare AI Assistant | Aarogya Marg | GITAM University | "
    "Educational prototype — not for clinical use."
)
