import joblib
import pandas as pd

# Load models + columns
cost_model = joblib.load("cost_model.pkl")
delay_model = joblib.load("delay_model.pkl")
model_columns = joblib.load("model_columns.pkl")

def _build_features(project_type, project_size, area_m2, duration_months, workers):
    # Create empty row with training columns
    X = pd.DataFrame([{c: 0 for c in model_columns}])

    # Fill numeric columns if they exist
    for col, val in {
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }.items():
        if col in X.columns:
            X.at[0, col] = val

    # One-hot for categories (handles different training column naming)
    candidates = [
        f"project_type_{project_type}",
        f"project_type__{project_type}",
        f"project_type={project_type}",
        project_type,  # fallback if training used raw strings as columns (rare)
    ]
    for c in candidates:
        if c in X.columns:
            X.at[0, c] = 1
            break

    candidates = [
        f"project_size_{project_size}",
        f"project_size__{project_size}",
        f"project_size={project_size}",
        project_size,
    ]
    for c in candidates:
        if c in X.columns:
            X.at[0, c] = 1
            break

    return X

def _risk_level(delay_prob):
    if delay_prob >= 60:
        return "High"
    if delay_prob >= 30:
        return "Medium"
    return "Low"

def _recommendations(risk, duration_months, workers):
    recs = []

    if risk == "High":
        recs.append("Add schedule buffer and split tasks into weekly milestones.")
        if workers < 10:
            recs.append("Increase workforce or add a backup crew for peak activities.")
        if duration_months < 2:
            recs.append("Extend duration to reduce schedule pressure and rework risk.")
        recs.append("Prioritize long-lead items early (materials, approvals, permits).")

    elif risk == "Medium":
        recs.append("Monitor progress weekly and prepare contingency for delays.")
        recs.append("Confirm supplier timelines and lock key materials early.")

    else:
        recs.append("Plan looks stable. Keep monthly monitoring and quality checks.")

    return recs

def predict(project_type, project_size, area_m2, duration_months, workers):
    X = _build_features(project_type, project_size, area_m2, duration_months, workers)

    est_cost = float(cost_model.predict(X)[0])
    delay_prob = float(delay_model.predict_proba(X)[0][1] * 100)

    risk = _risk_level(delay_prob)
    recs = _recommendations(risk, duration_months, workers)

    return {
        "estimated_cost": round(est_cost, 2),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recs
    }
