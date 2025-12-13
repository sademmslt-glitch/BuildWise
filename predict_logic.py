import pandas as pd
import joblib
import streamlit as st

# -------------------------------------------------
# Load models once (for speed + consistency)
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

    # ---------- Prepare input ----------
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

    # ---------- Cost prediction ----------
    estimated_cost = float(cost_model.predict(df)[0])

    # ---------- Delay probability (REAL probability) ----------
    delay_probability = delay_model.predict_proba(df)[0][1] * 100

    # ---------- Risk level ----------
    if delay_probability < 30:
        risk_level = "Low"
    elif delay_probability < 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # -------------------------------------------------
    # SMART, EFFECTIVE & REALISTIC RECOMMENDATIONS
    # -------------------------------------------------
    recommendations = []

    if risk_level == "High":
        # High risk needs STRONG adjustment
        target_workers = int(round(workers * 1.4))
        target_duration = round(duration_months * 1.3, 1)

        recommendations.append(
            f"Increase workforce to around {target_workers} workers to significantly reduce workload pressure."
        )
        recommendations.append(
            f"Extend the project duration to approximately {target_duration} months to stabilize the schedule."
        )
        recommendations.append(
            "Prioritize critical activities early (materials, approvals, subcontractors)."
        )

    elif risk_level == "Medium":
        # Medium risk needs MODERATE adjustment
        target_workers = int(round(workers * 1.2))

        recommendations.append(
            f"Increase workers to about {target_workers} during peak phases to avoid delays."
        )
        recommendations.append(
            "Conduct weekly progress reviews and adjust resources if needed."
        )

    else:  # Low risk
        recommendations.append(
            "Current workforce and schedule are well balanced."
        )
        recommendations.append(
            "Continue with regular monitoring and planned execution."
        )

    # ---------- Final output ----------
    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk_level,
        "recommendations": recommendations
    }
