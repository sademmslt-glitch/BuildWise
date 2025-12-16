import streamlit as st
import pandas as pd
from predict_logic import predict
import os

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

if "company_projects" not in st.session_state:
    st.session_state.company_projects = []

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
    "FTTH Infrastructure",
    "Digital Screen Installation",
]

PROJECT_SIZES = ["Small", "Medium", "Large"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")
ADMIN_DATA_FILE = "admin_projects_data.csv"

# =================================
# USER PAGE
# =================================
if page == "User":

    st.title("BuildWise")
    st.caption("Clear insights to plan your construction project with confidence.")

    # ✅ الحل المضمون لظهور عدد الشاشات: داخل form
    with st.form("user_project_form"):

        project_type = st.selectbox("Project Type", PROJECT_TYPES)
        project_size = st.selectbox("Project Size", PROJECT_SIZES)

        # يظهر فقط عند اختيار Digital Screen
        num_screens = 0
        if project_type == "Digital Screen Installation":
            num_screens = st.number_input(
                "Number of Digital Screens",
                min_value=1,
                max_value=20,
                value=2,
                step=1
            )

        area_m2 = st.number_input("Project Area (m²)", 50, 200000, 300, step=50)
        duration_months = st.number_input("Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)
        workers = st.number_input("Number of Workers", 1, 500, 10)

        submit_user = st.form_submit_button("Go 🚀")

    if submit_user:
        with st.spinner("Analyzing project..."):
            # مهم: predict لازم يقبل num_screens (إذا ما يقبله بيطلع TypeError)
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers,
                num_screens
            )

        cost = float(result["estimated_cost"])
        margin = 0.10
        cost_low = cost * (1 - margin)
        cost_high = cost * (1 + margin)

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

    st.success("Welcome, Admin ✅")

    # ---------------------------------
    # Predicted Projects Analysis
    # ---------------------------------
    st.subheader("📊 Predicted Projects Analysis")

    if st.session_state.predicted_projects:
        df_pred = pd.DataFrame(st.session_state.predicted_projects)

        total = len(df_pred)
        high = len(df_pred[df_pred["Risk Level"] == "High"])
        medium = len(df_pred[df_pred["Risk Level"] == "Medium"])
        low = len(df_pred[df_pred["Risk Level"] == "Low"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Predicted", total)
        c2.metric("High Risk", high)
        c3.metric("Medium Risk", medium)
        c4.metric("Low Risk", low)

        st.dataframe(df_pred, use_container_width=True)
    else:
        st.info("No predicted projects yet.")

    # ---------------------------------
    # Stored Company Projects (CSV)
    # ---------------------------------
    st.subheader("🏢 Stored Company Projects")

    if os.path.exists(ADMIN_DATA_FILE):
        df_company = pd.read_csv(ADMIN_DATA_FILE)
        st.dataframe(df_company, use_container_width=True)
    else:
        st.info("No company projects stored yet.")

    # ---------------------------------
    # Add Company Project Form (Admin)
    # ---------------------------------
    st.subheader("➕ Add Company Project")

    with st.form("add_company_project"):
        p_type = st.selectbox("Project Type", PROJECT_TYPES, key="admin_type")

        # ✅ لو الادمن اختار Digital Screen برضو يظهر عدد الشاشات
        p_screens = 0
        if p_type == "Digital Screen Installation":
            p_screens = st.number_input(
                "Number of Digital Screens",
                min_value=1,
                max_value=20,
                value=2,
                step=1,
                key="admin_screens"
            )

        p_area = st.number_input("Area (m²)", 50, 200000, 300, step=50, key="admin_area")
        p_duration = st.number_input("Duration (months)", 0.5, 60.0, 3.0, step=0.5, key="admin_duration")
        p_workers = st.number_input("Workers", 1, 500, 10, key="admin_workers")

        p_cost = st.number_input(
            "Estimated Budget (SAR)",
            min_value=0,
            step=10000,
            value=500000,
            key="admin_cost"
        )

        add = st.form_submit_button("Add Project")

    if add:
        new_project = {
            "project_type": p_type,
            "area_m2": p_area,
            "duration_months": p_duration,
            "workers": p_workers,
            "num_screens": p_screens if p_type == "Digital Screen Installation" else 0,
            "estimated_cost_sar": p_cost,
            "delay": None
        }

        if os.path.exists(ADMIN_DATA_FILE):
            df_existing = pd.read_csv(ADMIN_DATA_FILE)
            df_updated = pd.concat([df_existing, pd.DataFrame([new_project])], ignore_index=True)
        else:
            df_updated = pd.DataFrame([new_project])

        df_updated.to_csv(ADMIN_DATA_FILE, index=False)
        st.success("✅ Project added and stored successfully.")
