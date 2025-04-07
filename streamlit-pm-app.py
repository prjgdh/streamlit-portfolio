import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import time
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

# CSS for modern styling
st.markdown("""
<style>
    :root {
        --primary: #2c3e50;
        --secondary: #3498db;
        --background: #f8f9fa;
    }
    
    .main-header {
        font-size: 2.5rem;
        color: var(--primary);
        font-weight: 700;
        margin-bottom: 1rem;
        border-bottom: 3px solid var(--secondary);
        padding-bottom: 0.5rem;
    }
    
    .card {
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 25px;
        margin-bottom: 25px;
        transition: transform 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
    }
    
    .metric-box {
        text-align: center;
        padding: 20px;
        border-radius: 8px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .gantt-chart {
        border-radius: 8px;
        overflow: hidden;
    }
    
    .stButton>button {
        background: var(--secondary);
        color: white;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: var(--primary);
        transform: scale(1.05);
    }
    
    .sidebar .sidebar-content {
        background: var(--background);
    }
</style>
""", unsafe_allow_html=True)

# Authentication Functions
USER_DATA_FILE = 'users.json'

def initialize_user_data():
    if not Path(USER_DATA_FILE).exists():
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f)

def load_users():
    initialize_user_data()
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Data Management
def initialize_project_data():
    return {
        'tasks': [],
        'milestones': [],
        'resources': [],
        'created_at': datetime.datetime.now().isoformat(),
        'last_modified': datetime.datetime.now().isoformat()
    }

# Excel Processing
def process_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name=None)
        return True, {'tasks': df['Tasks'].to_dict('records'), 
                     'milestones': df['Milestones'].to_dict('records')}
    except Exception as e:
        return False, str(e)

def create_gantt_chart(tasks):
    df = pd.DataFrame(tasks)
    df['Start'] = pd.to_datetime(df['scheduled_start'])
    df['Finish'] = pd.to_datetime(df['scheduled_finish'])
    
    fig = px.timeline(df, 
                     x_start="Start", 
                     x_end="Finish", 
                     y="title",
                     color="completion",
                     title="Project Gantt Chart")
    fig.update_yaxes(autorange="reversed")
    return fig

# Authentication Flow
def login_section():
    st.sidebar.header("Project Authentication")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    users = load_users()
    
    if st.sidebar.button("Login"):
        if username in users:
            if users[username]['password'] == hash_password(password):
                st.session_state['authenticated'] = True
                st.session_state['current_user'] = username
                st.success("Login Successful!")
                return True
        st.error("Invalid credentials")
    return False

def create_user_section():
    with st.expander("New User Registration"):
        new_user = st.text_input("New Username")
        if st.button("Create User"):
            if new_user in load_users():
                st.error("Username already exists")
            else:
                password = generate_password()
                users = load_users()
                users[new_user] = {
                    'password': hash_password(password),
                    'projects': {},
                    'created_at': datetime.datetime.now().isoformat()
                }
                save_users(users)
                st.success(f"User created! Password: {password}")

# Main App
def project_dashboard():
    st.title("Project Management Dashboard")
    
    users = load_users()
    current_user = st.session_state['current_user']
    
    # Project Selection
    projects = users[current_user]['projects']
    selected_project = st.selectbox("Select Project", list(projects.keys()))
    
    # Load Project Data
    project_data = projects[selected_project]
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Gantt Chart", "Resource Utilization", "Project Details"])
    
    with tab1:
        st.plotly_chart(create_gantt_chart(project_data['tasks']), use_container_width=True)
    
    with tab2:
        # Resource Utilization Visualization
        pass
    
    with tab3:
        # Project Details and Excel Management
        st.subheader("Project Data Management")
        
        uploaded_file = st.file_uploader("Upload Project Plan (Excel)", type="xlsx")
        if uploaded_file:
            success, result = process_excel(uploaded_file)
            if success:
                project_data.update(result)
                save_users(users)
                st.success("Project data updated!")
            else:
                st.error(f"Error: {result}")
        
        if st.button("Download Project Plan"):
            # Excel export implementation
            pass

# Main Execution
if __name__ == "__main__":
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        st.title("Project Management Portal")
        create_user_section()
        if login_section():
            st.experimental_rerun()
    else:
        project_dashboard()
