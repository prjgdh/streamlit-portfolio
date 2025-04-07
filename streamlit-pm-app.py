# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib
import json
import os
import io
import base64
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
USER_DATA_FILE = "pm_users.json"
MAX_PROJECTS_PER_USER = 50
SESSION_TIMEOUT = 1800  # 30 minutes

# Initialize paths
Path(USER_DATA_FILE).touch(exist_ok=True)

# --- Authentication System ---
class AuthSystem:
    def __init__(self):
        self.users = self._load_users()
        
    def _load_users(self):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def _save_users(self):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(self.users, f)
    
    def _hash(self, text):
        return hashlib.sha256(text.encode()).hexdigest()
    
    def create_user(self, username):
        if username in self.users:
            return False, "User exists"
        password = self._generate_password()
        self.users[username] = {
            'password': self._hash(password),
            'projects': {},
            'created': datetime.now().isoformat()
        }
        self._save_users()
        return True, password
    
    def authenticate(self, username, password):
        user = self.users.get(username)
        if not user or user['password'] != self._hash(password):
            return False
        return True
    
    def _generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=12))

# --- Project Management Core ---
class ProjectManager:
    def __init__(self, auth_system):
        self.auth = auth_system
        
    def create_project(self, username, project_name):
        if username not in self.auth.users:
            return False, "User not found"
        
        if len(self.auth.users[username]['projects']) >= MAX_PROJECTS_PER_USER:
            return False, "Project limit reached"
        
        project_id = self._generate_id()
        edit_pw = self.auth._generate_password()
        view_pw = self.auth._generate_password()
        
        self.auth.users[username]['projects'][project_id] = {
            'name': project_name,
            'edit_pw': self.auth._hash(edit_pw),
            'view_pw': self.auth._hash(view_pw),
            'created': datetime.now().isoformat(),
            'tasks': [],
            'milestones': [],
            'last_modified': datetime.now().isoformat()
        }
        self.auth._save_users()
        return True, (project_id, edit_pw, view_pw)
    
    def get_project(self, username, project_id, password):
        project = self.auth.users[username]['projects'].get(project_id)
        if not project:
            return False, "Project not found"
        
        if project['edit_pw'] == self.auth._hash(password):
            return True, 'edit'
        if project['view_pw'] == self.auth._hash(password):
            return True, 'view'
        return False, "Invalid password"
    
    def _generate_id(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

# --- Excel Integration ---
class ExcelHandler:
    @staticmethod
    def parse_excel(uploaded_file):
        try:
            tasks = pd.read_excel(uploaded_file, sheet_name='Tasks')
            milestones = pd.read_excel(uploaded_file, sheet_name='Milestones')
            
            # Data validation
            required_columns = {
                'Tasks': ['WBS', 'TASK TITLE', 'SCHEDULED START', 'SCHEDULED FINISH'],
                'Milestones': ['Milestones', 'Start Date', 'End Date']
            }
            
            for sheet, cols in required_columns.items():
                if not all(col in tasks.columns for col in cols):
                    return False, f"Missing columns in {sheet} sheet"
            
            return True, {
                'tasks': tasks.to_dict('records'),
                'milestones': milestones.to_dict('records')
            }
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def generate_excel(project_data):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Format tasks
            tasks_df = pd.DataFrame(project_data['tasks'])
            tasks_df.to_excel(writer, sheet_name='Tasks', index=False)
            
            # Format milestones
            milestones_df = pd.DataFrame(project_data['milestones'])
            milestones_df.to_excel(writer, sheet_name='Milestones', index=False)
            
            # Add formatting
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1E88E5',
                'font_color': 'white',
                'border': 1
            })
            
            for sheet in writer.sheets.values():
                sheet.set_column('A:Z', 20)
                sheet.write_row(0, 0, tasks_df.columns, header_format)
        
        output.seek(0)
        return output

# --- Visualization Engine ---
class ProjectVisualizer:
    @staticmethod
    def create_gantt(tasks):
        try:
            df = pd.DataFrame([{
                'Task': task['TASK TITLE'],
                'Start': pd.to_datetime(task['SCHEDULED START']),
                'Finish': pd.to_datetime(task['SCHEDULED FINISH']),
                'Progress': int(task.get('PCT OF TASK COMPLETE', 0)),
                'Owner': task.get('TASK OWNER', ''),
                'WBS': task.get('WBS', '')
            } for task in tasks])
            
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task",
                             color="Progress", color_continuous_scale='Blues',
                             hover_data=['Owner', 'WBS'],
                             title="Project Gantt Chart")
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=600)
            return fig
        except Exception as e:
            st.error(f"Error generating Gantt: {str(e)}")
            return None
    
    @staticmethod
    def create_resource_heatmap(tasks):
        try:
            resources = list(set([t.get('TASK OWNER') for t in tasks if t.get('TASK OWNER')]))
            date_range = pd.date_range(
                start=min([pd.to_datetime(t['SCHEDULED START']) for t in tasks]),
                end=max([pd.to_datetime(t['SCHEDULED FINISH']) for t in tasks])
            )
            
            data = []
            for date in date_range:
                if date.weekday() >= 5: continue  # Skip weekends
                for resource in resources:
                    count = sum(1 for t in tasks 
                              if t.get('TASK OWNER') == resource and 
                              pd.to_datetime(t['SCHEDULED START']) <= date <= pd.to_datetime(t['SCHEDULED FINISH']))
                    data.append({'Date': date, 'Resource': resource, 'Tasks': count})
            
            df = pd.DataFrame(data)
            fig = px.density_heatmap(df, x='Date', y='Resource', z='Tasks',
                                    color_continuous_scale='Viridis',
                                    title="Resource Utilization (Excluding Weekends)")
            fig.update_layout(height=600)
            return fig
        except Exception as e:
            st.error(f"Error generating heatmap: {str(e)}")
            return None

# --- UI Components ---
def auth_gate():
    st.markdown("""
    <style>
        .auth-container {
            max-width: 600px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .auth-header {
            font-size: 2rem;
            color: #1E88E5;
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header">Project Management Suite</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Login", "Register", "Access Project"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    auth = AuthSystem()
                    if auth.authenticate(username, password):
                        st.session_state.auth = {
                            'user': username,
                            'time': datetime.now(),
                            'projects': auth.users[username]['projects']
                        }
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("New Username")
                if st.form_submit_button("Create Account"):
                    auth = AuthSystem()
                    success, password = auth.create_user(new_user)
                    if success:
                        st.success(f"Account created! Password: {password}")
                    else:
                        st.error("Username already exists")
        
        with tab3:
            with st.form("project_access"):
                proj_user = st.text_input("Username")
                proj_id = st.text_input("Project ID")
                proj_pass = st.text_input("Password", type="password")
                if st.form_submit_button("Access Project"):
                    auth = AuthSystem()
                    pm = ProjectManager(auth)
                    valid, mode = pm.get_project(proj_user, proj_id, proj_pass)
                    if valid:
                        st.session_state.auth = {
                            'user': proj_user,
                            'project_id': proj_id,
                            'mode': mode,
                            'time': datetime.now()
                        }
                        st.rerun()
                    else:
                        st.error("Invalid project access credentials")
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- Main Application ---
def main_app():
    # Session timeout check
    if (datetime.now() - st.session_state.auth['time']).seconds > SESSION_TIMEOUT:
        st.error("Session expired")
        del st.session_state.auth
        st.rerun()
    
    auth = AuthSystem()
    pm = ProjectManager(auth)
    visualizer = ProjectVisualizer()
    
    # Sidebar controls
    with st.sidebar:
        st.header(f"Welcome, {st.session_state.auth['user']}")
        st.write(f"Access mode: {st.session_state.auth.get('mode', 'full')}")
        
        if st.button("Logout"):
            del st.session_state.auth
            st.rerun()
        
        if 'project_id' not in st.session_state.auth:
            with st.form("new_project"):
                project_name = st.text_input("New Project Name")
                if st.form_submit_button("Create Project"):
                    success, (pid, epw, vpw) = pm.create_project(
                        st.session_state.auth['user'], 
                        project_name
                    )
                    if success:
                        st.session_state.auth['project_id'] = pid
                        st.success(f"Created! Edit PW: {epw} | View PW: {vpw}")
                        st.rerun()
    
    # Main interface
    if 'project_id' in st.session_state.auth:
        current_project = auth.users[st.session_state.auth['user']]['projects'][
            st.session_state.auth['project_id']]
        
        # Excel operations
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("Upload Excel Plan", type=["xlsx"])
            if uploaded_file:
                success, data = ExcelHandler.parse_excel(uploaded_file)
                if success:
                    current_project.update(data)
                    auth._save_users()
                    st.success("Project data updated!")
                else:
                    st.error(f"Error: {data}")
        
        with col2:
            if st.download_button(
                label="Download Excel",
                data=ExcelHandler.generate_excel(current_project).getvalue(),
                file_name="project_plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ):
                st.success("Excel file generated")
        
        # Project visualization
        tab1, tab2, tab3 = st.tabs(["Gantt Chart", "Resource Utilization", "Details"])
        
        with tab1:
            fig = visualizer.create_gantt(current_project['tasks'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = visualizer.create_resource_heatmap(current_project['tasks'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.data_editor(
                pd.DataFrame(current_project['tasks']),
                num_rows="dynamic",
                use_container_width=True,
                disabled=(st.session_state.auth.get('mode', 'edit') != 'edit')
            )
    else:
        st.header("Your Projects")
        projects = auth.users[st.session_state.auth['user']]['projects']
        
        for pid, project in projects.items():
            with st.expander(f"{project['name']} ({pid})"):
                col1, col2 = st.columns(2)
                with col1:
                    password = st.text_input("Password", type="password", key=f"pw_{pid}")
                with col2:
                    if st.button("Open", key=f"open_{pid}"):
                        valid, mode = pm.get_project(
                            st.session_state.auth['user'],
                            pid,
                            password
                        )
                        if valid:
                            st.session_state.auth.update({
                                'project_id': pid,
                                'mode': mode
                            })
                            st.rerun()
                        else:
                            st.error("Invalid password")

# --- Main Flow ---
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    if 'auth' not in st.session_state:
        auth_gate()
    else:
        main_app()
