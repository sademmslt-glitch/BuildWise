import pandas as pd
import joblib
import streamlit as st

# --------------------------------------------------
# Load models ONCE only (this is the speed solution)
# --------------------------------------------------
@st.cache_resource
def load_models():
    cost_model = joblib.load("cost_model.pkl")
    delay_model = joblib.load("delay_model.pkl")
    model_columns = joblib.load("model_columns.pkl")
    return cost_model, delay_model, model_columns

cost_model, delay_model, model_columns = load_models()

# --------------------------------------------------
# Prediction logic
# --------------------------------------------------
def predict(project_type, project_size, area_m2, duration_months, workers):

    data = {
        "project_type": project_type,
        "project_size": project_size,
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }

    df = pd.DataFrame([data])
    df = pd.get_dummies(df)
    df = df.reindex(columns=model_columns, fill_value=0)

    estimated_cost = float(cost_model.predict(df)[0])
    delay_probability = float(delay_model.predict(df)[0])

    # Risk level
    if delay_probability < 30:
        risk = "Low"
    elif delay_probability < 60:
        risk = "Medium"
    else:
        risk = "High"

    # Friendly recommendations (مو رسمية)
    if risk == "High":
        recommendations = [
            "The schedule feels a bit tight — adding buffer time could help.",
            "Extra workers during peak weeks might reduce pressure.",
            "Ordering materials early can avoid last-minute delays."
        ]
    elif risk == "Medium":
        recommendations = [
            "The plan looks reasonable, just keep tracking progress.",
            "Weekly check-ins should help avoid surprises."
        ]
    else:
        recommendations = [
            "Everything looks smooth so far.",
            "Regular monitoring should be enough to stay on track."
        ]

    return {
        "estimated_cost": round(estimated_cost, 2),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
