import streamlit as st
import pandas as pd
from predict_logic import predict

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# --------------------------------------------------
# Session state for Admin logs
# --------------------------------------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigation", ["Project Analysis", "Admin"])

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

# ==================================================
# USER PAGE
# ==================================================
if page == "Project Analysis":

    st.title("BuildWise")
    st.caption("Smart insights for confident construction planning.")

    st.subheader("Project Details")

    project_type = st.selectbox("Project Type", PROJECT_TYPES)
    project_size = st.selectbox("Project Size", PROJECT_SIZES)
    area_m2 = st.number_input("Project Area (m²)", 50, 200000, 300, step=50)
    duration_months = st.number_input("Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)
    workers = st.number_input("Number of Workers", 1, 500, 20)

    if st.button("Analyze Project 🚀"):
        with st.spinner("Analyzing project..."):
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        st.subheader("Results")
        st.metric("Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        st.metric("Delay Probability", f"{result['delay_probability']}%")
        st.write("Risk Level:", result["risk_level"])

        st.subheader("Recommendations")
        for r in result["recommendations"]:
            st.write("•", r)

        # Save for admin
        st.session_state.logs.append({
            "Project Type": project_type,
            "Project Size": project_size,
            "Risk Level": result["risk_level"],
            "Delay %": result["delay_probability"]
        })

# ==================================================
# ADMIN PAGE
# ==================================================
else:
    st.title("Admin Panel 🔐")

    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")
    password = st.text_input("Admin Password", type="password")

    if password != ADMIN_PASSWORD:
        st.warning("Access restricted")
        st.stop()

    st.success("Admin access granted")

    if st.session_state.logs:
        st.dataframe(pd.DataFrame(st.session_state.logs))
    else:
        st.info("No predictions yet.")
