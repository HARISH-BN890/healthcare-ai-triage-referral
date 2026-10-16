                    "decision": decision, "override_reason": reason.strip() or "Not applicable",
                    "risk_label": result["level"], "mode": "plain checklist" if kill_switch else "illustrative model",
                }
                st.session_state.assessments.append(record)
                previous_hash = st.session_state.audit_log[-1]["hash"] if st.session_state.audit_log else "GENESIS"
                event = {
                    "event_id": len(st.session_state.audit_log) + 1,
                    "time_utc": utc_now(), "actor": "demo-health-worker",
                    "action": "decision_saved", "assessment_id": result["id"],
                    "previous_hash": previous_hash,
                }
                event["hash"] = hashlib.sha256(str(event).encode()).hexdigest()[:16]
                st.session_state.audit_log.append(event)
                st.success("Decision saved to this session's demo log.")
    st.markdown("### Saved assessments")
    if st.session_state.assessments:
        st.dataframe(pd.DataFrame(st.session_state.assessments), hide_index=True, use_container_width=True)
        csv = pd.DataFrame(st.session_state.assessments).to_csv(index=False).encode("utf-8")
        st.download_button("Download assessment log (CSV)", csv, "aarogya_marg_assessments.csv", "text/csv")
    else:
        st.caption("No decisions saved yet.")
    st.markdown("### Audit trail")
    if st.session_state.audit_log:
        st.success(f"Audit events recorded in this session: {len(st.session_state.audit_log)}")
        st.dataframe(pd.DataFrame(st.session_state.audit_log), hide_index=True, use_container_width=True)
    else:
        st.caption("Audit events will appear after a decision is saved.")
    st.caption("Logs are session-only and are not a tamper-proof clinical audit system.")

# ============================================================
# 6 EVALUATION
# ============================================================
with tabs[5]:
    st.subheader("Evaluation on synthetic data")
    st.write("This section demonstrates how evaluation tables and calibration plots can be presented. The generated data is synthetic and does not establish real-world medical performance.")
    rng = np.random.default_rng(7)
    n = 600
    eval_rows = []
    for condition, center in [("Hypertension", 0.34), ("Diabetes", 0.46), ("Heart-disease risk", 0.20)]:
        y = rng.binomial(1, center, size=n)
        scores = np.clip(y * rng.normal(0.72, 0.17, n) + (1-y) * rng.normal(0.18, 0.14, n), 0, 1)
        threshold = 0.5
        pred = scores >= threshold
        tp = int(np.sum((pred == 1) & (y == 1)))
        tn = int(np.sum((pred == 0) & (y == 0)))
        fp = int(np.sum((pred == 1) & (y == 0)))
        fn = int(np.sum((pred == 0) & (y == 1)))
        sensitivity = tp / max(1, tp + fn)
        specificity = tn / max(1, tn + fp)
        # Brier score is valid for synthetic labels/scores; AUC omitted to avoid dependency.
        brier = float(np.mean((scores - y) ** 2))
        eval_rows.append({
            "Condition": condition, "Synthetic rows": n, "Threshold": threshold,
            "Sensitivity (synthetic)": round(sensitivity, 3),
            "Specificity (synthetic)": round(specificity, 3),
            "Brier score (synthetic)": round(brier, 3),
        })
    st.dataframe(pd.DataFrame(eval_rows), hide_index=True, use_container_width=True)
    st.caption("These values are generated for software demonstration only. They are not validation results for the patient-scoring heuristic above.")
    st.markdown("#### Illustrative calibration-style view")
    calibration = pd.DataFrame({
        "Predicted score bin": ["0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"],
        "Example predicted": [0.1, 0.3, 0.5, 0.7, 0.9],
        "Example observed": [0.08, 0.27, 0.51, 0.68, 0.88],
    }).set_index("Predicted score bin")
    st.line_chart(calibration, y_label="Illustrative frequency")
    st.caption("The calibration-style values are illustrative placeholders, not measured performance.")

# ============================================================
# 7 SCENARIOS
# ============================================================
with tabs[6]:
    st.subheader("Preloaded patients for a repeatable demo")
    scenarios = [
        "A. Lakshmi (54 F): high BP and sugar with chest discomfort",
        "B. Ravi (62 M): very high blood pressure with dizziness",
        "C. Sunita (35 F): example healthy screening",
        "D. Bonus: sparse information (age and tiredness only)",
    ]
    for i, scenario in enumerate(scenarios):
        left, right = st.columns([8, 1])
        left.write(scenario)
        if right.button("Load", key=f"scenario_{i}"):
            st.session_state.patient = make_demo_patient(scenario)
            st.session_state.last_result = None
            st.success(f"Loaded scenario: {scenario}. Open Assess and run educational triage.")
    st.caption("All scenario profiles are fictional and are intended only for repeatable classroom demonstrations.")

# ============================================================
# 8 ABOUT & LIMITS
# ============================================================
with tabs[7]:
    st.subheader("About and limits")
    st.markdown("**Intended use:** demonstrate how a Bayesian-inspired scoring workflow, decision-support interface, referral search and human review might be organised for a rural-health coursework prototype.")
    st.markdown("**Not intended for:** real-patient diagnosis, autonomous triage, treatment decisions, or claims of clinical accuracy.")
    st.markdown("**Data:** scenario patients and evaluation data are synthetic. Do not enter names, phone numbers, addresses, medical record numbers or other identifying patient details.")
    st.markdown("**Human in charge:** the system may display an illustrative suggestion; a qualified healthcare professional must make the decision. Users can accept or override a suggestion and record a reason.")
    st.markdown("**Facility data:** sourced from public OpenStreetMap services when available. Listings may be missing, outdated, or incorrectly tagged. A failed request does not mean no healthcare facility exists.")
    st.markdown("**Routing:** public road-route estimates are not live traffic or ambulance guidance.")
    st.markdown("**Safety:** if chest discomfort, breathlessness, very high readings or other concerning symptoms occur in a real person, seek professional assessment rather than relying on this prototype.")
    st.markdown("**Model card**")
    st.json({
        "name": "Aarogya Marg educational prototype",
        "version": APP_VERSION,
        "model_type": "Transparent hand-written illustrative scoring heuristic",
        "training_data": "None for the patient scoring heuristic",
        "evaluation_data": "Separate synthetic demonstration data only",
        "clinical_validation": False,
        "approved_medical_device": False,
        "persistent_storage": False,
    })
    st.markdown("**Known limitations**")
    st.dataframe(pd.DataFrame([
        {"Hazard": "Missed high-risk case", "Cause": "Incomplete information or simplistic score", "Control": "Red-flag reminders; clinician review", "Residual risk": "Cannot be eliminated in this prototype"},
        {"Hazard": "Blind trust in output", "Cause": "Over-reliance on scores", "Control": "Warnings, explanations and human decision", "Residual risk": "Requires careful presentation"},
        {"Hazard": "Missing facility listing", "Cause": "Incomplete public map data or timeout", "Control": "Show service failure clearly; advise verification", "Residual risk": "Public data dependency"},
        {"Hazard": "Wrong travel estimate", "Cause": "Map data limitations and no live traffic", "Control": "Label estimates; verify route locally", "Residual risk": "Not for emergency dispatch"},
    ]), hide_index=True, use_container_width=True)

st.markdown("---")
st.markdown(
    '<p class="small-muted">AAROGYA MARG · Coursework prototype · Synthetic data only · Not clinically validated.</p>',
    unsafe_allow_html=True,
)
