import joblib
import numpy as np

# Load models safely
cost_model = joblib.load("cost_model.pkl")
delay_model = joblib.load("delay_model.pkl")
model_columns = joblib.load("model_columns.pkl")

def predict(project_type, project_size, area_m2, duration_months, workers):
    # Build input row
    data = {
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }

    for col in model_columns:
        if col.startswith("project_type_"):
            data[col] = 1 if col == f"project_type_{project_type}" else 0
        elif col.startswith("project_size_"):
            data[col] = 1 if col == f"project_size_{project_size}" else 0

    X = np.array([[data.get(col, 0) for col in model_columns]])

    estimated_cost = float(cost_model.predict(X)[0])
    delay_probability = float(delay_model.predict(X)[0])

    # Risk level
    if delay_probability < 30:
        risk = "Low"
    elif delay_probability < 60:
        risk = "Medium"
    else:
        risk = "High"

    # Friendly recommendations
    recommendations = []
    if risk == "High":
        recommendations = [
            "Try adding a small time buffer — it gives the team breathing room ⏱️",
            "If possible, add 1–2 extra workers during busy phases 👷",
            "Ordering materials early can save a lot of stress later 📦",
            "Breaking tasks into weekly goals helps keep things on track ✅"
        ]
    elif risk == "Medium":
        recommendations = [
            "A short buffer in the schedule could improve stability 👍",
            "Double-check supplier timelines to avoid surprises 📋",
            "Weekly check-ins help catch issues early 🔍"
        ]
    else:
        recommendations = [
            "Your plan looks solid — keep monitoring progress 👌",
            "Stick to the schedule and document changes 🗂️"
        ]

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_probability, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
