import joblib
import pandas as pd

# Load models safely
cost_model = joblib.load("cost_model.pkl")
delay_model = joblib.load("delay_model.pkl")
model_columns = joblib.load("model_columns.pkl")

def predict(project_type, project_size, area_m2, duration_months, workers):
    # Prepare input as DataFrame
    input_dict = {
        "project_type": project_type,
        "project_size": project_size,
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers,
    }

    df = pd.DataFrame([input_dict])

    # One-hot encoding
    df = pd.get_dummies(df)

    # Align with training columns
    df = df.reindex(columns=model_columns, fill_value=0)

    # Predictions
    estimated_cost = float(cost_model.predict(df)[0])
    delay_probability = float(delay_model.predict(df)[0])

    # Risk level logic
    if delay_probability < 30:
        risk = "Low"
    elif delay_probability < 60:
        risk = "Medium"
    else:
        risk = "High"

    # Friendly recommendations (غير رسمية)
    recommendations = []

    if risk == "High":
        recommendations = [
            "Try adding a small buffer to the schedule — it can reduce pressure a lot.",
            "Having a backup crew during busy phases might really help.",
            "Ordering materials early can save you last-minute stress.",
        ]
    elif risk == "Medium":
        recommendations = [
            "The plan looks okay, but keeping weekly check-ins is a smart move.",
            "Make sure key tasks don’t overlap too much.",
        ]
    else:
        recommendations = [
            "Everything looks smooth so far — just keep tracking progress regularly.",
            "A quick weekly review should be enough to stay on track.",
        ]

    return {
        "estimated_cost": round(estimated_cost, 2),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk,
        "recommendations": recommendations,
    }
