import pickle
import numpy as np

# -------------------------------
# Load models
# -------------------------------
cost_model = pickle.load(open("cost_model.pkl", "rb"))
delay_model = pickle.load(open("delay_model.pkl", "rb"))
model_columns = pickle.load(open("model_columns.pkl", "rb"))

# -------------------------------
# Helper functions
# -------------------------------
def calculate_pressure(area, workers, duration):
    return (area / max(workers, 1)) / max(duration, 0.5)

def classify_risk(delay_prob):
    if delay_prob < 30:
        return "Low"
    elif delay_prob < 55:
        return "Medium"
    else:
        return "High"

def generate_recommendations(area, workers, duration, risk):
    recs = []

    # قيم تقريبية شائعة في مشاريع مشابهة
    ideal_workers = max(5, int(area / 40))
    ideal_duration = max(1.5, area / 120)

    if risk == "High":
        if workers < ideal_workers:
            recs.append(
                f"عدد العمال الحالي أقل من المعتاد لمشاريع بهذا الحجم. رفع العدد بشكل تدريجي ليكون قريب من {ideal_workers} عامل قد يساعد في تخفيف ضغط العمل."
            )

        if duration < ideal_duration:
            recs.append(
                f"مدة التنفيذ الحالية تبدو قصيرة نسبيًا. لو كانت المدة بين {round(ideal_duration,1)} و {round(ideal_duration+1,1)} أشهر قد يكون التنفيذ أسهل وأكثر استقرارًا."
            )

        recs.append(
            "من الأفضل ترتيب الأعمال الأساسية مبكرًا مثل توريد المواد والموافقات لتجنب أي تأخير غير متوقع."
        )

    elif risk == "Medium":
        recs.append(
            "الوضع الحالي مقبول، لكن المتابعة المنتظمة تساعد في اكتشاف أي ضغط قبل أن يتحول إلى تأخير فعلي."
        )

        if workers < ideal_workers:
            recs.append(
                "إذا لاحظت ضغط في الجدول، دعم الفريق بعدد بسيط من العمال خلال المراحل المهمة قد يعطي مرونة أفضل."
            )

    else:
        recs.append(
            "الخطة الحالية متوازنة بشكل عام. الاستمرار بنفس الترتيب مع متابعة دورية يكفي للحفاظ على سير المشروع."
        )

    return recs

# -------------------------------
# Main prediction function
# -------------------------------
def predict(project_type, project_size, area_m2, duration_months, workers):

    # --------- Cost Prediction ---------
    X_cost = np.zeros(len(model_columns))
    for i, col in enumerate(model_columns):
        if col == "area_m2":
            X_cost[i] = area_m2
        elif col == "duration_months":
            X_cost[i] = duration_months
        elif col == "workers":
            X_cost[i] = workers
        elif col == f"project_type_{project_type}":
            X_cost[i] = 1
        elif col == f"project_size_{project_size}":
            X_cost[i] = 1

    estimated_cost = float(cost_model.predict([X_cost])[0])

    # --------- Delay Prediction (Hybrid) ---------
    base_delay = float(delay_model.predict_proba([X_cost])[0][1] * 100)

    pressure = calculate_pressure(area_m2, workers, duration_months)

    # تعديل النسبة بناءً على ضغط المشروع
    if pressure > 12:
        adjusted_delay = max(base_delay, 60 + (pressure - 12) * 2)
    elif pressure > 8:
        adjusted_delay = max(base_delay, 40 + (pressure - 8) * 2)
    else:
        adjusted_delay = min(base_delay, 25)

    delay_probability = round(min(adjusted_delay, 90), 1)
    risk_level = classify_risk(delay_probability)

    # --------- Recommendations ---------
    recommendations = generate_recommendations(
        area_m2, workers, duration_months, risk_level
    )

    return {
        "estimated_cost": estimated_cost,
        "delay_probability": delay_probability,
        "risk_level": risk_level,
        "recommendations": recommendations
    }
