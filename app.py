import streamlit as st
import pandas as pd
from predict_logic import predict

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# ---------------- Styling ----------------
st.markdown("""
<style>
body {background-color:#0e1117;}
.block-container {padding-top:2rem;}

.card {
    background:#161b22;
    padding:20px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,0.08);
}

h1,h2,h3,h4 {color:white;}
label, p {color:#d0d6dc;}

.metric-box {
    background:#0d1b2a;
    padding:16px;
    border-radius:12px;
    text-align:center;
}

.risk-low {color:#2ecc71;}
.risk-medium {color:#f1c40f;}
.risk-high {color:#e74c3c;}
</style>
""", unsafe_allow_html=True)

# ---------------- Session ----------------
if "logs" not in st.session_state:
    st.session_state.logs = []

# ---------------- Sidebar ----------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigate", ["Predict", "Admin"])

PROJECT_TYPES = [
    "Residential Construction",
    "Building Finishing",
    "Commercial Fit-Out",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home Systems",
    "Security Systems"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# ---------------- Predict Page ----------------
if page == "Predict":
    st.title("BuildWise")
    st.caption("Plan smarter. Build with confidence.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 Project Details")

    col1, col2 = st.columns(2)
    with col1:
        project_type = st.selectbox("Project Type", PROJECT_TYPES)
        project_size = st.selectbox("Project Size", PROJECT_SIZES)
        workers = st.number_input("👷 Number of Workers", 1, 300, 10)
    with col2:
        area_m2 = st.number_input("📐 Project Area (m²)", 50, 200000, 300)
        duration = st.number_input("⏳ Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)

    analyze = st.button("🔍 Analyze Project", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze:
        result = predict(project_type, project_size, area_m2, duration, workers)

        risk_class = (
            "risk-low" if result["risk_level"] == "Low"
            else "risk-medium" if result["risk_level"] == "Medium"
            else "risk-high"
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Insights & Results")

        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        c2.metric("Delay Probability", f"{result['delay_probability']}%")
        c3.markdown(f"<h4 class='{risk_class}'>⚠️ {result['risk_level']} Risk</h4>", unsafe_allow_html=True)

        st.subheader("💡 Recommendations")
        for r in result["recommendations"]:
            st.write(f"👉 {r}")

        st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.logs.append({
            "Type": project_type,
            "Size": project_size,
            "Area": area_m2,
            "Duration": duration,
            "Workers": workers,
            "Cost": result["estimated_cost"],
            "Delay %": result["delay_probability"],
            "Risk": result["risk_level"]
        })

# ---------------- Admin Page ----------------
else:
    st.title("🔐 Admin Dashboard")

    password = st.text_input("Admin Password", type="password")
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")

    if password != ADMIN_PASSWORD:
        st.warning("Enter the admin password to continue.")
        st.stop()

    st.success("Access granted ✔️")

    df = pd.DataFrame(st.session_state.logs)
    if df.empty:
        st.info("No predictions yet.")
    else:
        st.dataframe(df, use_container_width=True)
