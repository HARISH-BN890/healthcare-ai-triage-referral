import hashlib
import math
import time
from datetime import datetime, timezone

import folium
import numpy as np
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

# ============================================================
# AAROGYA MARG — educational rural triage/referral prototype
# ============================================================

st.set_page_config(
    page_title="Aarogya Marg | Rural Healthcare Support",
    page_icon="🏥",
    layout="wide",
)

APP_VERSION = "am-2026.10"
DISCLAIMER = (
    "EDUCATIONAL PROTOTYPE ONLY — not a medical device, diagnosis, or "
    "clinically validated decision system. Use synthetic/demo data only. "
    "A qualified clinician must make clinical decisions. For a real emergency, "
    "contact local emergency services immediately."
)

# ----------------------------- Styling -----------------------------
st.markdown(
    """
    <style>
    .block-container {max-width: 1450px; padding-top: 1.4rem; padding-bottom: 2rem;}
    .hero {padding: 25px 30px; border-radius: 18px; color: white;
           background: linear-gradient(115deg,#073b5c,#087f8c 72%,#11998e);
           margin-bottom: 15px;}
    .hero h1 {color:white !important; margin:0 0 7px 0;}
    .hero p {color:#e5f6f7 !important; margin:0;}
    .notice {padding:13px 16px; border-radius:10px; background:#fff9d8;
             color:#725b00; margin:12px 0 18px 0;}
    .small-muted {color:#6b7280; font-size:.86rem;}
    div[data-testid="stMetric"] {border:1px solid #e0e7ed; padding:12px; border-radius:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🩺 AAROGYA MARG</h1>
      <p>Rural triage and referral support · आरोग्य मार्ग</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f'<div class="notice">{DISCLAIMER}</div>', unsafe_allow_html=True)

# ----------------------------- Utilities -----------------------------
def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def clamp(value, low=0.01, high=0.99):
    return max(low, min(high, float(value)))


def pct(value):
    return f"{100 * value:.0f}%"


def get_default_patient():
    return {
        "age": 35,
        "sex": "Female",
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "glucose": 100,
        "glucose_type": "Random",
        "bmi": 23.0,
        "smoker": "No",
        "family_history": "No",
        "headache": "No",
        "thirst": "No",
        "tiredness": "No",
        "chest_discomfort": "No",
        "breathlessness": "No",
        "dizziness": "No",
    }


def risk_estimates(p):
    """
    Transparent educational scoring heuristic. These are not clinical predictions.
