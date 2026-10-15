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
            st_folium(route_map, height=450, key="route_map_persistent")
            st.caption(
                "Route estimates depend on OpenStreetMap road data and the public routing service. "
                "They do not account for live traffic, road closures, ambulance availability, "
                "or whether a facility can accept a patient. For emergencies, contact local emergency services."
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    '<div class="site-footer">Rural Healthcare Assistant · GITAM University · Educational prototype only. Not clinically validated; do not use for diagnosis or delay emergency care.</div>',
    unsafe_allow_html=True,
)
