import streamlit as st
import hashlib
import json
import os
import random
import string
import datetime

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