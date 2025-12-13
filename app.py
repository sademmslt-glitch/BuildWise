import time
import pandas as pd
import streamlit as st
from predict_logic import predict

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# --------------------------------------------------
# Clean & Construction-themed UI
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

body {
    background-color: #0f172a;
    color: #e5e7eb;
}

h1, h2, h3 {
    font-weight: 700;
}

.card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 24px;
}

.label {
    font-size: 0.85rem;
    color: #94a3b8;
}

.metric-box {
    background: #020617;
    border-radius: 14px;
    padding: 16px;
    text-align: center;
}

.badge {
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
}

.badge-low {background: rgba(34,197,94,0.15); color:#22c55e;}
.badge-med {background: rgba(251,191,36,0.15); color:#fbbf24;}
.badge-high{background: rgba(239,68,68,0.15); color:#ef4444;}

.reco {
    background: #020617;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Session State (Admin Logs)
# --------------------------------------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigate", ["📊 Predict", "🔐 Admin"])

PROJECT_TYPES = [
    "Residential Construction",
    "Commercial Building",
    "Building Finishing",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home Systems",
    "Security Systems",
    "FTTH Infrastructure",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# --------------------------------------------------
# Predict Page
# --------------------------------------------------
if page == "📊 Predict":

    st.markdown("## BuildWise")
    st.markdown("🧠 *Plan smarter. Build with confidence.*")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🏗️ Project Details")

    col1, col2 = st.columns(2)

    with col1:
        project_type = st.selectbox("🏢 Project Type", PROJECT_TYPES)
        project_size = st.selectbox("📐 Project Size", PROJECT_SIZES)
        workers = st.number_input("👷 Number of Workers", 1, 500, 10)

    with col2:
        area_m2 = st.number_input("📏 Project Area (m²)", 50, 200000, 300, step=50)
        duration_months = st.number_input("🗓️ Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)

    analyze = st.button("🔍 Analyze Project", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze:
        with st.spinner("Analyzing your project..."):
            time.sleep(0.5)
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        risk = result["risk_level"]
        badge = "badge-low" if risk == "Low" else "badge-med" if risk == "Medium" else "badge-high"

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📊 Insights & Results")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("💰 Estimated Cost")
            st.markdown(f"### {result['estimated_cost']:,.0f} SAR")
        with c2:
            st.markdown("⏱️ Delay Probability")
            st.markdown(f"### {result['delay_probability']}%")
        with c3:
            st.markdown("⚠️ Risk Level")
            st.markdown(f"<span class='badge {badge}'>{risk}</span>", unsafe_allow_html=True)

        st.markdown("### 🧩 Suggestions to Consider")
        for r in result["recommendations"]:
            st.markdown(f"<div class='reco'>• {r}</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Save for Admin
        st.session_state.logs.append({
            "time": pd.Timestamp.now(),
            "type": project_type,
            "size": project_size,
            "area": area_m2,
            "duration": duration_months,
            "workers": workers,
            "risk": risk
        })

# --------------------------------------------------
# Admin Page
# --------------------------------------------------
else:
    st.markdown("## 🔐 Admin Dashboard")

    password = st.text_input("Admin Password", type="password")
    if password != "buildwise123":
        st.info("Enter admin password to continue.")
        st.stop()

    st.success("Access granted")

    logs = pd.DataFrame(st.session_state.logs)
    if logs.empty:
        st.warning("No predictions yet.")
    else:
        st.dataframe(logs.tail(10), use_container_width=True)
