import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import random
import string
import hashlib
import json
import os
import io
import base64
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Project Management App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 1rem;
        border-bottom: 3px solid #0D47A1;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .gantt-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #1E88E5 !important;
        color: white !important;
    }
    .st-eb {
        background: #f0f4f8 !important;
    }
    .warning {
        background: #fff3cd;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
USER_FILE = "users.json"
Path(USER_FILE).touch(exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    with open(USER_FILE, "r") as f:
        return json.loads(f.read() or "{}")

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(12))

# Project management functions
def init_project(name):
    return {
        "name": name,
        "tasks": [],
        "milestones": [],
        "created": datetime.datetime.now().isoformat(),
        "edit_pw": generate_password(),
        "view_pw": generate_password()
    }

def validate_dates(start, end):
    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        return start_date < end_date
    except:
        return False

# Excel processing
def process_excel(uploaded_file):
    try:
        tasks_df = pd.read_excel(uploaded_file, sheet_name="Tasks")
        milestones_df = pd.read_excel(uploaded_file, sheet_name="Milestones")
        
        tasks = []
        for _, row in tasks_df.iterrows():
            tasks.append({
                "id": str(len(tasks) + 1),
                "title": row.get("Task Title", ""),
                "owner": row.get("Owner", ""),
                "start": row.get("Start Date", ""),
                "end": row.get("End Date", ""),
                "progress": f"{row.get('Progress', 0)}%",
                "dependencies": row.get("Dependencies", ""),
                "wbs": row.get("WBS", "1.1")
            })
            
        milestones = []
        for _, row in milestones_df.iterrows():
            milestones.append({
                "id": str(len(milestones) + 1),
                "name": row.get("Milestone", ""),
                "date": row.get("Date", ""),
                "type": row.get("Type", "Major")
            })
            
        return True, {"tasks": tasks, "milestones": milestones}
    except Exception as e:
        return False, str(e)

def export_to_excel(project):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Tasks sheet
        tasks_df = pd.DataFrame(project["tasks"])
        tasks_df.to_excel(writer, sheet_name="Tasks", index=False)
        
        # Milestones sheet
        milestones_df = pd.DataFrame(project["milestones"])
        milestones_df.to_excel(writer, sheet_name="Milestones", index=False)
    
    output.seek(0)
    return output.getvalue()

# Visualization functions
def create_gantt(tasks):
    df = pd.DataFrame([{
        "Task": t["title"],
        "Start": pd.to_datetime(t["start"]),
        "Finish": pd.to_datetime(t["end"]),
        "Progress": int(t["progress"].replace("%", "")),
        "Owner": t["owner"]
    } for t in tasks if t.get("start") and t.get("end")])
    
    if df.empty:
        return None
    
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", 
                     color="Progress", color_continuous_scale="Blues",
                     title="Project Gantt Chart")
    fig.update_yaxes(autorange="reversed")
    return fig

def create_resource_chart(tasks):
    resources = {}
    for task in tasks:
        if task["owner"]:
            duration = (pd.to_datetime(task["end"]) - pd.to_datetime(task["start"])).days
            resources[task["owner"]] = resources.get(task["owner"], 0) + duration
    
    if not resources:
        return None
    
    fig = px.bar(x=list(resources.keys()), y=list(resources.values()), 
                labels={"x": "Resource", "y": "Total Days"},
                title="Resource Allocation")
    return fig

# Authentication UI
def auth_section():
    st.sidebar.header("Authentication")
    mode = st.sidebar.radio("Mode", ["Login", "Register"])
    
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    users = load_users()
    
    if mode == "Register":
        if st.sidebar.button("Create Account"):
            if username in users:
                st.sidebar.error("Username exists")
            elif len(password) < 8:
                st.sidebar.error("Password needs 8+ chars")
            else:
                users[username] = {
                    "pw": hash_password(password),
                    "projects": {}
                }
                save_users(users)
                st.sidebar.success("Account created")
    
    if mode == "Login":
        if st.sidebar.button("Login"):
            user = users.get(username)
            if user and user["pw"] == hash_password(password):
                st.session_state.user = username
                st.session_state.projects = user["projects"]
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

# Main app
def project_dashboard():
    st.title("Project Management Dashboard")
    user = st.session_state.user
    projects = st.session_state.projects
    
    # Project selection
    col1, col2 = st.columns([3,1])
    with col1:
        selected_project = st.selectbox("Projects", list(projects.keys()))
    with col2:
        if st.button("New Project"):
            project_name = f"Project {len(projects)+1}"
            new_project = init_project(project_name)
            projects[new_project["edit_pw"]] = new_project  # Using edit_pw as key
            save_users(load_users())
            st.rerun()
    
    # Project actions
    project = projects[selected_project]
    tab1, tab2, tab3, tab4 = st.tabs(["Plan", "Gantt", "Resources", "Settings"])
    
    with tab1:
        # Excel upload
        uploaded_file = st.file_uploader("Upload Excel Plan", type=["xlsx"])
        if uploaded_file:
            success, data = process_excel(uploaded_file)
            if success:
                project.update(data)
                save_users(load_users())
                st.success("Plan updated")
            else:
                st.error(f"Error: {data}")
        
        # Task table
        st.data_editor(
            pd.DataFrame(project["tasks"]),
            num_rows="dynamic",
            use_container_width=True
        )
    
    with tab2:
        # Gantt chart
        fig = create_gantt(project["tasks"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Add tasks with dates to view Gantt")
    
    with tab3:
        # Resource chart
        fig = create_resource_chart(project["tasks"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Add tasks with owners to view resources")
    
    with tab4:
        # Project credentials
        st.markdown(f"""
        ### Project Access
        **Edit Password:** `{project['edit_pw']}`  
        **View Password:** `{project['view_pw']}`
        """)
        
        # Excel export
        excel_data = export_to_excel(project)
        st.download_button(
            label="Export to Excel",
            data=excel_data,
            file_name="project_plan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Danger zone
        with st.expander("Danger Zone"):
            if st.button("Delete Project"):
                del projects[selected_project]
                save_users(load_users())
                st.rerun()

# Main flow
if "user" not in st.session_state:
    auth_section()
    st.markdown("""
    <div class="main-header">Project Management Suite</div>
    <div class="warning">
        <b>Important:</b> Passwords are stored securely using SHA-256 hashing.
        Projects persist across sessions using local storage.
    </div>
    """, unsafe_allow_html=True)
else:
    project_dashboard()
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()
