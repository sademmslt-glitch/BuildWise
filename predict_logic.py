import pandas as pd
import joblib
import streamlit as st

# =================================================
# Load models (cached for performance)
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
# Delay probability with domain realism rules
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
# Helpers to find realistic improvement options
# =================================================
def _find_target_workers(
    project_type, project_size, area_m2, duration_months, workers,
    target_prob, max_extra_workers=15
):
    for w in range(workers + 1, workers + max_extra_workers + 1):
        p = _delay_probability(project_type, project_size, area_m2, duration_months, w)
        if p <= target_prob:
            return w
    return None


def _find_target_duration(
    project_type, project_size, area_m2, duration_months, workers,
    target_prob, max_extra_months=6
):
    d = duration_months
    while d <= duration_months + max_extra_months:
        p = _delay_probability(project_type, project_size, area_m2, d, workers)
        if p <= target_prob:
            return round(d, 1)
        d += 0.5
    return None

# =================================================
# Main prediction function
# =================================================
def predict(project_type, project_size, area_m2, duration_months, workers):

    # ---------- Cost prediction ----------
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)
    estimated_cost = float(cost_model.predict(X)[0])

    # Optional HVAC calibration
    if project_type == "HVAC Installation":
        min_cost = area_m2 * 1800
        max_cost = area_m2 * 4500
        estimated_cost = max(min_cost, min(estimated_cost, max_cost))

    # ---------- Delay & risk ----------
    delay_prob = _delay_probability(
        project_type, project_size, area_m2, duration_months, workers
    )
    risk = _risk_level(delay_prob)

    # ---------- Professional recommendations ----------
    recommendations = []

    if risk == "Low":
        recommendations.append(
            "وضع المشروع الحالي مستقر، ولا توجد مؤشرات واضحة على خطر التأخير. يُنصح بالاستمرار في المتابعة الدورية."
        )

    else:
        # اقتراح العمال
        w_target = _find_target_workers(
            project_type, project_size, area_m2, duration_months, workers, 30
        )
        if w_target:
            diff = w_target - workers
            recommendations.append(
                f"زيادة عدد العمال بحوالي {diff} عمال قد تساهم في تحسين وتيرة التنفيذ وتقليل الضغط خلال مراحل العمل."
            )

        # اقتراح المدة
        d_target = _find_target_duration(
            project_type, project_size, area_m2, duration_months, workers, 30
        )
        if d_target and d_target > duration_months:
            recommendations.append(
                f"تمديد مدة التنفيذ من {duration_months} إلى نحو {d_target} أشهر قد يكون خيارًا أفضل لتقليل مخاطر التأخير."
            )

        # توصية إدارية واحدة فقط
        recommendations.append(
            "يُفضل البدء بالأنشطة الحرجة مبكرًا، مثل توريد المواد والحصول على الموافقات، لتجنب أي تعطل غير متوقع."
        )

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
