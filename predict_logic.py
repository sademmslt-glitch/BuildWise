import pandas as pd
import joblib
import streamlit as st

# ----------------------------
# Load models once (VERY IMPORTANT)
# ----------------------------
@st.cache_resource
def load_models():
    cost_model = joblib.load("cost_model.pkl")
    delay_model = joblib.load("delay_model.pkl")
    model_columns = joblib.load("model_columns.pkl")
    return cost_model, delay_model, model_columns

cost_model, delay_model, model_columns = load_models()

# ----------------------------
# Prediction function
# ----------------------------
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

    # Friendly recommendations
    if risk == "High":
        recommendations = [
            "You might want to give the schedule a little breathing room.",
            "Having extra workers during busy weeks could really help.",
            "Ordering materials early can save last-minute stress."
        ]
    elif risk == "Medium":
        recommendations = [
            "Things look okay, just keep an eye on progress.",
            "Weekly check-ins should be enough to stay on track."
        ]
    else:
        recommendations = [
            "Everything looks smooth so far.",
            "Just keep monitoring the project regularly."
        ]

    return {
        "estimated_cost": round(estimated_cost, 2),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
