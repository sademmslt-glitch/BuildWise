import pandas as pd
import joblib
import streamlit as st

# -------------------------------------------------
# Load models once (speed + stability)
# -------------------------------------------------
@st.cache_resource
def load_models():
    cost_model = joblib.load("cost_model.pkl")
    delay_model = joblib.load("delay_model.pkl")
    model_columns = joblib.load("model_columns.pkl")
    return cost_model, delay_model, model_columns

cost_model, delay_model, model_columns = load_models()

# -------------------------------------------------
# Main prediction logic
# -------------------------------------------------
def predict(project_type, project_size, area_m2, duration_months, workers):

    # ---------------- Prepare input ----------------
    input_data = {
        "project_type": project_type,
        "project_size": project_size,
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }

    df = pd.DataFrame([input_data])
    df = pd.get_dummies(df)
    df = df.reindex(columns=model_columns, fill_value=0)

    # ---------------- Cost prediction (base model) ----------------
    estimated_cost = float(cost_model.predict(df)[0])

    # ---------------- HVAC COST CALIBRATION (IMPORTANT) ----------------
    # Prevent unrealistic multi-million costs for HVAC projects
    if project_type == "HVAC Installation":
        min_cost = area_m2 * 1800   # conservative lower bound
        max_cost = area_m2 * 4500   # realistic upper bound
        estimated_cost = max(min_cost, min(estimated_cost, max_cost))

    # ---------------- Delay probability (correct class index) ----------------
    proba = delay_model.predict_proba(df)[0]
    classes = delay_model.classes_
    delay_index = list(classes).index(1)   # class "1" = delayed
    delay_probability = proba[delay_index] * 100

    # ---------------- Sanity rules (REALISM LAYER) ----------------
    # Handle unrealistic workforce vs project scale
    if project_size == "Large" and area_m2 >= 400 and workers <= 3:
        delay_probability = max(delay_probability, 75.0)

    if project_size == "Medium" and area_m2 >= 250 and workers <= 2:
        delay_probability = max(delay_probability, 60.0)

    # ---------------- Risk level ----------------
    if delay_probability < 30:
        risk_level = "Low"
    elif delay_probability < 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # -------------------------------------------------
    # STRONG & EFFECTIVE RECOMMENDATIONS
    # -------------------------------------------------
    recommendations = []

    if risk_level == "High":
        target_workers = max(int(workers * 1.5), workers + 7)
        target_duration = round(duration_months * 1.3, 1)

        recommendations.append(
            f"Increase workforce to around {target_workers} workers to match the project scale."
        )
        recommendations.append(
            f"Extend the project duration to approximately {target_duration} months to reduce schedule pressure."
        )
        recommendations.append(
            "Start critical activities early (materials procurement, approvals, subcontractors)."
        )

    elif risk_level == "Medium":
        target_workers = max(int(workers * 1.25), workers + 3)

        recommendations.append(
            f"Increase workforce to about {target_workers} workers during peak phases."
        )
        recommendations.append(
            "Monitor progress weekly and reallocate resources if delays appear."
        )

    else:  # Low risk
        recommendations.append(
            "Current workforce and schedule are well balanced for this project."
        )
        recommendations.append(
            "Continue regular monitoring to maintain steady progress."
        )

    # ---------------- Final output ----------------
    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk_level,
        "recommendations": recommendations
    }
