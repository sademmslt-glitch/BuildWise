import time
import streamlit as st
import pandas as pd
from predict_logic import predict

# --------------------
# Page config
# --------------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# --------------------
# CSS Styling (خففنا التباين)
# --------------------
st.markdown("""
<style>
body {background-color:#0f172a;}
.card {
    background:#111827;
    padding:20px;
    border-radius:16px;
    margin-bottom:16px;
}
h1, h2, h3, p, label {
    color:#e5e7eb;
}
.stButton>button {
    background:#2563eb;
    color:white;
    border-radius:10px;
    height:3em;
}
.badge {
    padding:6px 14px;
    border-radius:999px;
    font-weight:600;
}
.low {background:#064e3b; color:#a7f3d0;}
.medium {background:#78350f; color:#fde68a;}
.high {background:#7f1d1d; color:#fecaca;}
</style>
""", unsafe_allow_html=True)

# --------------------
# Session state for admin logs
# --------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

# --------------------
# Sidebar
# --------------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigation", ["Project Analysis", "Admin Panel"])

PROJECT_TYPES = [
    "Residential Construction",
    "Commercial Construction",
    "Building Finishing",
    "Smart Home Systems",
    "Electrical Works",
    "HVAC Installation",
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# =====================================================
# MAIN USER PAGE
# =====================================================
if page == "Project Analysis":

    st.title("BuildWise")
    st.caption("Plan smarter. Build with confidence.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 Project Details")

    col1, col2 = st.columns(2)

    with col1:
        project_type = st.selectbox("Project Type", PROJECT_TYPES)
        project_size = st.selectbox("Project Size", PROJECT_SIZES)
        workers = st.number_input("👷 Number of Workers", 1, 500, 10)

    with col2:
        area_m2 = st.number_input("📐 Project Area (m²)", 50, 200000, 300, step=50)
        duration_months = st.number_input("⏳ Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)

    analyze = st.button("Analyze Project 🚀", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze:
        with st.spinner("Analyzing your project..."):
            time.sleep(0.6)
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        risk_class = "low" if result["risk_level"] == "Low" else \
                     "medium" if result["risk_level"] == "Medium" else "high"

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Insights & Results")

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        c2.metric("⏱️ Delay Probability", f"{result['delay_probability']}%")
        c3.markdown(
            f"<span class='badge {risk_class}'>Risk: {result['risk_level']}</span>",
            unsafe_allow_html=True
        )

        st.subheader("💡 Recommendations")
        for rec in result["recommendations"]:
            st.write(f"• {rec}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Save for admin
        st.session_state.logs.append({
            "Project Type": project_type,
            "Size": project_size,
            "Area": area_m2,
            "Duration": duration_months,
            "Workers": workers,
            "Risk": result["risk_level"]
        })

# =====================================================
# ADMIN PANEL
# =====================================================
else:
    st.title("🔐 Admin Panel")

    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")

    password = st.text_input("Enter Admin Password", type="password")

    if password != ADMIN_PASSWORD:
        st.warning("Access restricted.")
        st.stop()

    st.success("Welcome, Admin ✅")

    logs = st.session_state.logs

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Usage Overview")

    st.metric("Total Analyses", len(logs))

    if logs:
        df = pd.DataFrame(logs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No project analyses yet.")

    st.markdown('</div>', unsafe_allow_html=True)
