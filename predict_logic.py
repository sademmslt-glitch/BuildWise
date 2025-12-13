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
# Helpers
# -------------------------------------------------
def _make_features(project_type, project_size, area_m2, duration_months, workers):
    row = pd.DataFrame([{
        "project_type": project_type,
        "project_size": project_size,
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }])
    row = pd.get_dummies(row)
    row = row.reindex(columns=model_columns, fill_value=0)
    return row


def _delay_probability(project_type, project_size, area_m2, duration_months, workers):
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)

    # Correct probability index for class=1 (Delay)
    proba = delay_model.predict_proba(X)[0]
    classes = delay_model.classes_
    delay_index = list(classes).index(1)
    p = float(proba[delay_index]) * 100

    # Realism layer (edge cases)
    if project_size == "Large" and area_m2 >= 400 and workers <= 3:
        p = max(p, 75.0)
    if project_size == "Medium" and area_m2 >= 250 and workers <= 2:
        p = max(p, 60.0)

    return p


def _risk_level(delay_prob):
    if delay_prob < 30:
        return "Low"
    elif delay_prob < 60:
        return "Medium"
    else:
        return "High"


def _find_target_workers(project_type, project_size, area_m2, duration_months, workers, target_prob, max_add=60):
    """
    Find the smallest workers number that reaches delay_probability <= target_prob
    """
    for w in range(workers, workers + max_add + 1):
        p = _delay_probability(project_type, project_size, area_m2, duration_months, w)
        if p <= target_prob:
            return w, p
    return None, None


def _find_target_duration(project_type, project_size, area_m2, duration_months, workers, target_prob, max_add_months=12, step=0.5):
    """
    Find the smallest duration that reaches delay_probability <= target_prob
    """
    d = duration_months
    end = duration_months + max_add_months
    while d <= end:
        p = _delay_probability(project_type, project_size, area_m2, d, workers)
        if p <= target_prob:
            return round(d, 1), p
        d += step
    return None, None


# -------------------------------------------------
# Main function
# -------------------------------------------------
def predict(project_type, project_size, area_m2, duration_months, workers):

    # ---------------- Cost prediction ----------------
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)
    estimated_cost = float(cost_model.predict(X)[0])

    # Optional HVAC calibration (prevents crazy values)
    if project_type == "HVAC Installation":
        min_cost = area_m2 * 1800
        max_cost = area_m2 * 4500
        estimated_cost = max(min_cost, min(estimated_cost, max_cost))

    # ---------------- Delay probability ----------------
    delay_prob = _delay_probability(project_type, project_size, area_m2, duration_months, workers)
    risk = _risk_level(delay_prob)

    # ---------------- Smart recommendations (Precise) ----------------
    # Goal: if Medium/High, propose changes that actually push the risk down.
    recommendations = []

    # Determine the next better target:
    # - If High -> aim for <= 55% first (down to Medium), and offer option for <= 30% (Low)
    # - If Medium -> aim for <= 30% (Low)
    if risk == "Low":
        recommendations.append("خطتك حلوة 👍 كمّلي نفس الأسلوب وراقبي التقدم أسبوعيًا.")
    else:
        if risk == "High":
            target_probs = [55, 30]   # first to Medium, then to Low
        else:
            target_probs = [30]       # Medium -> Low

        # Build two-option recommendations per target (workers OR duration)
        for tp in target_probs:
            w_target, w_newprob = _find_target_workers(project_type, project_size, area_m2, duration_months, workers, tp)
            d_target, d_newprob = _find_target_duration(project_type, project_size, area_m2, duration_months, workers, tp)

            # If both found, present both as choices (user-friendly)
            if w_target is not None and d_target is not None:
                # choose the "lighter" change to highlight first
                add_w = w_target - workers
                add_d = d_target - duration_months
                if add_w <= 5:
                    first = f"لو تبين ينزل الخطر لـ {tp}% تقريبًا: زوّدي العمال إلى {w_target} (يعني +{add_w})."
                    second = f"أو بديل ثاني: زوّدي المدة إلى {d_target} شهر تقريبًا."
                else:
                    first = f"لو تبين ينزل الخطر لـ {tp}% تقريبًا: زوّدي المدة إلى {d_target} شهر."
                    second = f"أو بديل ثاني: زوّدي العمال إلى {w_target} (يعني +{add_w})."

                recommendations.append(first)
                recommendations.append(second)

            elif w_target is not None:
                add_w = w_target - workers
                recommendations.append(f"عشان ينزل الخطر لـ {tp}% تقريبًا: زوّدي العمال إلى {w_target} (يعني +{add_w}).")

            elif d_target is not None:
                recommendations.append(f"عشان ينزل الخطر لـ {tp}% تقريبًا: زوّدي المدة إلى {d_target} شهر.")

            else:
                # fallback if model can't reach target within search limits
                recommendations.append(f"لتقليل الخطر بشكل واضح: زوّدي العمال أو المدة (التغيير البسيط قد لا يكفي هنا).")

        # Always include one practical tip for execution
        recommendations.append("نصيحة سريعة: رتّبي التوريد والموافقات بدري (هذي أكثر شي يسبب تأخير).")

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
