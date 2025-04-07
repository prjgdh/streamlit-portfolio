import streamlit as st
from auth import user_exists, save_users

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