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

# Set page config
st.set_page_config(
    page_title="Project Management App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        font-weight: 600;
        margin: 1rem 0;
    }
    .card {
        border-radius: 5px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    .metric-card {
        text-align: center;
        padding: 15px;
        border-radius: 5px;
        background-color: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #616161;
        margin-top: 5px;
    }
    .status-active {
        color: white;
        background-color: #4CAF50;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .status-completed {
        color: white;
        background-color: #2196F3;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .status-overdue {
        color: white;
        background-color: #F44336;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .status-pending {
        color: white;
        background-color: #FF9800;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    .footer {
        text-align: center;
        margin-top: 40px;
        padding: 20px;
        border-top: 1px solid #e0e0e0;
        color: #9e9e9e;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Custom styling for tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
    /* Weekend highlight in resource utilization */
    .weekend {
        background-color: #f8f9fa;
    }
    /* Task detail panel */
    .task-detail {
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    /* Button styling */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# Functions for authentication and user management
def generate_random_password():
    """Generate a random password with 8 characters"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_users():
    """Initialize the users dictionary in session state"""
    if 'users' not in st.session_state:
        # Check if users.json exists
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                st.session_state.users = json.load(f)
        else:
            st.session_state.users = {}

def save_users():
    """Save the users dictionary to a JSON file"""
    try:
        with open('users.json', 'w') as f:
            json.dump(st.session_state.users, f)
    except Exception as e:
        st.error(f"Error saving user data: {str(e)}")

def user_exists(username):
    """Check if a user exists"""
    return username in st.session_state.users

def create_project(username, project_name):
    """Create a new project for a user"""
    if username not in st.session_state.users:
        return False, "User does not exist"
    
    edit_password = generate_random_password()
    view_password = generate_random_password()
    
    project_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    
    # Store hashed passwords
    st.session_state.users[username]['projects'][project_id] = {
        'name': project_name,
        'edit_password': hash_password(edit_password),
        'view_password': hash_password(view_password),
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'tasks': [],
        'milestones': []
    }
    
    save_users()
    
    return True, {
        'project_id': project_id,
        'edit_password': edit_password,
        'view_password': view_password
    }

def authenticate_project(username, project_id, password, mode='edit'):
    """Authenticate a user for a project"""
    if username not in st.session_state.users:
        return False, "User does not exist"
    
    if project_id not in st.session_state.users[username]['projects']:
        return False, "Project does not exist"
    
    hashed_password = hash_password(password)
    
    if mode == 'edit' and st.session_state.users[username]['projects'][project_id]['edit_password'] == hashed_password:
        return True, "Authentication successful"
    elif mode == 'view' and st.session_state.users[username]['projects'][project_id]['view_password'] == hashed_password:
        return True, "Authentication successful"
    elif mode == 'view' and st.session_state.users[username]['projects'][project_id]['edit_password'] == hashed_password:
        # Edit password can also be used to view
        return True, "Authentication successful"
    
    return False, "Incorrect password"

def register_user(username, password):
    """Register a new user"""
    if user_exists(username):
        return False, "Username already exists"
    
    st.session_state.users[username] = {
        'password': hash_password(password),
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'projects': {}
    }
    
    save_users()
    
    return True, "User registered successfully"

def login_user(username, password):
    """Login a user"""
    if not user_exists(username):
        return False, "User does not exist"
    
    if st.session_state.users[username]['password'] == hash_password(password):
        return True, "Login successful"
    
    return False, "Incorrect password"

def get_user_projects(username):
    """Get all projects for a user"""
    if not user_exists(username):
        return []
    
    projects = []
    for project_id, project_data in st.session_state.users[username]['projects'].items():
        projects.append({
            'id': project_id,
            'name': project_data['name'],
            'created_at': project_data['created_at']
        })
    
    return projects

# Functions for project data management
def init_project_data():
    """Initialize project data in session state"""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    
    if 'milestones' not in st.session_state:
        st.session_state.milestones = []

def load_project_data(username, project_id):
    """Load project data into session state"""
    if not user_exists(username) or project_id not in st.session_state.users[username]['projects']:
        return False
    
    project_data = st.session_state.users[username]['projects'][project_id]
    
    # Set current project
    st.session_state.current_project = {
        'username': username,
        'project_id': project_id,
        'name': project_data['name']
    }
    
    # Load tasks and milestones
    if 'tasks' in project_data:
        st.session_state.tasks = project_data['tasks']
    else:
        st.session_state.tasks = []
    
    if 'milestones' in project_data:
        st.session_state.milestones = project_data['milestones']
    else:
        st.session_state.milestones = []
    
    return True

def save_project_data():
    """Save project data from session state to users data"""
    if st.session_state.current_project is None:
        return False
    
    username = st.session_state.current_project['username']
    project_id = st.session_state.current_project['project_id']
    
    if not user_exists(username) or project_id not in st.session_state.users[username]['projects']:
        return False
    
    # Save tasks and milestones
    st.session_state.users[username]['projects'][project_id]['tasks'] = st.session_state.tasks
    st.session_state.users[username]['projects'][project_id]['milestones'] = st.session_state.milestones
    
    save_users()
    
    return True

def parse_date(date_str):
    """Parse date string in various formats"""
    if pd.isna(date_str) or date_str == '':
        return None
    
    formats = [
        '%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y',
        '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
        '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If none of the formats match, return None
    return None

def format_date(date_obj):
    """Format date object to string"""
    if date_obj is None:
        return ''
    
    return date_obj.strftime('%d/%m/%Y')

# Functions for Excel file processing
def process_uploaded_excel(upload_file):
    """Process uploaded Excel file"""
    try:
        # Read Excel file
        xlsx_data = upload_file.read()
        
        # Process with pandas
        excel_file = io.BytesIO(xlsx_data)
        
        # Read first sheet - tasks
        tasks_df = pd.read_excel(excel_file, sheet_name=0, header=4)
        
        # Clean tasks data
        tasks = []
        for _, row in tasks_df.iterrows():
            # Skip empty rows or header rows
            if pd.isna(row['WBS']) or pd.isna(row['TASK TITLE']) or row['WBS'] == 'WBS':
                continue
            
            task = {
                'id': str(len(tasks) + 1),
                'wbs': str(row['WBS']),
                'title': str(row['TASK TITLE']),
                'description': str(row['TASK DESCRIPTION']) if not pd.isna(row['TASK DESCRIPTION']) else '',
                'dependencies': str(row['DEPENDENCIES']) if not pd.isna(row['DEPENDENCIES']) else '',
                'owner': str(row['TASK OWNER']) if not pd.isna(row['TASK OWNER']) else '',
                'completion': str(row['PCT OF TASK COMPLETE']) if not pd.isna(row['PCT OF TASK COMPLETE']) else '0%',
                'scheduled_start': format_date(parse_date(str(row['SCHEDULED START']))) if not pd.isna(row['SCHEDULED START']) else '',
                'scheduled_finish': format_date(parse_date(str(row['SCHEDULED FINISH']))) if not pd.isna(row['SCHEDULED FINISH']) else '',
                'actual_start': format_date(parse_date(str(row['ACTUAL START']))) if not pd.isna(row['ACTUAL START']) else '',
                'actual_finish': format_date(parse_date(str(row['ACTUAL FINISH']))) if not pd.isna(row['ACTUAL FINISH']) else '',
                'finish_variance': str(row['FINISH VARIANCE']) if not pd.isna(row['FINISH VARIANCE']) else '',
                'duration': str(row['DURATION']) if not pd.isna(row['DURATION']) else ''
            }
            
            tasks.append(task)
        
        # Reset excel file pointer
        excel_file.seek(0)
        
        # Read second sheet - milestones
        try:
            milestones_df = pd.read_excel(excel_file, sheet_name=1)
            
            # Clean milestones data
            milestones = []
            for _, row in milestones_df.iterrows():
                # Skip header row
                if row['Milestones'] == 'Milestones':
                    continue
                
                milestone = {
                    'id': str(len(milestones) + 1),
                    'name': str(row['Milestones']),
                    'start_date': format_date(parse_date(str(row['Start Date']))) if not pd.isna(row['Start Date']) else '',
                    'end_date': format_date(parse_date(str(row['End Date']))) if not pd.isna(row['End Date']) else '',
                    'key_milestone': str(row['Key Milestones']) if not pd.isna(row['Key Milestones']) else ''
                }
                
                milestones.append(milestone)
        except Exception as e:
            st.warning(f"Error processing milestones: {str(e)}")
            milestones = []
        
        # Set data in session state
        st.session_state.tasks = tasks
        st.session_state.milestones = milestones
        
        # Save project data
        save_project_data()
        
        return True, "Excel file processed successfully"
    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}"

def export_to_excel():
    """Export project data to Excel file"""
    try:
        # Create a Pandas Excel writer
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Create tasks DataFrame
        tasks_data = []
        for task in st.session_state.tasks:
            tasks_data.append({
                'WBS': task['wbs'],
                'TASK TITLE': task['title'],
                'TASK DESCRIPTION': task['description'],
                'DEPENDENCIES': task['dependencies'],
                'TASK OWNER': task['owner'],
                'PCT OF TASK COMPLETE': task['completion'],
                'SCHEDULED START': task['scheduled_start'],
                'SCHEDULED FINISH': task['scheduled_finish'],
                'ACTUAL START': task['actual_start'],
                'ACTUAL FINISH': task['actual_finish'],
                'FINISH VARIANCE': task['finish_variance'],
                'DURATION': task['duration']
            })
            
        tasks_df = pd.DataFrame(tasks_data)
        
        # Create milestones DataFrame
        milestones_data = []
        for milestone in st.session_state.milestones:
            milestones_data.append({
                'Milestones': milestone['name'],
                'Start Date': milestone['start_date'],
                'End Date': milestone['end_date'],
                'Key Milestones': milestone['key_milestone']
            })
        
        milestones_df = pd.DataFrame(milestones_data)
        
        # Write project title and info
        project_info_df = pd.DataFrame([
            ['PROJECT TITLE', '', st.session_state.current_project['name'], '', 'COMPANY NAME', '', 'Your Company'],
            ['PROJECT MANAGER', '', 'Project Manager', '', 'PROJECT START DATE', '', datetime.datetime.now().strftime('%d/%m/%Y'), '', '0']
        ])
        
        # Write Excel file with formatting
        project_info_df.to_excel(writer, sheet_name='Sheet1', startrow=0, header=False, index=False)
        
        # Add header for tasks
        header_df = pd.DataFrame([['WBS', 'TASK TITLE', 'TASK DESCRIPTION', 'DEPENDENCIES', 'TASK OWNER', 
                                 'PCT OF TASK COMPLETE', 'SCHEDULED START', 'SCHEDULED FINISH', 
                                 'ACTUAL START', 'ACTUAL FINISH', 'FINISH VARIANCE', 'DURATION']])
        header_df.to_excel(writer, sheet_name='Sheet1', startrow=4, header=False, index=False)
        
        # Write tasks
        tasks_df.to_excel(writer, sheet_name='Sheet1', startrow=5, header=False, index=False)
        
        # Write milestones to second sheet
        milestones_df.to_excel(writer, sheet_name='Sheet2', index=False)
        
        # Close the Pandas Excel writer and get the output
        writer.close()
        
        return output.getvalue()
    except Exception as e:
        st.error(f"Error exporting to Excel: {str(e)}")
        return None

# Functions for Gantt chart generation
def create_gantt_chart(tasks, level=1, parent_wbs=None):
    """Create a Gantt chart from tasks"""
    # Filter tasks based on WBS level
    filtered_tasks = []
    for task in tasks:
        wbs_parts = task['wbs'].split('.')
        
        # Check if task matches the current level and parent WBS
        if len(wbs_parts) == level and (parent_wbs is None or task['wbs'].startswith(parent_wbs + '.')):
            filtered_tasks.append(task)
    
    # Prepare data for Gantt chart
    gantt_data = []
    
    for task in filtered_tasks:
        # Parse dates
        start_date = parse_date(task['scheduled_start']) or parse_date(task['actual_start'])
        end_date = parse_date(task['scheduled_finish']) or parse_date(task['actual_finish'])
        
        if start_date and end_date:
            # Calculate completion percentage
            completion = 0
            if task['completion'] and task['completion'].strip():
                try:
                    completion = float(task['completion'].replace('%', '')) / 100
                except:
                    completion = 0
            
            # Determine color based on completion
            if completion >= 1:
                color = '#4CAF50'  # Completed - Green
            elif completion > 0:
                color = '#2196F3'  # In Progress - Blue
            else:
                color = '#FF9800'  # Not Started - Orange
            
            # Add task to Gantt data
            gantt_data.append(dict(
                Task=task['title'],
                WBS=task['wbs'],
                Owner=task['owner'],
                Start=start_date,
                Finish=end_date,
                Completion=completion,
                Color=color
            ))
    
    if not gantt_data:
        return None
    
    # Create DataFrame for Gantt chart
    df = pd.DataFrame(gantt_data)
    
    # Create Gantt chart with Plotly
    fig = px.timeline(
        df, 
        x_start="Start", 
        x_end="Finish", 
        y="Task",
        color="Color",
        hover_data=["WBS", "Owner", "Completion"]
    )
    
    # Update layout
    fig.update_layout(
        title="Project Gantt Chart",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=max(400, len(gantt_data) * 40),
        showlegend=False
    )
    
    # Update traces
    fig.update_traces(marker_line_width=0)
    
    return fig

def create_resource_utilization_chart(tasks):
    """Create a resource utilization chart"""
    if not tasks:
        return None
    
    # Get unique resources
    resources = set()
    for task in tasks:
        if task['owner'] and task['owner'].strip():
            resources.add(task['owner'])
    
    # Get date range for the project
    all_dates = []
    for task in tasks:
        start_date = parse_date(task['scheduled_start']) or parse_date(task['actual_start'])
        end_date = parse_date(task['scheduled_finish']) or parse_date(task['actual_finish'])
        
        if start_date:
            all_dates.append(start_date)
        if end_date:
            all_dates.append(end_date)
    
    if not all_dates:
        return None
    
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    # Create date range
    date_range = pd.date_range(start=min_date, end=max_date)
    
    # Create resource utilization data
    utilization_data = {}
    for resource in resources:
        utilization_data[resource] = [0] * len(date_range)
    
    # Fill utilization data
    for task in tasks:
        if not task['owner'] or not task['owner'].strip():
            continue
        
        start_date = parse_date(task['scheduled_start']) or parse_date(task['actual_start'])
        end_date = parse_date(task['scheduled_finish']) or parse_date(task['actual_finish'])
        
        if not start_date or not end_date:
            continue
        
        # Get date range for the task
        task_dates = pd.date_range(start=start_date, end=end_date)
        
        # Increment utilization for each day the resource is working on the task
        for date in task_dates:
            if date in date_range:
                index = (date - min_date).days
                if index < len(utilization_data[task['owner']]):
                    utilization_data[task['owner']][index] += 1
    
    # Create DataFrame for the chart
    df_data = []
    for resource, utilization in utilization_data.items():
        for i, date in enumerate(date_range):
            # Skip weekends
            if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
            
            df_data.append({
                'Resource': resource,
                'Date': date,
                'Utilization': utilization[i]
            })
    
    df = pd.DataFrame(df_data)
    
    # Create heatmap
    fig = px.density_heatmap(
        df,
        x='Date',
        y='Resource',
        z='Utilization',
        color_continuous_scale='Viridis',
        title='Resource Utilization'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Resource',
        height=max(400, len(resources) * 40)
    )
    
    return fig

def create_task_completion_chart(tasks):
    """Create a task completion chart"""
    if not tasks:
        return None
    
    # Calculate completion percentages
    total_tasks = len(tasks)
    completed_tasks = 0
    in_progress_tasks = 0
    not_started_tasks = 0
    
    for task in tasks:
        completion = 0
        if task['completion'] and task['completion'].strip():
            try:
                completion = float(task['completion'].replace('%', '')) / 100
            except:
                completion = 0
        
        if completion >= 1:
            completed_tasks += 1
        elif completion > 0:
            in_progress_tasks += 1
        else:
            not_started_tasks += 1
    
    # Create pie chart
    labels = ['Completed', 'In Progress', 'Not Started']
    values = [completed_tasks, in_progress_tasks, not_started_tasks]
    colors = ['#4CAF50', '#2196F3', '#FF9800']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=colors
    )])
    
    fig.update_layout(
        title='Task Completion Status'
    )
    
    return fig

def create_milestone_timeline(milestones):
    """Create a milestone timeline chart"""
    if not milestones:
        return None
    
    # Prepare data for timeline
    timeline_data = []
    
    for milestone in milestones:
        end_date = parse_date(milestone['end_date'])
        
        if end_date:
            timeline_data.append({
                'Milestone': milestone['name'],
                'Date': end_date,
                'Description': milestone['key_milestone']
            })
    
    if not timeline_data:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(timeline_data)
    
    # Sort by date
    df = df.sort_values('Date')
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='Date',
        y='Milestone',
        hover_data=['Description'],
        size=[15] * len(df),
        color_discrete_sequence=['#E91E63']
    )
    
    # Add line connecting milestones
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Milestone'],
            mode='lines',
            line=dict(width=2, color='#9E9E9E'),
            hoverinfo='none'
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Milestone Timeline',
        xaxis_title='Date',
        yaxis_title='Milestone',
        height=max(400, len(timeline_data) * 40),
        showlegend=False
    )
    
    return fig

# Main app UI
def main():
    # Initialize session state
    init_users()
    init_project_data()
    
    # App header
    st.markdown('<div class="main-header">Project Management App</div>', unsafe_allow_html=True)
    
    # Check if user is logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Authentication section
    if not st.session_state.logged_in:
        # Show login/register form
        st.markdown('<div class="sub-header">User Authentication</div>', unsafe_allow_html=True)
        
        auth_tabs = st.tabs(["Login", "Register", "Project Access"])
        
        with auth_tabs[0]:  # Login tab
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if login_username and login_password:
                    success, message = login_user(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both username and password")
        
        with auth_tabs[1]:  # Register tab
            st.subheader("Register")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            
            if st.button("Register", key="register_button"):
                if reg_username and reg_password:
                    success, message = register_user(reg_username, reg_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both username and password")
        
        with auth_tabs[2]:  # Project Access tab
            st.subheader("Project Access")
            proj_username = st.text_input("Username", key="proj_username")
            proj_id = st.text_input("Project ID", key="proj_id")
            proj_password = st.text_input("Password (Edit or View)", type="password", key="proj_password")
            
            if st.button("Access Project", key="project_access_button"):
                if proj_username and proj_id and proj_password:
                    # Try edit mode first
                    success, message = authenticate_project(proj_username, proj_id, proj_password, mode='edit')
                    if success:
                        st.session_state.username = proj_username
                        st.session_state.edit_mode = True
                        load_project_data(proj_username, proj_id)
                        st.success("Project loaded in edit mode")
                        st.experimental_rerun()
                    else:
                        # Try view mode
                        success, message = authenticate_project(proj_username, proj_id, proj_password, mode='view')
                        if success:
                            st.session_state.username = proj_username
                            st.session_state.edit_mode = False
                            load_project_data(proj_username, proj_id)
                            st.success("Project loaded in view mode")
                            st.experimental_rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter username, project ID, and password")
        
        # Information note
        st.markdown("""
        <div class="highlight">
        <strong>Note:</strong> When you create a project, two passwords will be generated:
        <ul>
            <li>An edit password for full access</li>
            <li>A view password for read-only access</li>
        </ul>
        Please save these passwords, as they cannot be recovered if lost.
        </div>
        """, unsafe_allow_html=True)
            
    else:
        # User is logged in
        st.sidebar.success(f"Logged in as: {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.current_project = None
            st.session_state.tasks = []
            st.session_state.milestones = []
            st.session_state.edit_mode = False
            st.experimental_rerun()
        
        # Check if a project is loaded
        if st.session_state.current_project is not None:
            st.sidebar.info(f"Current Project: {st.session_state.current_project['name']}")
            st.sidebar.info(f"Mode: {'Edit' if st.session_state.edit_mode else 'View'}")
            
            # Main project section
            st.markdown(f'<div class="sub-header">{st.session_state.current_project["name"]}</div>', unsafe_allow_html=True)
            
            # Project tabs
            project_tabs = st.tabs(["Project Plan", "Resource Utilization", "Analytics", "Gantt Chart", "Settings"])
            
            with project_tabs[0]:  # Project Plan tab
                st.subheader("Project Plan")
                
                # Project plan actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.session_state.edit_mode and st.button("Add Task"):
                        st.session_state.add_task = True
                
                with col2:
                    if st.session_state.edit_mode and st.button("Add Milestone"):
                        st.session_state.add_milestone = True
                
                with col3:
                    if st.session_state.edit_mode:
                        upload_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"], key="project_plan_upload")
                        if upload_file:
                            success, message = process_uploaded_excel(upload_file)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                
                # Task addition form
                if st.session_state.edit_mode and 'add_task' in st.session_state and st.session_state.add_task:
                    st.subheader("Add New Task")
                    
                    # Create WBS options
                    wbs_options = ["1"]
                    for task in st.session_state.tasks:
                        wbs_parts = task['wbs'].split('.')
                        if len(wbs_parts) == 1:
                            wbs_options.append(f"{task['wbs']}.1")
                    
                    task_wbs = st.selectbox("WBS", wbs_options)
                    task_title = st.text_input("Task Title")
                    task_desc = st.text_area("Task Description")
                    task_deps = st.text_input("Dependencies")
                    task_owner = st.text_input("Task Owner")
                    task_completion = st.slider("Completion (%)", 0, 100, 0)
                    task_start = st.date_input("Scheduled Start")
                    task_finish = st.date_input("Scheduled Finish")
                    task_duration = st.number_input("Duration (days)", min_value=1, value=1)
                    
                    if st.button("Save Task"):
                        new_task = {
                            'id': str(len(st.session_state.tasks) + 1),
                            'wbs': task_wbs,
                            'title': task_title,
                            'description': task_desc,
                            'dependencies': task_deps,
                            'owner': task_owner,
                            'completion': f"{task_completion}%",
                            'scheduled_start': format_date(task_start),
                            'scheduled_finish': format_date(task_finish),
                            'actual_start': '',
                            'actual_finish': '',
                            'finish_variance': '',
                            'duration': str(task_duration)
                        }
                        
                        st.session_state.tasks.append(new_task)
                        save_project_data()
                        st.session_state.add_task = False
                        st.success("Task added successfully")
                        st.experimental_rerun()
                    
                    if st.button("Cancel"):
                        st.session_state.add_task = False
                        st.experimental_rerun()
                
                # Milestone addition form
                if st.session_state.edit_mode and 'add_milestone' in st.session_state and st.session_state.add_milestone:
                    st.subheader("Add New Milestone")
                    
                    ms_name = st.text_input("Milestone Name")
                    ms_start = st.date_input("Start Date")
                    ms_end = st.date_input("End Date")
                    ms_key = st.text_input("Key Milestone Description")
                    
                    if st.button("Save Milestone"):
                        new_milestone = {
                            'id': str(len(st.session_state.milestones) + 1),
                            'name': ms_name,
                            'start_date': format_date(ms_start),
                            'end_date': format_date(ms_end),
                            'key_milestone': ms_key
                        }
                        
                        st.session_state.milestones.append(new_milestone)
                        save_project_data()
                        st.session_state.add_milestone = False
                        st.success("Milestone added successfully")
                        st.experimental_rerun()
                    
                    if st.button("Cancel", key="cancel_milestone"):
                        st.session_state.add_milestone = False
                        st.experimental_rerun()
                
                # Display tasks
                st.subheader("Tasks")
                if st.session_state.tasks:
                    # Create expandable sections for top-level tasks
                    top_level_tasks = [task for task in st.session_state.tasks if len(task['wbs'].split('.')) == 1]
                    
                    for top_task in top_level_tasks:
                        with st.expander(f"{top_task['wbs']}. {top_task['title']}"):
                            # Display top task details
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Owner:** {top_task['owner']}")
                                st.markdown(f"**Completion:** {top_task['completion']}")
                            with col2:
                                st.markdown(f"**Start:** {top_task['scheduled_start']}")
                                st.markdown(f"**Finish:** {top_task['scheduled_finish']}")
                            
                            st.markdown(f"**Description:** {top_task['description']}")
                            
                            # Get subtasks
                            subtasks = [task for task in st.session_state.tasks if task['wbs'].startswith(f"{top_task['wbs']}.")]
                            
                            if subtasks:
                                # Display subtasks in a table
                                subtask_data = []
                                for subtask in subtasks:
                                    subtask_data.append({
                                        'WBS': subtask['wbs'],
                                        'Title': subtask['title'],
                                        'Owner': subtask['owner'],
                                        'Completion': subtask['completion'],
                                        'Start': subtask['scheduled_start'],
                                        'Finish': subtask['scheduled_finish'],
                                        'Duration': subtask['duration']
                                    })
                                
                                df = pd.DataFrame(subtask_data)
                                st.dataframe(df)
                            
                            # Edit button for top task
                            if st.session_state.edit_mode and st.button(f"Edit Task {top_task['wbs']}", key=f"edit_{top_task['wbs']}"):
                                st.session_state.edit_task_id = top_task['id']
                
                # Display milestones
                st.subheader("Milestones")
                if st.session_state.milestones:
                    milestone_data = []
                    for milestone in st.session_state.milestones:
                        milestone_data.append({
                            'Name': milestone['name'],
                            'Start Date': milestone['start_date'],
                            'End Date': milestone['end_date'],
                            'Description': milestone['key_milestone']
                        })
                    
                    df = pd.DataFrame(milestone_data)
                    st.dataframe(df)
                
                # Export button
                if st.button("Export to Excel"):
                    excel_data = export_to_excel()
                    if excel_data:
                        # Create download link
                        b64 = base64.b64encode(excel_data).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="project_plan.xlsx">Download Excel file</a>'
                        st.markdown(href, unsafe_allow_html=True)
            
            with project_tabs[1]:  # Resource Utilization tab
                st.subheader("Resource Utilization")
                
                # Generate resource utilization chart
                resource_chart = create_resource_utilization_chart(st.session_state.tasks)
                if resource_chart:
                    st.plotly_chart(resource_chart, use_container_width=True)
                else:
                    st.info("No resource utilization data available")
                
                # Display resource allocation
                if st.session_state.tasks:
                    # Get unique resources
                    resources = {}
                    for task in st.session_state.tasks:
                        if task['owner'] and task['owner'].strip():
                            if task['owner'] not in resources:
                                resources[task['owner']] = []
                            
                            resources[task['owner']].append({
                                'WBS': task['wbs'],
                                'Task': task['title'],
                                'Start': task['scheduled_start'],
                                'Finish': task['scheduled_finish'],
                                'Completion': task['completion']
                            })
                    
                    # Display resources and their tasks
                    for resource, tasks in resources.items():
                        with st.expander(f"Resource: {resource}"):
                            # Create DataFrame for resource tasks
                            df = pd.DataFrame(tasks)
                            st.dataframe(df)
                            
                            # Calculate resource workload
                            total_days = 0
                            for task in tasks:
                                start_date = parse_date(task['Start'])
                                finish_date = parse_date(task['Finish'])
                                
                                if start_date and finish_date:
                                    # Exclude weekends
                                    business_days = np.busday_count(
                                        start_date.strftime('%Y-%m-%d'),
                                        finish_date.strftime('%Y-%m-%d')
                                    )
                                    total_days += business_days
                            
                            st.metric("Total Working Days", total_days)
            
            with project_tabs[2]:  # Analytics tab
                st.subheader("Project Analytics")
                
                # Create metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate metrics
                total_tasks = len(st.session_state.tasks)
                
                completed_tasks = 0
                for task in st.session_state.tasks:
                    completion = 0
                    if task['completion'] and task['completion'].strip():
                        try:
                            completion = float(task['completion'].replace('%', '')) / 100
                        except:
                            completion = 0
                    
                    if completion >= 1:
                        completed_tasks += 1
                
                completion_percentage = 0
                if total_tasks > 0:
                    completion_percentage = int((completed_tasks / total_tasks) * 100)
                
                # Calculate total duration
                total_duration = 0
                for task in st.session_state.tasks:
                    if task['duration'] and task['duration'].strip():
                        try:
                            total_duration += int(task['duration'])
                        except:
                            pass
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{total_tasks}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Tasks</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{completion_percentage}%</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Project Completion</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{total_duration}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Duration (days)</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{len(st.session_state.milestones)}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Milestones</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Create charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Task completion chart
                    completion_chart = create_task_completion_chart(st.session_state.tasks)
                    if completion_chart:
                        st.plotly_chart(completion_chart, use_container_width=True)
                    else:
                        st.info("No task completion data available")
                
                with col2:
                    # Milestone timeline
                    milestone_chart = create_milestone_timeline(st.session_state.milestones)
                    if milestone_chart:
                        st.plotly_chart(milestone_chart, use_container_width=True)
                    else:
                        st.info("No milestone data available")
            
            with project_tabs[3]:  # Gantt Chart tab
                st.subheader("Gantt Chart")
                
                # Display Gantt chart
                gantt_chart = create_gantt_chart(st.session_state.tasks)
                if gantt_chart:
                    st.plotly_chart(gantt_chart, use_container_width=True)
                else:
                    st.info("No task data available for Gantt chart")
                
                # Task drill-down
                if st.session_state.tasks:
                    st.subheader("Task Drill-Down")
                    
                    # Get top-level tasks
                    top_level_tasks = [task for task in st.session_state.tasks if len(task['wbs'].split('.')) == 1]
                    top_level_options = [f"{task['wbs']}. {task['title']}" for task in top_level_tasks]
                    
                    selected_task = st.selectbox("Select Task", ["All Tasks"] + top_level_options)
                    
                    if selected_task != "All Tasks":
                        # Get selected task WBS
                        selected_wbs = selected_task.split('.')[0]
                        
                        # Create Gantt chart for selected task and its subtasks
                        task_gantt = create_gantt_chart(
                            st.session_state.tasks,
                            level=2,
                            parent_wbs=selected_wbs
                        )
                        
                        if task_gantt:
                            st.plotly_chart(task_gantt, use_container_width=True)
                        else:
                            st.info("No subtasks available for this task")
            
            with project_tabs[4]:  # Settings tab
                st.subheader("Project Settings")
                
                if st.session_state.edit_mode:
                    # Project info
                    st.markdown("### Project Information")
                    project_name = st.text_input("Project Name", st.session_state.current_project['name'])
                    
                    if st.button("Update Project Information"):
                        st.session_state.current_project['name'] = project_name
                        save_project_data()
                        st.success("Project information updated successfully")
                
                # Project access info
                st.markdown("### Project Access Information")
                st.markdown(f"**Project ID:** {st.session_state.current_project['project_id']}")
                
                # Project sharing
                st.markdown("### Share Project")
                st.markdown("""
                To share this project with others, provide them with:
                1. Your username
                2. The Project ID
                3. The appropriate password (Edit or View)
                """
                
                # Export/Import project
                st.markdown("### Export/Import Project")
                
                if st.session_state.edit_mode:
                    if st.button("Export Project Data"):
                        # Create JSON data
                        project_data = {
                            'project_name': st.session_state.current_project['name'],
                            'tasks': st.session_state.tasks,
                            'milestones': st.session_state.milestones
                        }
                        
                        # Convert to JSON
                        json_str = json.dumps(project_data, indent=4)
                        
                        # Create download link
                        b64 = base64.b64encode(json_str.encode()).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="project_data.json">Download Project Data</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    upload_file = st.file_uploader("Import Project Data", type=["json"], key="import_project")
                    if upload_file:
                        try:
                            import_data = json.load(upload_file)
                            
                            # Update project data
                            st.session_state.current_project['name'] = import_data['project_name']
                            st.session_state.tasks = import_data['tasks']
                            st.session_state.milestones = import_data['milestones']
                            
                            save_project_data()
                            st.success("Project data imported successfully")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error importing project data: {str(e)}")
        else:
            # No project loaded, show project creation/selection
            st.markdown('<div class="sub-header">Project Dashboard</div>', unsafe_allow_html=True)
            
            # Create tabs
            dashboard_tabs = st.tabs(["My Projects", "Create New Project"])
            
            with dashboard_tabs[0]:  # My Projects tab
                st.subheader("My Projects")
                
                # Get user's projects
                projects = get_user_projects(st.session_state.username)
                
                if projects:
                    # Display projects in a table
                    project_data = []
                    for project in projects:
                        project_data.append({
                            'Project Name': project['name'],
                            'Created At': project['created_at'],
                            'Project ID': project['id']
                        })
                    
                    df = pd.DataFrame(project_data)
                    st.dataframe(df)
                    
                    # Select project to load
                    project_options = [project['name'] for project in projects]
                    selected_project = st.selectbox("Select Project", project_options)
                    
                    # Find selected project ID
                    selected_id = None
                    for project in projects:
                        if project['name'] == selected_project:
                            selected_id = project['id']
                            break
                    
                    # Ask for password
                    if selected_id:
                        password = st.text_input("Enter Password (Edit or View)", type="password")
                        
                        if st.button("Load Project"):
                            # Try edit mode first
                            success, message = authenticate_project(st.session_state.username, selected_id, password, mode='edit')
                            if success:
                                st.session_state.edit_mode = True
                                load_project_data(st.session_state.username, selected_id)
                                st.success("Project loaded in edit mode")
                                st.experimental_rerun()
                            else:
                                # Try view mode
                                success, message = authenticate_project(st.session_state.username, selected_id, password, mode='view')
                                if success:
                                    st.session_state.edit_mode = False
                                    load_project_data(st.session_state.username, selected_id)
                                    st.success("Project loaded in view mode")
                                    st.experimental_rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("You don't have any projects yet")
                    st.markdown("Go to the 'Create New Project' tab to create your first project")
            
            with dashboard_tabs[1]:  # Create New Project tab
                st.subheader("Create New Project")
                
                project_name = st.text_input("Project Name")
                
                if st.button("Create Project"):
                    if project_name:
                        success, result = create_project(st.session_state.username, project_name)
                        if success:
                            # Show project credentials
                            st.success("Project created successfully")
                            
                            st.markdown("### Project Credentials")
                            st.markdown("**IMPORTANT:** Save these credentials. They cannot be recovered if lost.")
                            
                            st.markdown(f"**Project ID:** {result['project_id']}")
                            st.markdown(f"**Edit Password:** {result['edit_password']}")
                            st.markdown(f"**View Password:** {result['view_password']}")
                            
                            # Create download link for credentials
                            credentials = f"""
                            Project Credentials
                            -------------------
                            Project Name: {project_name}
                            Project ID: {result['project_id']}
                            Edit Password: {result['edit_password']}
                            View Password: {result['view_password']}
                            """
                            
                            b64 = base64.b64encode(credentials.encode()).decode()
                            href = f'<a href="data:text/plain;base64,{b64}" download="project_credentials.txt">Download Credentials</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                            # Load the project
                            st.session_state.edit_mode = True
                            load_project_data(st.session_state.username, result['project_id'])
                            
                            if st.button("Go to Project"):
                                st.experimental_rerun()
                        else:
                            st.error(result)
                    else:
                        st.warning("Please enter a project name")

if __name__ == "__main__":
    main())
