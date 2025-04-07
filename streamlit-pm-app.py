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
    .weekend { background-color: #f8f9fa !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Authentication System
class AuthSystem:
    def __init__(self):
        self.users_file = "pm_users.json"
        Path(self.users_file).touch(exist_ok=True)
        
    def _load_users(self):
        with open(self.users_file, 'r') as f:
            return json.loads(f.read() or "{}")
    
    def _save_users(self, users):
        with open(self.users_file, 'w') as f:
            json.dump(users, f)
    
    def register_user(self, username, password):
        users = self._load_users()
        if username in users:
            return False, "Username exists"
        users[username] = {
            'password': self._hash_password(password),
            'projects': {},
            'created_at': datetime.datetime.now().isoformat()
        }
        self._save_users(users)
        return True, "Registered successfully"
    
    def authenticate_user(self, username, password):
        users = self._load_users()
        user = users.get(username)
        if not user or user['password'] != self._hash_password(password):
            return False, "Invalid credentials"
        return True, "Login successful"
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

# Project Management Core
class ProjectManager:
    def __init__(self, username):
        self.auth = AuthSystem()
        self.username = username
    
    def create_project(self, project_name):
        users = self.auth._load_users()
        project_id = self._generate_id()
        edit_pw = self._generate_password()
        view_pw = self._generate_password()
        
        users[self.username]['projects'][project_id] = {
            'name': project_name,
            'edit_pw': self.auth._hash_password(edit_pw),
            'view_pw': self.auth._hash_password(view_pw),
            'created_at': datetime.datetime.now().isoformat(),
            'tasks': [],
            'milestones': []
        }
        self.auth._save_users(users)
        return project_id, edit_pw, view_pw
    
    def load_project(self, project_id, password):
        users = self.auth._load_users()
        project = users[self.username]['projects'].get(project_id)
        if not project:
            return False, "Project not found"
        if project['edit_pw'] == self.auth._hash_password(password):
            return True, "edit"
        if project['view_pw'] == self.auth._hash_password(password):
            return True, "view"
        return False, "Invalid password"
    
    def _generate_id(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    
    def _generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(random.choices(chars, k=12))

# Excel Integration
class ExcelManager:
    @staticmethod
    def import_excel(uploaded_file):
        try:
            df_tasks = pd.read_excel(uploaded_file, sheet_name='Tasks')
            df_milestones = pd.read_excel(uploaded_file, sheet_name='Milestones')
            
            tasks = []
            for _, row in df_tasks.iterrows():
                tasks.append({
                    'id': str(uuid.uuid4()),
                    'title': row['Task Title'],
                    'start': row['Start Date'].strftime('%Y-%m-%d'),
                    'end': row['End Date'].strftime('%Y-%m-%d'),
                    'progress': f"{row['Progress']}%",
                    'owner': row['Owner'],
                    'wbs': row['WBS']
                })
            
            milestones = []
            for _, row in df_milestones.iterrows():
                milestones.append({
                    'id': str(uuid.uuid4()),
                    'name': row['Milestone'],
                    'date': row['Date'].strftime('%Y-%m-%d'),
                    'type': row['Type']
                })
            
            return True, {'tasks': tasks, 'milestones': milestones}
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def export_excel(project_data):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tasks sheet
            tasks_df = pd.DataFrame(project_data['tasks'])
            tasks_df.to_excel(writer, sheet_name='Tasks', index=False)
            
            # Milestones sheet
            milestones_df = pd.DataFrame(project_data['milestones'])
            milestones_df.to_excel(writer, sheet_name='Milestones', index=False)
        output.seek(0)
        return output

# Visualization Engine
class Visualizer:
    @staticmethod
    def gantt_chart(tasks):
        df = pd.DataFrame([{
            'Task': t['title'],
            'Start': pd.to_datetime(t['start']),
            'Finish': pd.to_datetime(t['end']),
            'Progress': int(t['progress'].strip('%')),
            'Owner': t['owner']
        } for t in tasks])
        
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task",
                         color="Progress", color_continuous_scale='Blues',
                         title="Project Timeline")
        fig.update_yaxes(autorange="reversed")
        return fig
    
    @staticmethod
    def resource_heatmap(tasks):
        resources = list(set([t['owner'] for t in tasks if t['owner']]))
        date_range = pd.date_range(
            start=min([pd.to_datetime(t['start']) for t in tasks]),
            end=max([pd.to_datetime(t['end']) for t in tasks])
        )
        
        data = []
        for date in date_range:
            if date.weekday() >= 5: continue  # Skip weekends
            for resource in resources:
                count = sum(1 for t in tasks 
                          if t['owner'] == resource and 
                          pd.to_datetime(t['start']) <= date <= pd.to_datetime(t['end']))
                data.append({'Date': date, 'Resource': resource, 'Tasks': count})
        
        df = pd.DataFrame(data)
        fig = px.density_heatmap(df, x='Date', y='Resource', z='Tasks',
                                color_continuous_scale='Viridis',
                                title="Resource Utilization")
        fig.update_layout(xaxis_title='Date', yaxis_title='Resource')
        return fig

# Main Application
def main():
    auth = AuthSystem()
    
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = {
            'authenticated': False,
            'current_user': None,
            'current_project': None,
            'edit_mode': False
        }
    
    if not st.session_state.auth_state['authenticated']:
        render_auth_interface(auth)
    else:
        render_main_interface(auth)

def render_auth_interface(auth):
    st.markdown('<div class="main-header">Project Management Suite</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["Login", "Register", "Access Project"])
    with tabs[0]:
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                success, msg = auth.authenticate_user(username, password)
                if success:
                    st.session_state.auth_state.update({
                        'authenticated': True,
                        'current_user': username
                    })
                    st.rerun()
                else:
                    st.error(msg)
    
    with tabs[1]:
        with st.form("register"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Register"):
                success, msg = auth.register_user(new_user, new_pass)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    
    with tabs[2]:
        with st.form("project_access"):
            proj_user = st.text_input("Username")
            proj_id = st.text_input("Project ID")
            proj_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Access"):
                # Project access logic
                pass

def render_main_interface(auth):
    pm = ProjectManager(st.session_state.auth_state['current_user'])
    
    st.sidebar.header("Project Controls")
    if st.sidebar.button("New Project"):
        with st.form("new_project"):
            name = st.text_input("Project Name")
            if st.form_submit_button("Create"):
                project_id, edit_pw, view_pw = pm.create_project(name)
                st.success(f"Project created! Edit Password: {edit_pw} | View Password: {view_pw}")
    
    if st.session_state.auth_state['current_project']:
        render_project_workspace(pm)
    else:
        render_project_selection(pm)

def render_project_selection(pm):
    st.header("Your Projects")
    users = pm.auth._load_users()
    projects = users[pm.username]['projects']
    
    for pid, project in projects.items():
        with st.expander(f"{project['name']} ({pid})"):
            col1, col2 = st.columns(2)
            with col1:
                mode = st.radio("Mode", ["Edit", "View"], key=f"mode_{pid}")
                password = st.text_input("Password", type="password", key=f"pw_{pid}")
            
            with col2:
                if st.button("Load", key=f"load_{pid}"):
                    success, result = pm.load_project(pid, password)
                    if success:
                        st.session_state.auth_state.update({
                            'current_project': pid,
                            'edit_mode': (result == "edit")
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

def render_project_workspace(pm):
    project_data = pm.auth._load_users()[pm.username]['projects'][
        st.session_state.auth_state['current_project']]
    
    st.header(f"Project: {project_data['name']}")
    
    tabs = st.tabs(["Plan", "Resources", "Analytics", "Gantt", "Settings"])
    
    with tabs[0]:
        handle_excel_operations(project_data)
    
    with tabs[1]:
        st.plotly_chart(Visualizer.resource_heatmap(project_data['tasks']))
    
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(Visualizer.gantt_chart(project_data['tasks']))
        with col2:
            # Analytics components
            pass
    
    with tabs[3]:
        st.plotly_chart(Visualizer.gantt_chart(project_data['tasks']))
    
    with tabs[4]:
        st.write("Project Settings")
        st.write(f"Edit Password: {project_data['edit_pw']}")
        st.write(f"View Password: {project_data['view_pw']}")

def handle_excel_operations(project_data):
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
        if uploaded_file:
            success, data = ExcelManager.import_excel(uploaded_file)
            if success:
                project_data.update(data)
                st.success("Data imported!")
    
    with col2:
        if st.button("Export to Excel"):
            excel_data = ExcelManager.export_excel(project_data)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="project_plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
