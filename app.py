import streamlit as st
import pandas as pd
from predict_logic import predict

# ---------------------------------
# Page Config
# ---------------------------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# ---------------------------------
# Session State
# ---------------------------------
if "predicted_projects" not in st.session_state:
    st.session_state.predicted_projects = []

# ---------------------------------
# Sidebar
# ---------------------------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigate", ["User", "Admin"])

# ---------------------------------
# Constants
# ---------------------------------
PROJECT_TYPES = [
    "Residential Construction",
    "Commercial Fit-Out",
    "Building Finishing",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home System",
    "Security Systems",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")

# =================================
# USER PAGE
# =================================
if page == "User":

    st.title("BuildWise")
    st.caption("Clear insights to plan your construction project with confidence.")

    # -------- Project Type --------
    project_type = st.selectbox(
        "Project Type",
        PROJECT_TYPES
    )

    # خط فاصل يجبر Streamlit يعيد ترتيب الصفحة
    st.markdown("---")

    # -------- Project Size --------
    project_size = st.selectbox(
        "Project Size",
        PROJECT_SIZES
    )

    # -------- Dynamic Digital Screens (الحل النهائي) --------
    screen_container = st.container()
    num_screens = 0

    if project_type == "Digital Screen Installation":
        with screen_container:
            num_screens = st.number_input(
                "Number of Digital Screens",
                min_value=1,
                max_value=10,
                value=2,
                step=1
            )

    # -------- Other Inputs --------
    area_m2 = st.number_input(
        "Project Area (m²)",
        min_value=50,
        max_value=200000,
        value=300,
        step=50
    )

    duration_months = st.number_input(
        "Expected Duration (months)",
        min_value=0.5,
        max_value=60.0,
        value=3.0,
        step=0.5
    )

    workers = st.number_input(
        "Number of Workers",
        min_value=1,
        max_value=500,
        value=10
    )

    # -------- Prediction --------
    if st.button("Go 🚀"):

        with st.spinner("Analyzing project..."):
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers,
                num_screens
            )

        # -------- Cost Range --------
        cost = float(result["estimated_cost"])
        margin = 0.10
        cost_low = cost * (1 - margin)
        cost_high = cost * (1 + margin)

        # -------- Save Prediction --------
        st.session_state.predicted_projects.append({
            "Project Type": project_type,
            "Project Size": project_size,
            "Area (m²)": area_m2,
            "Duration (months)": duration_months,
            "Workers": workers,
            "Number of Screens": num_screens if project_type == "Digital Screen Installation" else "-",
            "Estimated Cost (SAR)": round(cost, 0),
            "Cost Range (SAR)": f"{cost_low:,.0f} – {cost_high:,.0f}",
            "Delay Probability (%)": result["delay_probability"],
            "Risk Level": result["risk_level"]
        })

        # -------- Results --------
        st.subheader("Project Results")

        st.metric("Estimated Cost (SAR)", f"{cost:,.0f}")
        st.caption(f"Expected Cost Range: **{cost_low:,.0f} – {cost_high:,.0f} SAR**")

        st.metric("Delay Probability", f"{result['delay_probability']}%")

        if result["risk_level"] == "Low":
            st.success("🟢 Low Delay Risk")
        elif result["risk_level"] == "Medium":
            st.warning("🟡 Medium Delay Risk")
        else:
            st.error("🔴 High Delay Risk")

        st.subheader("What you can do")
        for rec in result["recommendations"]:
            st.write(f"• {rec}")

# =================================
# ADMIN PAGE
# =================================
else:

    st.title("🔐 Admin Dashboard")

    password = st.text_input("Admin Password", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Enter admin password to continue.")
        st.stop()

    st.success("Welcome, Admin")

    st.subheader("📊 Predicted Projects")

    if st.session_state.predicted_projects:
        df_pred = pd.DataFrame(st.session_state.predicted_projects)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(df_pred))
        c2.metric("High Risk", len(df_pred[df_pred["Risk Level"] == "High"]))
        c3.metric("Medium Risk", len(df_pred[df_pred["Risk Level"] == "Medium"]))
        c4.metric("Low Risk", len(df_pred[df_pred["Risk Level"] == "Low"]))

        st.dataframe(df_pred, use_container_width=True)
    else:
        st.info("No predicted projects yet.")
