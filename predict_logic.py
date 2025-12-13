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

def _make_features(project_type, project_size, area_m2, duration_months, workers):
    row = pd.DataFrame([{
        "project_type": project_type,
        "project_size": project_size,
        "area_m2": area_m2,
        "duration_months": duration_months,
        "workers": workers
    }])
    row = pd.get_dummies(row)
    return row.reindex(columns=model_columns, fill_value=0)

def _delay_probability(project_type, project_size, area_m2, duration_months, workers):
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)

    proba = delay_model.predict_proba(X)[0]
    delay_index = list(delay_model.classes_).index(1)  # class 1 = delay
    p = float(proba[delay_index]) * 100

    # قواعد واقعية عامة
    if project_size == "Large" and workers <= 3:
        p = max(p, 70.0)
    if project_size == "Medium" and workers <= 2:
        p = max(p, 55.0)

    # قواعد واقعية للكهرباء
    if project_type == "Electrical Works":
        if project_size == "Large" and area_m2 >= 300 and workers <= 6:
            p = max(p, 65.0)
        elif project_size == "Medium" and area_m2 >= 200 and workers <= 4:
            p = max(p, 50.0)

    return min(p, 95.0)

def _risk_level(delay_prob):
    if delay_prob < 30:
        return "Low"
    elif delay_prob < 60:
        return "Medium"
    return "High"

def _find_target_workers(project_type, project_size, area_m2, duration_months, workers, target_prob, max_extra_workers=15):
    for w in range(workers + 1, workers + max_extra_workers + 1):
        p = _delay_probability(project_type, project_size, area_m2, duration_months, w)
        if p <= target_prob:
            return w
    return None

def _find_target_duration(project_type, project_size, area_m2, duration_months, workers, target_prob, max_extra_months=6):
    d = duration_months
    while d <= duration_months + max_extra_months:
        p = _delay_probability(project_type, project_size, area_m2, d, workers)
        if p <= target_prob:
            return round(d, 1)
        d += 0.5
    return None

def _calibrate_cost(project_type, project_size, area_m2, estimated_cost):
    """
    معايرة تكلفة بسيطة لضمان واقعية الأرقام حسب نوع المشروع.
    (بدون مبالغة وبدون أرقام خيالية)
    """
    # إذا ما فيه مساحة (مثل FTTH/شاشات) لا نطبّق معايرة m²
    if area_m2 <= 0:
        return estimated_cost

    # نطاقات تقريبية (SAR لكل m²) — هدفها تمنع الأرقام غير المنطقية مثل 253k لـ 500m² Fit-Out
    if project_type == "Commercial Fit-Out":
        # Medium/Large fit-out عادة أعلى من التشطيبات
        if project_size == "Large":
            min_pm2, max_pm2 = 4200, 7000
        elif project_size == "Medium":
            min_pm2, max_pm2 = 3500, 6000
        else:
            min_pm2, max_pm2 = 2800, 5200

        min_cost = area_m2 * min_pm2
        max_cost = area_m2 * max_pm2
        return max(min_cost, min(estimated_cost, max_cost))

    if project_type == "Building Finishing":
        # تشطيبات أقل
        min_pm2, max_pm2 = 600, 1400
        min_cost = area_m2 * min_pm2
        max_cost = area_m2 * max_pm2
        return max(min_cost, min(estimated_cost, max_cost))

    if project_type == "Residential Construction":
        # إنشاء (تقريبي) — نتركه أوسع
        min_pm2, max_pm2 = 2500, 5500
        min_cost = area_m2 * min_pm2
        max_cost = area_m2 * max_pm2
        return max(min_cost, min(estimated_cost, max_cost))

    if project_type == "Non-Residential Construction":
        min_pm2, max_pm2 = 3000, 6500
        min_cost = area_m2 * min_pm2
        max_cost = area_m2 * max_pm2
        return max(min_cost, min(estimated_cost, max_cost))

    if project_type == "HVAC Installation":
        # (تغطي نفس اللي كنا نسويه)
        min_pm2, max_pm2 = 1800, 4500
        min_cost = area_m2 * min_pm2
        max_cost = area_m2 * max_pm2
        return max(min_cost, min(estimated_cost, max_cost))

    # باقي الأنواع نخليها بدون معايرة (أو نضيف لاحقًا لو لاحظتي شذوذ)
    return estimated_cost

def predict(project_type, project_size, area_m2, duration_months, workers):
    X = _make_features(project_type, project_size, area_m2, duration_months, workers)

    estimated_cost = float(cost_model.predict(X)[0])
    estimated_cost = _calibrate_cost(project_type, project_size, area_m2, estimated_cost)

    delay_prob = _delay_probability(project_type, project_size, area_m2, duration_months, workers)
    risk = _risk_level(delay_prob)

    recommendations = []

    if risk == "Low":
        recommendations.append("وضع المشروع الحالي مستقر. يُنصح بالاستمرار في المتابعة الدورية لضمان الالتزام بالخطة.")
    else:
        w_target = _find_target_workers(project_type, project_size, area_m2, duration_months, workers, 30)
        if w_target:
            diff = w_target - workers
            recommendations.append(f"زيادة عدد العمال بحوالي {diff} عمال قد تساهم في تحسين وتيرة التنفيذ وتقليل الضغط خلال مراحل العمل.")

        d_target = _find_target_duration(project_type, project_size, area_m2, duration_months, workers, 30)
        if d_target and d_target > duration_months:
            recommendations.append(f"تمديد مدة التنفيذ من {duration_months} إلى نحو {d_target} أشهر قد يكون خيارًا أفضل لتقليل احتمالية التأخير.")

        recommendations.append("يُفضل البدء بالأنشطة الحرجة مبكرًا، مثل توريد المواد واعتمادها، لتجنب أي تعطل غير متوقع.")

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": round(delay_prob, 1),
        "risk_level": risk,
        "recommendations": recommendations
    }
