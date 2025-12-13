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
# Main prediction function
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

    # ---------------- Cost prediction ----------------
    estimated_cost = float(cost_model.predict(df)[0])

    # ---------------- Delay probability (CORRECT) ----------------
    # Make sure we read the probability of class = 1 (Delayed)
    proba = delay_model.predict_proba(df)[0]
    classes = delay_model.classes_
    delay_index = list(classes).index(1)   # class "1" means delay
    delay_probability = proba[delay_index] * 100

    # ---------------- Sanity rules (REALISM LAYER) ----------------
    # Extreme unrealistic cases must be corrected logically
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
        # High risk needs MAJOR adjustment
        target_workers = max(int(workers * 1.5), workers + 7)
        target_duration = round(duration_months * 1.3, 1)

        recommendations.append(
            f"Increase workforce to around {target_workers} workers to handle project scale properly."
        )
        recommendations.append(
            f"Extend the project duration to approximately {target_duration} months to reduce schedule pressure."
        )
        recommendations.append(
            "Start critical activities early (materials, approvals, subcontractors)."
        )

    elif risk_level == "Medium":
        # Medium risk needs MODERATE adjustment
        target_workers = max(int(workers * 1.25), workers + 3)

        recommendations.append(
            f"Increase workforce to about {target_workers} workers during peak phases."
        )
        recommendations.append(
            "Monitor progress weekly and adjust resources if delays appear."
        )

    else:  # Low risk
        recommendations.append(
            "Current workforce and schedule are well balanced for this project."
        )
        recommendations.append(
            "Continue regular monitoring to maintain progress."
        )

    # ---------------- Final output ----------------
    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk_level,
        "recommendations": recommendations
    }
