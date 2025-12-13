import pandas as pd
import joblib
import streamlit as st

# =================================================
# Load models (cached for speed)
# =================================================
@st.cache_resource
def load_models():
    cost_model = joblib.load("cost_model.pkl")
    delay_model = joblib.load("delay_model.pkl")
    model_columns = joblib.load("model_columns.pkl")
    return cost_model, delay_model, model_columns

cost_model, delay_model, model_columns = load_models()

# =================================================
# Feature preparation
# =================================================
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

# =================================================
# Delay probability with realism rules
# =================================================
def _delay_probability(project_type, project_size, area_m2, duration_months, workers):
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)

    proba = delay_model.predict_proba(X)[0]
    delay_index = list(delay_model.classes_).index(1)
    p = float(proba[delay_index]) * 100

    # -------- General realism rules --------
    if project_size == "Large" and workers <= 3:
        p = max(p, 70.0)

    if project_size == "Medium" and workers <= 2:
        p = max(p, 55.0)

    # -------- Electrical Works specific rules --------
    if project_type == "Electrical Works":
        if project_size == "Large" and area_m2 >= 300 and workers <= 6:
            p = max(p, 65.0)
        elif project_size == "Medium" and area_m2 >= 200 and workers <= 4:
            p = max(p, 50.0)

    return min(p, 95.0)

# =================================================
# Risk level
# =================================================
def _risk_level(delay_prob):
    if delay_prob < 30:
        return "Low"
    elif delay_prob < 60:
        return "Medium"
    else:
        return "High"

# =================================================
# Smart recommendation helpers (bounded & realistic)
# =================================================
def _find_target_workers(
    project_type, project_size, area_m2, duration_months, workers,
    target_prob, max_extra_workers=15
):
    max_workers = workers + max_extra_workers

    for w in range(workers + 1, max_workers + 1):
        p = _delay_probability(project_type, project_size, area_m2, duration_months, w)
        if p <= target_prob:
            return w, p
    return None, None


def _find_target_duration(
    project_type, project_size, area_m2, duration_months, workers,
    target_prob, max_extra_months=6
):
    d = duration_months
    end = duration_months + max_extra_months

    while d <= end:
        p = _delay_probability(project_type, project_size, area_m2, d, workers)
        if p <= target_prob:
            return round(d, 1), p
        d += 0.5

    return None, None

# =================================================
# Main prediction function
# =================================================
def predict(project_type, project_size, area_m2, duration_months, workers):

    # ---------- Cost prediction ----------
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)
    estimated_cost = float(cost_model.predict(X)[0])

    # Optional calibration for HVAC
    if project_type == "HVAC Installation":
        min_cost = area_m2 * 1800
        max_cost = area_m2 * 4500
        estimated_cost = max(min_cost, min(estimated_cost, max_cost))

    # ---------- Delay & risk ----------
    delay_prob = _delay_probability(
        project_type, project_size, area_m2, duration_months, workers
    )
    risk = _risk_level(delay_prob)

    # ---------- Recommendations (formal & effective) ----------
    recommendations = []

    if risk == "Low":
        recommendations.append(
            "خطة المشروع الحالية مناسبة. استمر في المتابعة الدورية لضمان الالتزام بالجدول الزمني."
        )

    else:
        # Targets
        targets = [30] if risk == "Medium" else [55, 30]

        for tp in targets:
            w_target, _ = _find_target_workers(
                project_type, project_size, area_m2, duration_months, workers, tp
            )
            d_target, _ = _find_target_duration(
                project_type, project_size, area_m2, duration_months, workers, tp
            )

            if w_target and d_target:
                recommendations.append(
                    f"لخفض خطر التأخير إلى مستوى أقرب للاستقرار، يمكنك زيادة عدد العمال إلى حوالي {w_target} عامل "
                    f"أو تمديد مدة المشروع إلى نحو {d_target} أشهر."
                )
            elif w_target:
                recommendations.append(
                    f"لخفض خطر التأخير، يُوصى بزيادة عدد العمال إلى حوالي {w_target} عامل خلال مراحل الذروة."
                )
            elif d_target:
                recommendations.append(
                    f"لخفض خطر التأخير، يُوصى بتمديد مدة المشروع إلى نحو {d_target} أشهر لتقليل ضغط الجدول الزمني."
                )

        recommendations.append(
            "كما يُنصح ببدء الأنشطة الحرجة مبكرًا، مثل توريد المواد والموافقات، لتقليل احتمالية التعثر أثناء التنفيذ."
        )

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
