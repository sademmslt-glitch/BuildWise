import pickle
import numpy as np

# Load models
cost_model = pickle.load(open("cost_model.pkl", "rb"))
delay_model = pickle.load(open("delay_model.pkl", "rb"))
columns = pickle.load(open("model_columns.pkl", "rb"))

def predict(project_type, project_size, area, duration, workers):

    x = np.zeros(len(columns))
    x[columns.index("area_m2")] = area
    x[columns.index("duration_months")] = duration
    x[columns.index("workers")] = workers

    if f"type_{project_type}" in columns:
        x[columns.index(f"type_{project_type}")] = 1

    if f"size_{project_size}" in columns:
        x[columns.index(f"size_{project_size}")] = 1

    estimated_cost = float(cost_model.predict([x])[0])
    delay_prob = round(float(delay_model.predict_proba([x])[0][1]) * 100, 1)

    if delay_prob < 30:
        risk = "Low"
    elif delay_prob < 60:
        risk = "Medium"
    else:
        risk = "High"

    recommendations = []

    if risk == "High":
        recommendations = [
            "Adding a little extra time to the schedule could reduce pressure later on.",
            "You might consider increasing the workforce during busy phases.",
            "Ordering materials early can help avoid unexpected waiting.",
            "Breaking the project into smaller milestones may make tracking easier."
        ]
    elif risk == "Medium":
        recommendations = [
            "The plan looks reasonable, but keeping a small time buffer could help.",
            "Regular progress checks may prevent minor delays from growing."
        ]
    else:
        recommendations = [
            "The project setup looks balanced.",
            "Just keep monitoring progress as work moves forward."
        ]

    return {
        "estimated_cost": estimated_cost,
        "delay_probability": delay_prob,
        "risk_level": risk,
        "recommendations": recommendations
    }
