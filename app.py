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
# Clean Dark UI Styling (No white glare)
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 900px;
}
.card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
}
.soft-text {
    color: #9ca3af;
    font-size: 0.9rem;
}
.badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
}
.badge-low {
    background: rgba(16,185,129,0.15);
    color: #10b981;
}
.badge-med {
    background: rgba(245,158,11,0.15);
    color: #f59e0b;
}
.badge-high {
    background: rgba(239,68,68,0.15);
    color: #ef4444;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Session storage for Admin
# --------------------------------------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------
st.sidebar.title("BuildWise")
page = st.sidebar.radio("Navigate", ["Predict", "Admin"])

# --------------------------------------------------
# Dropdown Values
# --------------------------------------------------
PROJECT_TYPES = [
    "Residential Construction",
    "Non-Residential Construction",
    "Building Finishing",
    "Commercial Fit-Out",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home Systems",
    "Security Systems",
    "FTTH Infrastructure",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# ==================================================
# PREDICTION PAGE
# ==================================================
if page == "Predict":

    st.title("BuildWise")
    st.caption("Plan smarter. Build with confidence.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Project Details")
    st.markdown('<p class="soft-text">Just a few inputs — we’ll handle the thinking.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        project_type = st.selectbox("Project Type", PROJECT_TYPES)
        project_size = st.selectbox("Project Size", PROJECT_SIZES)
        workers = st.number_input(
            "Number of Workers",
            min_value=1,
            max_value=500,
            value=15,
            step=1
        )

    with col2:
        area_m2 = st.number_input(
            "Project Area (m²)",
            min_value=50,
            max_value=200000,
            value=250,
            step=25
        )
        duration_months = st.number_input(
            "Expected Duration (months)",
            min_value=0.5,
            max_value=60.0,
            value=3.0,
            step=0.5
        )

    analyze = st.button("Analyze Project", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------
    # Results
    # -------------------------------
    if analyze:
        with st.spinner("Analyzing project risks and costs..."):
            time.sleep(0.5)
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        risk = result["risk_level"]
        badge_class = (
            "badge-low" if risk == "Low"
            else "badge-med" if risk == "Medium"
            else "badge-high"
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Insights & Results")

        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        c2.metric("Delay Probability", f"{result['delay_probability']}%")
        c3.markdown(
            f'<span class="badge {badge_class}">Risk Level: {risk}</span>',
            unsafe_allow_html=True
        )

        st.markdown("### Friendly Recommendations")
        for r in result["recommendations"]:
            st.write(f"👉 {r}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Save log
        st.session_state.logs.append({
            "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "type": project_type,
            "size": project_size,
            "area": area_m2,
            "duration": duration_months,
            "workers": workers,
            "cost": result["estimated_cost"],
            "delay": result["delay_probability"],
            "risk": risk
        })

# ==================================================
# ADMIN PAGE
# ==================================================
else:
    st.title("Admin Dashboard")
    st.caption("Internal view for monitoring system usage.")

    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")
    entered = st.text_input("Admin Password", type="password")

    if entered != ADMIN_PASSWORD:
        st.info("Please enter the admin password.")
        st.stop()

    st.success("Welcome back 👋")

    logs = st.session_state.logs

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Usage Overview")

    total = len(logs)
    high = sum(1 for x in logs if x["risk"] == "High")
    med = sum(1 for x in logs if x["risk"] == "Medium")
    low = sum(1 for x in logs if x["risk"] == "Low")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Predictions", total)
    c2.metric("High Risk", high)
    c3.metric("Medium Risk", med)
    st.caption(f"Low Risk: {low}")

    st.markdown('</div>', unsafe_allow_html=True)

    if total > 0:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Recent Predictions")
        st.dataframe(pd.DataFrame(logs).tail(10), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
