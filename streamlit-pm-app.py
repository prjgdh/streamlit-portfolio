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
    with open('users.json', 'w') as f:
        json.dump(st.session_state.users, f)

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
        except:
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
            