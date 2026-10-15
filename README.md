# 🏥 Rural Healthcare AI Assistant

### Uncertainty-Aware Triage Support and Healthcare Facility Discovery Across India

The **Rural Healthcare AI Assistant** is an educational web-based prototype designed to support rural primary healthcare workers by organising basic patient information, demonstrating uncertainty-aware decision-support concepts, locating nearby healthcare facilities, and displaying estimated road routes.

The project combines Python-based decision-support modules with mapping and location services to explore how technology can help improve access to healthcare in rural areas.

## 🎯 Problem Statement

People living in rural areas may face challenges in finding nearby healthcare facilities and understanding possible referral options. Healthcare workers may also need support when patient information is incomplete or uncertain.

This project explores a technology-based approach to patient information collection, healthcare facility discovery, and referral-route visualisation.

## ✨ Key Features

- **Patient Assessment:** Enter basic patient information, vital measurements, symptoms, and medical history.
- **Custom Symptom Input:** Select listed symptoms or describe other symptoms.
- **Medical History:** Record available medical history, including additional details.
- **Healthcare Facility Search:** Search for villages, towns, and locations across India.
- **Nearby Facility Discovery:** Search for healthcare facilities within a selected radius.
- **Interactive Maps:** View facility locations using map markers.
- **Road Route Estimation:** Display an estimated road route, distance, and travel time to a selected destination.
- **Bayesian Probability Demonstration:** Explore probability calculations and uncertainty labels.
- **Expected Utility Decision Support:** Compare hypothetical actions using utility scores.
- **Referral Routing Algorithm:** Find a lowest-cost path through a simulated healthcare referral network.

## 🛠️ Tools and Technologies

| Technology | Purpose |
|---|---|
| Python | Application logic and algorithms |
| Streamlit | Web interface |
| Pandas | Data organisation |
| Requests | API communication |
| Folium | Interactive maps |
| Streamlit-Folium | Display maps in Streamlit |
| OpenStreetMap | Open map and facility data |
| Nominatim | Location search |
| Overpass API | Nearby facility queries |
| OSRM | Estimated road routing |
| GitHub | Source-code management and collaboration |
| Google Colab / Jupyter Notebook | Notebook-based development |
| Streamlit Community Cloud | Website hosting |

## 🧠 AI and Algorithm Modules

- **`bayesian_model.py`** — Demonstrates probability calculations and uncertainty labels.
- **`decision_support.py`** — Calculates expected utility and compares hypothetical actions.
- **`referral_routing.py`** — Finds a lowest-cost route through a simulated healthcare referral network.
- **`app.py`** — Provides the Streamlit application interface and connects the user-facing features.

## 📁 Project Structure

```text
healthcare-ai-triage-referral/
│
├── app.py
├── bayesian_model.py
├── decision_support.py
├── referral_routing.py
├── Healthcare_AI_Project.ipynb
├── requirements.txt
└── README.md
```

## 🚀 Run the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/HARISH-BN890/healthcare-ai-triage-referral.git
```

### 2. Open the project folder

```bash
cd healthcare-ai-triage-referral
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the website

```bash
streamlit run app.py
```

The application should open in your browser at the local Streamlit address displayed in the terminal.

## 🗺️ Location and Routing Services

The project uses public mapping services to explore healthcare access:

- **Nominatim:** Converts a place or address into geographic coordinates.
- **Overpass API:** Searches OpenStreetMap data for nearby healthcare facilities.
- **OSRM:** Calculates estimated road routes between selected locations.

The availability and completeness of facility data depend on OpenStreetMap contributions and the availability of public API services.

## 🔮 Future Improvements

- Improve the interface for mobile and low-bandwidth environments.
- Add more complete and verified rural healthcare facility information.
- Improve multilingual support for rural healthcare workers.
- Add better handling of incomplete patient information.
- Evaluate decision-support algorithms using appropriate, validated datasets.
- Add more robust error handling and API availability checks.

## ⚠️ Disclaimer

This project is an **educational prototype**, not a clinically validated medical diagnostic or triage system.

The probability and expected-utility examples use illustrative values. They must not be interpreted as validated patient-risk predictions or medical recommendations. Facility listings may be incomplete or outdated, and estimated routes do not confirm facility availability, emergency-service availability, or clinical suitability.

Always rely on qualified healthcare professionals for medical decisions.

## 👥 Project Information

**Project:** Rural Healthcare AI Assistant  
**Repository:** [GitHub Repository](https://github.com/HARISH-BN890/healthcare-ai-triage-referral)

Developed as an academic project exploring artificial intelligence, uncertainty-aware decision support, and rural healthcare access.
