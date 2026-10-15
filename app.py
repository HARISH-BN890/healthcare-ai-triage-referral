import streamlit as st
import requests
import pandas as pd
import folium

from streamlit_folium import st_folium


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Rural Healthcare AI Assistant",
    page_icon="🏥",
    layout="wide",
)


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    .hero {
        padding: 28px;
        border-radius: 16px;
        background: linear-gradient(120deg, #075985, #0f766e);
        color: white;
        margin-bottom: 22px;
    }

    .hero h1, .hero p {
        color: white;
    }

    .hero p {
        font-size: 1.1rem;
    }

    .card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #dbe3ea;
        margin-bottom: 12px;
    }

    div[data-testid="stMetric"] {
        background: #f8fafc;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🏥 Rural Healthcare AI Assistant</h1>
        <p>
            Uncertainty-aware triage support and healthcare
            facility discovery across India
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "👤 Patient Assessment",
        "📍 Find Healthcare",
        "🗺️ Referral Route",
    ]
)


# =========================================================
# TAB 1: PATIENT ASSESSMENT
# =========================================================

with tab1:

    st.header("Patient Assessment")

    st.write(
        "Enter the available patient information for a basic "
        "assessment record."
    )

    with st.form("patient_assessment_form"):

        col1, col2 = st.columns(2)

        with col1:

            age = st.number_input(
                "Age (years)",
                min_value=1,
                max_value=120,
                value=35,
            )

            systolic_bp = st.number_input(
                "Systolic blood pressure (mmHg)",
                min_value=50,
                max_value=300,
                value=120,
            )

            blood_sugar = st.number_input(
                "Blood sugar (mg/dL)",
                min_value=20,
                max_value=600,
                value=100,
            )

        with col2:

            symptom_options = [
                "Chest discomfort",
                "Breathlessness",
                "Excessive thirst",
                "Frequent urination",
                "Dizziness",
                "Fever",
                "Severe headache",
                "Other (describe below)",
            ]
            selected_symptoms = st.multiselect(
                "Symptoms (select all that apply)",
                symptom_options,
                help="Choose Other to enter a symptom that is not listed.",
            )
            other_symptoms = ""
            if "Other (describe below)" in selected_symptoms:
                other_symptoms = st.text_input(
                    "Describe other symptoms",
                    placeholder="Type symptoms here",
                    max_chars=500,
                )

            history_options = [
                "Not known",
                "Hypertension",
                "Diabetes",
                "Heart disease",
                "Family history of heart disease",
                "Other (describe below)",
            ]
            history = st.selectbox("Medical history", history_options)
            other_history = ""
            if history == "Other (describe below)":
                other_history = st.text_area(
                    "Describe other medical history",
                    placeholder="Type any other known medical history here",
                    max_chars=1000,
                    height=90,
                )

        submitted = st.form_submit_button(
            "Save Patient Assessment",
            type="primary",
        )

    if submitted:

        st.session_state["patient"] = {
            "age": age,
            "systolic_bp": systolic_bp,
            "blood_sugar": blood_sugar,
            "symptoms": [
                symptom for symptom in selected_symptoms
                if symptom != "Other (describe below)"
            ] + ([f"Other: {other_symptoms.strip()}"] if other_symptoms.strip() else []),
            "history": (
                f"Other: {other_history.strip()}"
                if history == "Other (describe below)" and other_history.strip()
                else history
            ),
        }

        st.success(
            "Assessment information saved for this session."
        )

    st.info(
        "This form records information only. It does not "
        "provide a clinically validated diagnosis or determine "
        "whether a patient is safe."
    )

    if "patient" in st.session_state:

        patient = st.session_state["patient"]

        st.subheader("Assessment Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Age",
            f'{patient["age"]} years',
        )

        col2.metric(
            "Systolic BP",
            f'{patient["systolic_bp"]} mmHg',
        )

        col3.metric(
            "Blood sugar",
            f'{patient["blood_sugar"]} mg/dL',
        )

        st.write(
            "**Symptoms:**",
            ", ".join(patient["symptoms"]) or "None selected",
        )

        st.write(
            "**Medical history:**",
            patient["history"],
        )

        st.caption(
            "Information is stored in the current application "
            "session and is not a permanent medical record."
        )


# =========================================================
# TAB 2: HEALTHCARE FACILITY SEARCH
# =========================================================

with tab2:

    st.header("Find Healthcare Facilities Across India")

    st.write(
        "Search using a village, town, district, PIN code, "
        "or address."
    )

    place = st.text_input(
        "Enter location",
        placeholder="Example: Pavagada, Karnataka",
        key="location_input",
    )

    radius = st.select_slider(
        "Search radius",
        options=[2, 5, 10, 15, 25],
        value=5,
        format_func=lambda value: f"{value} km",
    )

    search_clicked = st.button(
        "Search Location and Facilities",
        type="primary",
    )

    # -----------------------------------------------------
    # GEOCODING
    # -----------------------------------------------------

    if search_clicked:

        if not place.strip():

            st.warning(
                "Please enter a village, town, or address."
            )

        else:

            with st.spinner("Searching for your location..."):

                try:

                    response = requests.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={
                            "q": f"{place.strip()}, India",
                            "format": "jsonv2",
                            "limit": 1,
                            "countrycodes": "in",
                        },
                        headers={
                            "User-Agent": (
                                "RuralHealthcareAIStudentProject/1.0 "
                                "(educational prototype)"
                            )
                        },
                        timeout=25,
                    )

                    response.raise_for_status()

                    results = response.json()

                    if not results:

                        st.error(
                            "Location not found. Try including "
                            "the district and state."
                        )

                    else:

                        result = results[0]

                        location_data = {
                            "name": result["display_name"],
                            "lat": float(result["lat"]),
                            "lon": float(result["lon"]),
                            "radius": radius,
                        }

                        st.session_state["location"] = location_data

                        # Clear facilities from the previous location.
                        st.session_state.pop("facilities", None)

                        st.success("Location found!")

                        st.write(
                            "**Selected location:**",
                            location_data["name"],
                        )

                        st.write(
                            f'**Coordinates:** '
                            f'{location_data["lat"]:.5f}, '
                            f'{location_data["lon"]:.5f}'
                        )

                except requests.RequestException as error:

                    st.error(
                        "The location search service is unavailable."
                    )

                    st.caption(
                        f"Technical details: {type(error).__name__}. "
                        "Please try again later."
                    )

                except (ValueError, KeyError, TypeError) as error:

                    st.error(
                        "The location service returned an unexpected response."
                    )

                    st.caption(
                        f"Technical details: {type(error).__name__}"
                    )

    # -----------------------------------------------------
    # SEARCH NEARBY HEALTHCARE FACILITIES
    # -----------------------------------------------------

    if "location" in st.session_state:

        location = st.session_state["location"]

        lat = location["lat"]
        lon = location["lon"]
        radius_m = location["radius"] * 1000

        st.subheader("Nearby Healthcare Facilities")

        st.write(
            f'Searching within {location["radius"]} km '
            f'of the selected location.'
        )

        load_facilities = st.button(
            "Load Nearby Facilities",
            key="load_facilities_button",
        )

        if load_facilities:

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

            # Public Overpass servers. A second is attempted
            # if the first server fails.
            endpoints = [
                "https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter",
            ]

            facilities = []
            last_error = None
            successful_response = False

            with st.spinner(
                "Searching OpenStreetMap for nearby facilities..."
            ):

                for endpoint in endpoints:

                    try:

                        response = requests.post(
                            endpoint,
                            data={"data": query},
                            headers={
                                "User-Agent": (
                                    "RuralHealthcareAIStudentProject/1.0"
                                )
                            },
                            timeout=90,
                        )

                        response.raise_for_status()

                        data = response.json()

                        elements = data.get("elements", [])

                        successful_response = True
                        last_error = None

                        for item in elements:

                            tags = item.get("tags", {})

                            center = item.get("center", {})

                            facility_lat = item.get(
                                "lat",
                                center.get("lat"),
                            )

                            facility_lon = item.get(
                                "lon",
                                center.get("lon"),
                            )

                            if (
                                facility_lat is None
                                or facility_lon is None
                            ):
                                continue

                            address_parts = [
                                tags.get("addr:street"),
                                tags.get("addr:city"),
                                tags.get("addr:postcode"),
                            ]

                            facilities.append(
                                {
                                    "Facility": tags.get(
                                        "name",
                                        "Unnamed facility",
                                    ),
                                    "Type": tags.get(
                                        "amenity",
                                        "Healthcare",
                                    ),
                                    "Latitude": float(facility_lat),
                                    "Longitude": float(facility_lon),
                                    "Address": ", ".join(
                                        part
                                        for part in address_parts
                                        if part
                                    ) or "Address not listed",
                                }
                            )

                        # Do not contact another server if this
                        # server returned a valid response.
                        break

                    except (
                        requests.RequestException,
                        ValueError,
                    ) as error:

                        last_error = error

            if not successful_response:

                st.session_state.pop("facilities", None)

                st.error(
                    "Healthcare facility data is temporarily unavailable."
                )

                if last_error is not None:

                    st.caption(
                        f"Technical details: "
                        f"{type(last_error).__name__}."
                    )

                st.info(
                    "Both public search services may be busy or "
                    "unavailable. Please try again later or increase "
                    "the search radius after retrying."
                )

            else:

                # Remove duplicate entries when possible.
                unique_facilities = {}

                for facility in facilities:

                    key = (
                        facility["Facility"],
                        facility["Latitude"],
                        facility["Longitude"],
                    )

                    unique_facilities[key] = facility

                facilities = list(unique_facilities.values())

                st.session_state["facilities"] = facilities

                if facilities:

                    st.success(
                        f"Found {len(facilities)} mapped facilities."
                    )

                else:

                    st.warning(
                        "No mapped healthcare facilities were found "
                        "within this radius. This does not mean that "
                        "no healthcare services exist nearby. Try a "
                        "larger radius."
                    )

        # -------------------------------------------------
        # DISPLAY FACILITIES
        # -------------------------------------------------

        facilities = st.session_state.get("facilities", [])

        if facilities:

            st.subheader("Facility Directory")

            dataframe = pd.DataFrame(facilities)

            st.dataframe(
                dataframe[
                    [
                        "Facility",
                        "Type",
                        "Address",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

            st.subheader("Healthcare Facility Map")

            facility_map = folium.Map(
                location=[lat, lon],
                zoom_start=12,
            )

            folium.Marker(
                [lat, lon],
                tooltip="Searched location",
                popup=location["name"],
                icon=folium.Icon(
                    color="blue",
                    icon="home",
                ),
            ).add_to(facility_map)

            for facility in facilities:

                folium.Marker(
                    [
                        facility["Latitude"],
                        facility["Longitude"],
                    ],
                    tooltip=facility["Facility"],
                    popup=(
                        f'{facility["Facility"]} '
                        f'— {facility["Type"]}'
                    ),
                    icon=folium.Icon(
                        color="red",
                        icon="plus-sign",
                    ),
                ).add_to(facility_map)

            st_folium(
                facility_map,
                width=None,
                height=450,
                key="facility_map",
            )

            st.caption(
                "Facility data comes from OpenStreetMap contributors. "
                "Listings may be incomplete or outdated. Verify "
                "facility details before travelling."
            )

    else:

        st.info(
            "Enter a location and click Search Location and Facilities "
            "to begin."
        )


# =========================================================
# TAB 3: REFERRAL ROUTE PLANNER
# =========================================================

with tab3:
    st.header("Referral Route Planner")
    st.write(
        "Estimate a road route between your searched location "
        "and a selected healthcare facility."
    )

    facilities = st.session_state.get("facilities", [])
    location = st.session_state.get("location")

    if not facilities or not location:
        st.info(
            "First open Find Healthcare, search for a location, "
            "and load nearby facilities."
        )
    else:
        labels = [
            f'{facility["Facility"]} — {facility["Type"]} '
            f'({facility["Latitude"]:.4f}, {facility["Longitude"]:.4f})'
            for facility in facilities
        ]
        selected_label = st.selectbox("Choose a destination", labels)
        selected_index = labels.index(selected_label)

        # Drop a saved route if the user changes the destination or location.
        saved_route = st.session_state.get("route_result")
        route_signature = (
            location["lat"], location["lon"], selected_label
        )
        if saved_route and saved_route.get("signature") != route_signature:
            st.session_state.pop("route_result", None)
            saved_route = None

        if st.button("Calculate Road Route", type="primary", key="calculate_road_route"):
            destination = facilities[selected_index]
            route_url = (
                "https://router.project-osrm.org/route/v1/driving/"
                f'{location["lon"]},{location["lat"]};'
                f'{destination["Longitude"]},{destination["Latitude"]}'
            )

            try:
                with st.spinner("Calculating the estimated road route..."):
                    response = requests.get(
                        route_url,
                        params={"overview": "full", "geometries": "geojson"},
                        headers={"User-Agent": "RuralHealthcareAIStudentProject/1.0"},
                        timeout=30,
                    )
                    response.raise_for_status()
                    route_data = response.json()

                if route_data.get("code") == "Ok" and route_data.get("routes"):
                    route = route_data["routes"][0]
                    coordinates = [
                        [point[1], point[0]]
                        for point in route["geometry"]["coordinates"]
                    ]
                    if not coordinates:
                        st.error("The routing service returned an empty route. Try another destination.")
                        st.session_state.pop("route_result", None)
                    else:
                        st.session_state["route_result"] = {
                            "signature": route_signature,
                            "destination": destination.copy(),
                            "location": location.copy(),
                            "distance_km": route["distance"] / 1000,
                            "duration_min": route["duration"] / 60,
                            "coordinates": coordinates,
                        }
                        st.success("Route calculated. The route will remain visible while you use this session.")
                else:
                    st.session_state.pop("route_result", None)
                    st.error("No road route was returned. Try another destination or check the location.")
                    st.caption(f'Response code: {route_data.get("code", "Unknown")}.')

            except requests.RequestException as error:
                st.error("The routing service is currently unavailable. Please try again in a moment.")
                st.caption(f"Technical details: {type(error).__name__}.")
            except (ValueError, KeyError, IndexError, TypeError) as error:
                st.error("The routing service returned an unexpected response.")
                st.caption(f"Technical details: {type(error).__name__}.")
                st.session_state.pop("route_result", None)

        # Render saved route OUTSIDE the button block. Streamlit reruns the
        # script after map interaction; saving this in session_state prevents
        # the route from vanishing on that rerun.
        saved_route = st.session_state.get("route_result")
        if saved_route and saved_route.get("signature") == route_signature:
            route_location = saved_route["location"]
            destination = saved_route["destination"]

            col1, col2 = st.columns(2)
            col1.metric("Estimated road distance", f'{saved_route["distance_km"]:.1f} km')
            col2.metric("Estimated driving time", f'{saved_route["duration_min"]:.0f} min')
            st.write("**Destination:**", destination["Facility"])

            route_map = folium.Map(
                location=[route_location["lat"], route_location["lon"]],
                zoom_start=10,
            )
            folium.PolyLine(
                saved_route["coordinates"],
                color="blue",
                weight=5,
                tooltip="Estimated road route",
            ).add_to(route_map)
            folium.Marker(
                [route_location["lat"], route_location["lon"]],
                tooltip="Starting location",
                popup=route_location["name"],
                icon=folium.Icon(color="green", icon="home"),
            ).add_to(route_map)
            folium.Marker(
                [destination["Latitude"], destination["Longitude"]],
                tooltip=destination["Facility"],
                popup=destination["Facility"],
                icon=folium.Icon(color="red", icon="plus-sign"),
            ).add_to(route_map)

            st.subheader("Estimated Road Route")
            st_folium(route_map, width=None, height=450, key="route_map_persistent")
            st.caption(
                "Route estimates depend on OpenStreetMap road data and the public routing service. "
                "They do not account for live traffic, road closures, ambulance availability, "
                "or whether a facility can accept a patient. For emergencies, contact local emergency services."
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Rural Healthcare AI | GITAM University | "
    "Educational decision-support prototype. "
    "Not clinically validated; do not use for diagnosis "
    "or to delay emergency medical care."
)
