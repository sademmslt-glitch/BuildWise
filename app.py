import streamlit as st
import pandas as pd
from predict_logic import predict

st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# Session storage
if "logs" not in st.session_state:
    st.session_state.logs = []

# Sidebar
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigate", ["Project Insight", "Admin"])

PROJECT_TYPES = [
    "Residential Construction",
    "Commercial Fit-Out",
    "Building Finishing",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home System",
    "Security Systems",
    "FTTH Infrastructure",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]

# ================= USER PAGE =================
if page == "Project Insight":

    st.title("BuildWise")
    st.caption("Clear insights to plan your construction project with confidence.")

    project_type = st.selectbox("Project Type", PROJECT_TYPES)
    project_size = st.selectbox("Project Size", PROJECT_SIZES)
    area_m2 = st.number_input("Project Area (m²)", 50, 200000, 300, step=50)
    duration_months = st.number_input("Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)
    workers = st.number_input("Number of Workers", 1, 500, 20)

    if st.button("Show Insights 🚀"):
        with st.spinner("Checking project..."):
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        st.subheader("Project Results")

        st.metric("Estimated Cost (SAR)", f"{result['estimated_cost']:,.0f}")
        st.metric("Delay Probability", f"{result['delay_probability']}%")

        # Risk color
        if result["risk_level"] == "Low":
            st.success("🟢 Low Delay Risk")
        elif result["risk_level"] == "Medium":
            st.warning("🟡 Medium Delay Risk")
        else:
            st.error("🔴 High Delay Risk")

        st.subheader("What you can do")
        for rec in result["recommendations"]:
            st.write("•", rec)

        # Save for admin
        st.session_state.logs.append({
            "Project Type": project_type,
            "Area (m²)": area_m2,
            "Duration (months)": duration_months,
            "Workers": workers,
            "Cost (SAR)": result["estimated_cost"],
            "Delay %": result["delay_probability"],
            "Risk Level": result["risk_level"]
        })

# ================= ADMIN PAGE =================
else:
    st.title("🔐 BuildWise – Admin Dashboard")

    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")
    password = st.text_input("Admin Access Code", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Enter admin access code to continue.")
        st.stop()

    st.success("Welcome, Admin 👋")

    if len(st.session_state.logs) == 0:
        st.info("No project checks yet.")
    else:
        df = pd.DataFrame(st.session_state.logs)

        st.subheader("Management Overview")
        st.dataframe(df, use_container_width=True)

        st.subheader("Admin Actions")
        if st.button("Clear All Records"):
            st.session_state.logs.clear()
            st.success("All records cleared.")
