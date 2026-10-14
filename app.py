import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium

from bayesian_model import calculate_probability, uncertainty_label
from decision_support import calculate_expected_utility, choose_best_action

st.set_page_config(
    page_title="Rural Healthcare AI",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    max-width: 1250px;
}
.hero {
    padding: 25px;
    border-radius: 15px;
    background: linear-gradient(120deg, #075985, #0f766e);
    color: white;
    margin-bottom: 20px;
}
.hero h1, .hero p { color: white; }
.card {
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #dbe3ea;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏥 Rural Healthcare AI Assistant</h1>
    <p>Uncertainty-aware triage support and healthcare facility discovery across India</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "👤 Patient Assessment",
    "📍 Find Healthcare",
    "🗺️ Referral Route"
])

# ---------------- PATIENT ASSESSMENT ----------------
with tab1:
    st.header("Patient Assessment")
    st.write("Enter the available patient information.")

    c1, c2 = st.columns(2)

    with c1:
        age = st.number_input("Age (years)", 1, 120, 35)
        systolic_bp = st.number_input(
            "Systolic blood pressure (mmHg)", 50, 300, 120
        )
        blood_sugar = st.number_input(
            "Blood sugar (mg/dL)", 20, 600, 100
        )

    with c2:
        symptoms = st.multiselect(
            "Symptoms",
            [
                "Chest discomfort",
                "Breathlessness",
                "Excessive thirst",
                "Frequent urination",
                "Dizziness",
                "Fever",
                "Severe headache"
            ]
        )

        history = st.selectbox(
            "Medical history",
            [
                "Not known",
                "Hypertension",
                "Diabetes",
                "Heart disease",
                "Family history of heart disease"
            ]
        )

    st.info(
        "For severe symptoms, seek urgent professional medical assessment. "
        "This application cannot determine whether a patient is safe."
    )

    if st.button("Save Patient Assessment", type="primary"):
        st.session_state["patient"] = {
            "age": age,
            "systolic_bp": systolic_bp,
            "blood_sugar": blood_sugar,
            "symptoms": symptoms,
            "history": history
        }
        st.success("Assessment information saved for this session.")

    if "patient" in st.session_state:
        p = st.session_state["patient"]

        st.subheader("Assessment Summary")
        a, b, c = st.columns(3)
        a.metric("Age", f'{p["age"]} years')
        b.metric("Systolic BP", f'{p["systolic_bp"]} mmHg')
        c.metric("Blood sugar", f'{p["blood_sugar"]} mg/dL')

        st.write("**Symptoms:**", ", ".join(p["symptoms"]) or "None selected")
        st.write("**Medical history:**", p["history"])

        st.caption(
            "Patient data is held in the current application session. "
            "This prototype is not a validated diagnostic system."
        )

# ---------------- LOCATION SEARCH ----------------
with tab2:
    st.header("Find Healthcare Facilities Across India")
    st.write("Search using a village, town, district, PIN code, or address.")

    place = st.text_input(
        "Enter location",
        placeholder="Example: Pavagada, Karnataka"
    )

    radius = st.select_slider(
        "Search radius",
        options=[2, 5, 10, 15, 25],
        value=5,
        format_func=lambda x: f"{x} km"
    )

    if st.button("Search Location and Facilities", type="primary"):
        if not place.strip():
            st.warning("Please enter a location.")
        else:
            with st.spinner("Searching for the location..."):
                try:
                    response = requests.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={
                            "q": place + ", India",
                            "format": "jsonv2",
                            "limit": 1,
                            "countrycodes": "in"
                        },
                        headers={
                            "User-Agent": "RuralHealthcareAIStudentProject/1.0"
                        },
                        timeout=20
                    )
                    response.raise_for_status()
                    results = response.json()

                    if not results:
                        st.error(
                            "Location not found. Try adding the district "
                            "or state to your search."
                        )
                    else:
                        result = results[0]
                        lat = float(result["lat"])
                        lon = float(result["lon"])

                        st.session_state["location"] = {
                            "name": result["display_name"],
                            "lat": lat,
                            "lon": lon,
                            "radius": radius
                        }

                        st.success("Location found.")
                        st.write("**Selected location:**", result["display_name"])
                        st.write(
                            f"**Coordinates:** {lat:.5f}, {lon:.5f}"
                        )

                except requests.RequestException:
                    st.error(
                        "The location service is unavailable right now. "
                        "Please try again later."
                    )

    if "location" in st.session_state:
        loc = st.session_state["location"]
        lat = loc["lat"]
        lon = loc["lon"]
        radius_m = loc["radius"] * 1000

        st.subheader("Nearby Healthcare Facilities")

        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"^(hospital|clinic|doctors|health_post|pharmacy)$"]
            (around:{radius_m},{lat},{lon});
          way["amenity"~"^(hospital|clinic|doctors|health_post|pharmacy)$"]
            (around:{radius_m},{lat},{lon});
          relation["amenity"~"^(hospital|clinic|doctors|health_post|pharmacy)$"]
            (around:{radius_m},{lat},{lon});
        );
        out center tags;
        """

        if st.button("Load Nearby Facilities"):
            with st.spinner("Searching mapped healthcare facilities..."):
                try:
                    r = requests.post(
                        "https://overpass-api.de/api/interpreter",
                        data={"data": query},
                        timeout=40
                    )
                    r.raise_for_status()
                    elements = r.json().get("elements", [])

                    facilities = []
                    for item in elements:
                        tags = item.get("tags", {})
                        name = tags.get("name", "Unnamed facility")
                        f_lat = item.get("lat", item.get("center", {}).get("lat"))
                        f_lon = item.get("lon", item.get("center", {}).get("lon"))

                        if f_lat is not None and f_lon is not None:
                            facilities.append({
                                "Facility": name,
                                "Type": tags.get("amenity", "Healthcare"),
                                "Latitude": f_lat,
                                "Longitude": f_lon,
                                "Address": ", ".join(
                                    filter(None, [
                                        tags.get("addr:street"),
                                        tags.get("addr:city"),
                                        tags.get("addr:postcode")
                                    ])
                                ) or "Address not listed"
                            })

                    st.session_state["facilities"] = facilities
                    if facilities:
                        st.success(f"Found {len(facilities)} mapped facilities.")
                    else:
                        st.warning(
                            "No mapped facilities found within this radius. "
                            "Try increasing the search radius."
                        )

                except (requests.RequestException, ValueError):
                    st.error(
                        "The facility search service failed. Please try again later."
                    )

        facilities = st.session_state.get("facilities", [])

        if facilities:
            df = pd.DataFrame(facilities)
            st.dataframe(
                df[["Facility", "Type", "Address"]],
                use_container_width=True,
                hide_index=True
            )

            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker(
                [lat, lon],
                tooltip="Searched location",
                icon=folium.Icon(color="blue", icon="home")
            ).add_to(m)

            for f in facilities:
                folium.Marker(
                    [f["Latitude"], f["Longitude"]],
                    tooltip=f["Facility"],
                    popup=f'{f["Facility"]} — {f["Type"]}',
                    icon=folium.Icon(color="red", icon="plus-sign")
                ).add_to(m)

            st_folium(m, width=None, height=450, key="facility_map")

            st.caption(
                "Facility data comes from OpenStreetMap contributors. "
                "Listings may be incomplete or outdated. Verify details "
                "before travelling."
            )

# ---------------- REFERRAL ROUTING ----------------
with tab3:
    st.header("Referral Route Planner")
    st.write(
        "Estimate a road route between a searched location and a selected "
        "healthcare facility."
    )

    facilities = st.session_state.get("facilities", [])

    if not facilities or "location" not in st.session_state:
        st.info(
            "First search for a location and load nearby facilities "
            "in the Find Healthcare tab."
        )
    else:
        labels = [
            f'{f["Facility"]} — {f["Type"]} ({f["Latitude"]:.4f}, {f["Longitude"]:.4f})'
            for f in facilities
        ]

        selected = st.selectbox("Choose a destination", labels)

        if st.button("Calculate Road Route", type="primary"):
            destination = facilities[labels.index(selected)]
            loc = st.session_state["location"]

            url = (
                "https://router.project-osrm.org/route/v1/driving/"
                f'{loc["lon"]},{loc["lat"]};'
                f'{destination["Longitude"]},{destination["Latitude"]}'
            )

            try:
                with st.spinner("Calculating route..."):
                    r = requests.get(
                        url,
                        params={"overview": "full", "geometries": "geojson"},
                        timeout=30
                    )
                    r.raise_for_status()
                    data = r.json()

                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    distance_km = route["distance"] / 1000
                    duration_min = route["duration"] / 60

                    st.metric("Estimated road distance", f"{distance_km:.1f} km")
                    st.metric("Estimated driving time", f"{duration_min:.0f} min")

                    st.write("**Destination:**", destination["Facility"])

                    route_map = folium.Map(
                        location=[loc["lat"], loc["lon"]],
                        zoom_start=10
                    )

                    coordinates = [
                        [point[1], point[0]]
                        for point in route["geometry"]["coordinates"]
                    ]

                    folium.PolyLine(
                        coordinates,
                        color="blue",
                        weight=5,
                        tooltip="Estimated road route"
                    ).add_to(route_map)

                    folium.Marker(
                        [loc["lat"], loc["lon"]],
                        tooltip="Start"
                    ).add_to(route_map)

                    folium.Marker(
                        [destination["Latitude"], destination["Longitude"]],
                        tooltip=destination["Facility"]
                    ).add_to(route_map)

                    st_folium(route_map, width=None, height=450, key="route_map")
                    st.caption(
                        "Route estimates depend on OpenStreetMap road data "
                        "and the public routing service. They do not account "
                        "for live traffic, road closures, ambulance availability, "
                        "or whether the facility can accept the patient."
                    )
                else:
                    st.error("No road route was returned for this destination.")

            except (requests.RequestException, ValueError, KeyError):
                st.error(
                    "The routing service is unavailable or could not calculate "
                    "this route. Please try again later."
                )

st.divider()
st.caption(
    "Rural Healthcare AI | GITAM University | "
    "Decision-support prototype; outputs are not clinically validated."
)
