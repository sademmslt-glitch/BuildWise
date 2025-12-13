import pandas as pd
import joblib
import streamlit as st

# -------------------------------------------------
# Load models once (VERY IMPORTANT for correctness + speed)
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

    # ---------- Cost prediction (Regression) ----------
    estimated_cost = float(cost_model.predict(df)[0])

    # ---------- Delay prediction (Probability, NOT class) ----------
    # probability of delay = class 1
    delay_probability = delay_model.predict_proba(df)[0][1] * 100

    # ---------- Risk level ----------
    if delay_probability < 30:
        risk_level = "Low"
    elif delay_probability < 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # ---------- SMART & REALISTIC recommendations ----------
    recommendations = []

    if risk_level == "High":
        extra_workers = max(3, int(workers * 0.2))
        new_duration = round(duration_months + max(1, duration_months * 0.25), 1)

        recommendations.append(
            f"Add around {extra_workers} more workers to reduce workload pressure."
        )
        recommendations.append(
            f"Extend the project duration to about {new_duration} months to avoid delays."
        )
        recommendations.append(
            "Start material procurement earlier and confirm supplier availability."
        )

    elif risk_level == "Medium":
        recommendations.append(
            "The project is manageable, but close monitoring is recommended."
        )
        recommendations.append(
            "Consider adding 1–2 workers during critical phases."
        )
        recommendations.append(
            "Review the schedule weekly to catch delays early."
        )

    else:  # Low risk
        recommendations.append(
            "The project plan looks balanced and realistic."
        )
        recommendations.append(
            "Maintain current workforce and timeline."
        )
        recommendations.append(
            "Regular progress tracking should be sufficient."
        )

    # ---------- Final output ----------
    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk_level,
        "recommendations": recommendations
    }
