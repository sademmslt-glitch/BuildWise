import pandas as pd
import joblib
import streamlit as st

@st.cache_resource
def load_models():
    cost_model = joblib.load("cost_model.pkl")
    delay_model = joblib.load("delay_model.pkl")
    model_columns = joblib.load("model_columns.pkl")
    return cost_model, delay_model, model_columns

cost_model, delay_model, model_columns = load_models()

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
    delay_prob = float(delay_model.predict(df)[0])

    # Risk level
    if delay_prob < 30:
        risk = "Low"
    elif delay_prob < 60:
        risk = "Medium"
    else:
        risk = "High"

    # Friendly + precise recommendations
    recommendations = []

    if risk == "High":
        recommendations.append(f"Add {max(3, workers//5)} more workers to reduce delay risk.")
        recommendations.append(f"Extend project duration to around {round(duration_months + 1)} months.")
        recommendations.append("Start ordering materials earlier to avoid last-minute delays.")

    elif risk == "Medium":
        recommendations.append("Keep weekly progress checks to stay on track.")
        recommendations.append("Consider adding 1–2 extra workers during peak tasks.")

    else:
        recommendations.append("Project plan looks good.")
        recommendations.append("Continue monitoring progress as planned.")

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
