import time
import pandas as pd
import streamlit as st
from predict_logic import predict

# ----------------------------
# App Branding
# ----------------------------
st.set_page_config(page_title="BuildWise", page_icon="🏗️", layout="centered")

# Simple CSS for a clean "product" feel
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.card {border:1px solid rgba(0,0,0,0.08); border-radius:16px; padding:16px; background:#ffffff;}
.badge {display:inline-block; padding:6px 10px; border-radius:999px; font-weight:600; font-size:0.9rem;}
.badge-low {background:#eaf7ee; color:#1b7a3a;}
.badge-med {background:#fff6e6; color:#a15c00;}
.badge-high{background:#ffeaea; color:#a10000;}
.small {opacity:0.75; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Session storage (for Admin)
# ----------------------------
if "logs" not in st.session_state:
    st.session_state.logs = []  # each item: dict

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title("BuildWise")
page = st.sidebar.radio("Navigate", ["Predict", "Admin"])

# Project types aligned with your company activities
PROJECT_TYPES = [
    "Residential Construction",
    "Non-Residential Construction",
    "Building Finishing",
    "Commercial Fit-Out",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home System",
    "Security Systems",
    "FTTH Infrastructure",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# ----------------------------
# Predict Page
# ----------------------------
if page == "Predict":
    st.title("BuildWise")
    st.caption("Smart insights for confident construction planning.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Project Inputs")

    col1, col2 = st.columns(2)
    with col1:
        project_type = st.selectbox("Project Type", PROJECT_TYPES)
        project_size = st.selectbox("Project Size", PROJECT_SIZES)
        workers = st.number_input("Workers", min_value=1, max_value=500, value=20, step=1)
    with col2:
        area_m2 = st.number_input("Area (m²)", min_value=0, max_value=200000, value=250, step=10)
        duration_months = st.number_input("Expected Duration (months)", min_value=0.5, max_value=60.0, value=3.0, step=0.5)
        st.write("")

    analyze = st.button("Analyze", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze:
        with st.spinner("Analyzing..."):
            time.sleep(0.4)
            result = predict(project_type, project_size, area_m2, duration_months, workers)

        # Risk badge
        risk = result["risk_level"]
        badge_class = "badge-low" if risk == "Low" else ("badge-med" if risk == "Medium" else "badge-high")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Results")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        with c2:
            st.metric("Delay Probability", f"{result['delay_probability']}%")
        with c3:
            st.markdown(f'<span class="badge {badge_class}">Risk: {risk}</span>', unsafe_allow_html=True)

        st.markdown("### Recommendations")
        for r in result["recommendations"]:
            st.write(f"• {r}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Save a log for Admin view
        st.session_state.logs.append({
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_type": project_type,
            "project_size": project_size,
            "area_m2": area_m2,
            "duration_months": duration_months,
            "workers": workers,
            "estimated_cost": result["estimated_cost"],
            "delay_probability": result["delay_probability"],
            "risk_level": risk,
        })

# ----------------------------
# Admin Page
# ----------------------------
else:
    st.title("Admin")
    st.caption("Internal dashboard for monitoring predictions.")

    # Simple password gate (for demo)
    # الأفضل: تحطينه في Streamlit Secrets باسم ADMIN_PASSWORD
    DEFAULT_ADMIN_PASSWORD = "buildwise123"

    entered = st.text_input("Admin Password", type="password")
    admin_password = st.secrets.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    if entered != admin_password:
        st.info("Enter the admin password to view dashboard.")
        st.stop()

    logs = st.session_state.logs
    st.success("Access granted ✅")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Overview")

    total = len(logs)
    high = sum(1 for x in logs if x["risk_level"] == "High")
    med = sum(1 for x in logs if x["risk_level"] == "Medium")
    low = sum(1 for x in logs if x["risk_level"] == "Low")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Predictions", total)
    c2.metric("High Risk", high)
    c3.metric("Medium Risk", med)

    st.caption(f"Low Risk: {low}")
    st.markdown('</div>', unsafe_allow_html=True)

    if total > 0:
        df = pd.DataFrame(logs)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Recent Predictions")
        st.dataframe(df.tail(10), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No predictions yet. Go to Predict page and run a test.")
