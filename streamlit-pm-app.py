import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import calendar
import io
import base64
import time
import matplotlib.pyplot as plt
import altair as alt
import json
import re
import random
from streamlit_option_menu import option_menu
import xlsxwriter
import uuid
import os

# Set page configuration
st.set_page_config(
    page_title="Project Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3498db;
        color: white;
    }
    
    div[data-testid="stVerticalBlock"] div[style*="flex-direction: column;"] div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="stMetric"] > div:first-child {
        color: #2c3e50;
    }
    
    div[data-testid="stMetric"] > div:nth-child(2) {
        color: #3498db;
    }
    
    /* Progress bars */
    div[data-testid="stProgressBar"] > div {
        background-color: #3498db;
    }
    
    /* Custom styling for gantt chart */
    .gantt-milestone {
        color: #e74c3c;
        font-weight: bold;
    }
    
    .weekend-highlight {
        background-color: #f5f5f5;
        opacity: 0.5;
    }
    
    /* Login form */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    
    .login-button {
        background-color: #3498db;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: bold;
        width: 100%;
        margin-top: 20px;
    }
    
    /* Task cards */
    .task-card {
        border-left: 4px solid #3498db;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .milestone-card {
        border-left: 4px solid #e74c3c;
    }
    
    /* Resource cards */
    .resource-card {
        border-left: 4px solid #2ecc71;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom color for overallocated resources */
    .overallocated {
        color: #e74c3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'current_project' not in st.session_state:
    st.session_state['current_project'] = None
if 'projects' not in st.session_state:
    st.session_state['projects'] = []
if 'selected_task' not in st.session_state:
    st.session_state['selected_task'] = None
if 'show_task_details' not in st.session_state:
    st.session_state['show_task_details'] = False

# Generate dummy users for demo
users = {
    "admin": "admin123",
    "project_manager": "manager123",
    "developer": "dev123"
}

# Login function
def login(username, password):
    if username in users and users[username] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        return True
    return False

# Logout function
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['current_project'] = None

# Login screen
def login_screen():
    st.markdown("<h1 style='text-align: center;'>Project Management Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Professional project planning and resource management</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", key="login_btn"):
            if login(username, password):
                st.success("Login successful!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("<p style='text-align: center; margin-top: 20px;'>Demo accounts:<br>Username: admin, Password: admin123<br>Username: project_manager, Password: manager123</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# File Uploader and Processor
def file_uploader():
    uploaded_file = st.file_uploader("Upload Project Plan Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success("File successfully uploaded!")
            
            # Process the file and create a new project
            project_id = str(uuid.uuid4())
            project_name = uploaded_file.name.split('.')[0]
            
            # Try to extract project info
            project_info = {
                'id': project_id,
                'name': project_name,
                'creation_date': datetime.now().strftime("%Y-%m-%d"),
                'tasks': [],
                'resources': []
            }
            
            # Find the tasks in the dataframe
            if 'TASK TITLE' in df.columns or 'Task Title' in df.columns:
                task_title_col = 'TASK TITLE' if 'TASK TITLE' in df.columns else 'Task Title'
                
                # Get other potential columns
                potential_columns = {
                    'WBS': ['WBS', 'wbs', 'ID', 'id'],
                    'DESCRIPTION': ['TASK DESCRIPTION', 'Task Description', 'Description'],
                    'DEPENDENCIES': ['DEPENDENCIES', 'Dependencies', 'Predecessors'],
                    'OWNER': ['TASK OWNER', 'Task Owner', 'Owner', 'Resource'],
                    'COMPLETE': ['PCT OF TASK COMPLETE', '% Complete', 'Complete'],
                    'START': ['SCHEDULED START', 'Start Date', 'Start'],
                    'FINISH': ['SCHEDULED FINISH', 'Finish Date', 'Finish'],
                    'DURATION': ['DURATION', 'Duration']
                }
                
                column_mapping = {}
                for key, potential_names in potential_columns.items():
                    for name in potential_names:
                        if name in df.columns:
                            column_mapping[key] = name
                            break
                
                # Process each task
                for idx, row in df.iterrows():
                    if pd.notna(row[task_title_col]) and row[task_title_col] != '':
                        task = {
                            'id': len(project_info['tasks']) + 1,
                            'title': row[task_title_col]
                        }
                        
                        # Add other fields if they exist
                        if 'WBS' in column_mapping:
                            task['wbs'] = str(row[column_mapping['WBS']]) if pd.notna(row[column_mapping['WBS']]) else ''
                        
                        if 'DESCRIPTION' in column_mapping:
                            task['description'] = row[column_mapping['DESCRIPTION']] if pd.notna(row[column_mapping['DESCRIPTION']]) else ''
                        
                        if 'DEPENDENCIES' in column_mapping:
                            task['dependencies'] = str(row[column_mapping['DEPENDENCIES']]) if pd.notna(row[column_mapping['DEPENDENCIES']]) else ''
                        
                        if 'OWNER' in column_mapping:
                            task['owner'] = row[column_mapping['OWNER']] if pd.notna(row[column_mapping['OWNER']]) else ''
                            
                            # Also add to resources if not already there
                            if pd.notna(row[column_mapping['OWNER']]) and row[column_mapping['OWNER']] != '':
                                resource_exists = False
                                for resource in project_info['resources']:
                                    if resource['name'] == row[column_mapping['OWNER']]:
                                        resource_exists = True
                                        break
                                
                                if not resource_exists:
                                    project_info['resources'].append({
                                        'id': len(project_info['resources']) + 1,
                                        'name': row[column_mapping['OWNER']],
                                        'role': 'Team Member',
                                        'allocation': []
                                    })
                        
                        if 'COMPLETE' in column_mapping:
                            task['percentComplete'] = float(row[column_mapping['COMPLETE']]) if pd.notna(row[column_mapping['COMPLETE']]) else 0
                        
                        if 'START' in column_mapping:
                            if pd.notna(row[column_mapping['START']]):
                                if isinstance(row[column_mapping['START']], str):
                                    task['startDate'] = row[column_mapping['START']]
                                else:
                                    task['startDate'] = row[column_mapping['START']].strftime("%Y-%m-%d")
                            else:
                                task['startDate'] = ''
                        
                        if 'FINISH' in column_mapping:
                            if pd.notna(row[column_mapping['FINISH']]):
                                if isinstance(row[column_mapping['FINISH']], str):
                                    task['endDate'] = row[column_mapping['FINISH']]
                                else:
                                    task['endDate'] = row[column_mapping['FINISH']].strftime("%Y-%m-%d")
                            else:
                                task['endDate'] = ''
                        
                        if 'DURATION' in column_mapping:
                            task['duration'] = int(row[column_mapping['DURATION']]) if pd.notna(row[column_mapping['DURATION']]) else 0
                        
                        # Check if it's a milestone (duration 0 or 1)
                        if 'DURATION' in column_mapping:
                            task['milestone'] = int(row[column_mapping['DURATION']]) <= 1 if pd.notna(row[column_mapping['DURATION']]) else False
                        
                        project_info['tasks'].append(task)
            
            # If no tasks were found, use sample data
            if len(project_info['tasks']) == 0:
                # Create sample tasks
                sample_tasks = [
                    {
                        'id': 1,
                        'wbs': '1',
                        'title': 'Project Kickoff',
                        'description': 'Initial project meeting',
                        'dependencies': '',
                        'owner': 'John Doe',
                        'percentComplete': 100,
                        'startDate': '2019-01-25',
                        'endDate': '2019-02-01',
                        'duration': 7,
                        'milestone': True
                    },
                    {
                        'id': 2,
                        'wbs': '2',
                        'title': 'Planning Phase',
                        'description': 'Project planning activities',
                        'dependencies': '1',
                        'owner': 'Jane Smith',
                        'percentComplete': 80,
                        'startDate': '2019-02-01',
                        'endDate': '2019-03-15',
                        'duration': 42,
                        'milestone': False
                    },
                    {
                        'id': 3,
                        'wbs': '2.1',
                        'title': 'Assemble Resources',
                        'description': 'Gather team and resources',
                        'dependencies': '2',
                        'owner': 'Jane Smith',
                        'percentComplete': 100,
                        'startDate': '2019-02-01',
                        'endDate': '2019-02-15',
                        'duration': 14,
                        'milestone': False
                    },
                    {
                        'id': 4,
                        'wbs': '2.2',
                        'title': 'Working Plans',
                        'description': 'Create detailed plans',
                        'dependencies': '2.1',
                        'owner': 'Robert Johnson',
                        'percentComplete': 100,
                        'startDate': '2019-02-15',
                        'endDate': '2019-03-01',
                        'duration': 14,
                        'milestone': False
                    },
                    {
                        'id': 5,
                        'wbs': '2.3',
                        'title': 'Subcontractor Selection',
                        'description': 'Select subcontractors',
                        'dependencies': '2.2',
                        'owner': 'Sarah Williams',
                        'percentComplete': 90,
                        'startDate': '2019-03-01',
                        'endDate': '2019-03-15',
                        'duration': 14,
                        'milestone': False
                    },
                    {
                        'id': 6,
                        'wbs': '3',
                        'title': 'Development Phase I',
                        'description': 'First development phase',
                        'dependencies': '2',
                        'owner': 'Michael Brown',
                        'percentComplete': 70,
                        'startDate': '2019-03-15',
                        'endDate': '2019-06-30',
                        'duration': 107,
                        'milestone': False
                    },
                    {
                        'id': 7,
                        'wbs': '4',
                        'title': 'Beta Release',
                        'description': 'Beta version release',
                        'dependencies': '3',
                        'owner': 'Michael Brown',
                        'percentComplete': 0,
                        'startDate': '2019-06-30',
                        'endDate': '2019-06-30',
                        'duration': 0,
                        'milestone': True
                    }
                ]
                
                project_info['tasks'] = sample_tasks
                
                # Create sample resources
                sample_resources = [
                    {
                        'id': 1,
                        'name': 'John Doe',
                        'role': 'Project Manager',
                        'allocation': [
                            {'date': '2019-01-25', 'hours': 8},
                            {'date': '2019-01-28', 'hours': 8},
                            {'date': '2019-01-29', 'hours': 8},
                            {'date': '2019-01-30', 'hours': 8},
                            {'date': '2019-01-31', 'hours': 8}
                        ]
                    },
                    {
                        'id': 2,
                        'name': 'Jane Smith',
                        'role': 'Business Analyst',
                        'allocation': [
                            {'date': '2019-02-01', 'hours': 8},
                            {'date': '2019-02-04', 'hours': 8},
                            {'date': '2019-02-05', 'hours': 8},
                            {'date': '2019-02-06', 'hours': 8},
                            {'date': '2019-02-07', 'hours': 8},
                            {'date': '2019-02-08', 'hours': 8}
                        ]
                    },
                    {
                        'id': 3,
                        'name': 'Robert Johnson',
                        'role': 'Developer',
                        'allocation': [
                            {'date': '2019-02-15', 'hours': 8},
                            {'date': '2019-02-18', 'hours': 8},
                            {'date': '2019-02-19', 'hours': 8},
                            {'date': '2019-02-20', 'hours': 8},
                            {'date': '2019-02-21', 'hours': 8},
                            {'date': '2019-02-22', 'hours': 8}
                        ]
                    },
                    {
                        'id': 4,
                        'name': 'Sarah Williams',
                        'role': 'Developer',
                        'allocation': [
                            {'date': '2019-03-01', 'hours': 8},
                            {'date': '2019-03-04', 'hours': 8},
                            {'date': '2019-03-05', 'hours': 8},
                            {'date': '2019-03-06', 'hours': 8},
                            {'date': '2019-03-07', 'hours': 8},
                            {'date': '2019-03-08', 'hours': 8}
                        ]
                    },
                    {
                        'id': 5,
                        'name': 'Michael Brown',
                        'role': 'Lead Developer',
                        'allocation': [
                            {'date': '2019-03-15', 'hours': 8},
                            {'date': '2019-03-18', 'hours': 8},
                            {'date': '2019-03-19', 'hours': 8},
                            {'date': '2019-03-20', 'hours': 8},
                            {'date': '2019-03-21', 'hours': 8},
                            {'date': '2019-03-22', 'hours': 8}
                        ]
                    }
                ]
                
                project_info['resources'] = sample_resources
            
            # Add the project to session state
            st.session_state['projects'].append(project_info)
            st.session_state['current_project'] = project_info
            
            return project_info
            
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None
    
    return None

# Function to generate gantt chart data
def generate_gantt_chart_data(tasks):
    gantt_data = []
    
    for task in tasks:
        if 'startDate' in task and 'endDate' in task and task['startDate'] and task['endDate']:
            # Convert string dates to datetime
            start_date = pd.to_datetime(task['startDate'])
            end_date = pd.to_datetime(task['endDate'])
            
            # Create task entry
            task_data = dict(
                Task=task['title'],
                Start=start_date,
                Finish=end_date,
                Resource=task['owner'] if 'owner' in task else '',
                Complete=task['percentComplete'] if 'percentComplete' in task else 0,
                ID=task['id']
            )
            
            gantt_data.append(task_data)
    
    return pd.DataFrame(gantt_data)

# Function to generate resource utilization data
def generate_resource_utilization(resources, start_date=None, end_date=None):
    if not resources:
        return pd.DataFrame()
    
    # If no dates specified, use the range from resource allocations
    all_dates = []
    for resource in resources:
        if 'allocation' in resource:
            for alloc in resource['allocation']:
                if 'date' in alloc:
                    all_dates.append(pd.to_datetime(alloc['date']))
    
    if not all_dates:
        # No allocation data found, use default range
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)
    else:
        if not start_date:
            start_date = min(all_dates)
        if not end_date:
            end_date = max(all_dates)
    
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Create a dataframe with all resources and dates
    resource_data = []
    
    for resource in resources:
        resource_name = resource['name']
        
        # Create a dictionary of date -> hours for this resource
        allocation_dict = {}
        if 'allocation' in resource:
            for alloc in resource['allocation']:
                if 'date' in alloc and 'hours' in alloc:
                    alloc_date = pd.to_datetime(alloc['date'])
                    allocation_dict[alloc_date] = alloc['hours']
        
        # Add a row for each date in the range
        for date in date_range:
            # Skip weekends (Saturday = 5, Sunday = 6)
            if date.weekday() >= 5:
                continue
                
            hours = allocation_dict.get(date, 0)
            resource_data.append({
                'Resource': resource_name,
                'Date': date,
                'Hours': hours
            })
    
    return pd.DataFrame(resource_data)

# Function to check if a date is a weekend
def is_weekend(date):
    return pd.to_datetime(date).weekday() >= 5

# Function to format a date cell, highlighting weekends
def format_date_cell(date):
    date_str = pd.to_datetime(date).strftime('%b %d')
    if is_weekend(date):
        return f"<span style='color: #999;'>{date_str}</span>"
    return date_str

# Function to format a task cell for displaying in the Gantt chart
def format_task_cell(task):
    if task.get('milestone', False):
        return f"<span class='gantt-milestone'>🔴 {task['title']}</span>"
    return task['title']

# Function to create the project dashboard
def project_dashboard(project):
    st.markdown(f"<h1>{project['name']}</h1>", unsafe_allow_html=True)
    
    # Project Overview Metrics
    total_tasks = len(project['tasks'])
    completed_tasks = sum(1 for task in project['tasks'] if task.get('percentComplete', 0) == 100)
    in_progress_tasks = sum(1 for task in project['tasks'] if 0 < task.get('percentComplete', 0) < 100)
    not_started_tasks = sum(1 for task in project['tasks'] if task.get('percentComplete', 0) == 0)
    
    # Calculate project start and end dates
    start_dates = [pd.to_datetime(task['startDate']) for task in project['tasks'] if 'startDate' in task and task['startDate']]
    end_dates = [pd.to_datetime(task['endDate']) for task in project['tasks'] if 'endDate' in task and task['endDate']]
    
    if start_dates and end_dates:
        project_start = min(start_dates)
        project_end = max(end_dates)
        project_duration = (project_end - project_start).days
    else:
        project_start = "N/A"
        project_end = "N/A"
        project_duration = 0
    
    # Calculate overall project completion
    if total_tasks > 0:
        total_completion = sum(task.get('percentComplete', 0) for task in project['tasks']) / total_tasks
    else:
        total_completion = 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", total_tasks)
        st.progress(1.0)
    
    with col2:
        st.metric("Completed", f"{completed_tasks} ({int(completed_tasks/total_tasks*100 if total_tasks else 0)}%)")
        st.progress(completed_tasks/total_tasks if total_tasks else 0)
    
    with col3:
        st.metric("In Progress", f"{in_progress_tasks} ({int(in_progress_tasks/total_tasks*100 if total_tasks else 0)}%)")
        st.progress(in_progress_tasks/total_tasks if total_tasks else 0)
    
    with col4:
        st.metric("Not Started", f"{not_started_tasks} ({int(not_started_tasks/total_tasks*100 if total_tasks else 0)}%)")
        st.progress(not_started_tasks/total_tasks if total_tasks else 0)
    
    # Project Timeline
    if isinstance(project_start, datetime) and isinstance(project_end, datetime):
        st.markdown("### Project Timeline")
        st.markdown(f"**Start Date:** {project_start.strftime('%b %d, %Y')} | **End Date:** {project_end.strftime('%b %d, %Y')} | **Duration:** {project_duration} days")
        st.progress(total_completion)
        st.markdown(f"**Overall Progress:** {int(total_completion * 100)}%")
    
    # Tabs for different project views
    tab1, tab2, tab3, tab4 = st.tabs(["Gantt Chart", "Resource Utilization", "Task List", "Analytics"])
    
    with tab1:
        st.markdown("### Gantt Chart")
        gantt_df = generate_gantt_chart_data(project['tasks'])
        
        if not gantt_df.empty:
            fig = ff.create_gantt(
                gantt_df, 
                colors={
                    'Task': '#3498db',
                    'Milestone': '#e74c3c'
                },
                index_col='ID',
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True
            )
            
            # Customize layout
            fig.update_layout(
                autosize=True,
                height=600,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor='rgba(255,255,255,0.9)',
                paper_bgcolor='rgba(255,255,255,0.9)',
                title_font=dict(size=24, color='#2c3e50'),
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            # Add dependency lines (this is a simplified approach)
            for task in project['tasks']:
                if 'dependencies' in task and task['dependencies']:
                    if isinstance(task['dependencies'], str):
                        deps = task['dependencies'].split(',')
                        for dep in deps:
                            try:
                                # Try to find the dependency
                                dep_id = int(dep.strip())
                                dep_task = next((t for t in project['tasks'] if t['id'] == dep_id), None)
                                
                                if dep_task and 'endDate' in dep_task and 'startDate' in task:
                                    # Add a line from dependency end to task start
                                    dep_end = pd.to_datetime(dep_task['endDate'])
                                    task_start = pd.to_datetime(task['startDate'])
                                    
                                    # You would add a line here in a more complex implementation
                                    # This is simplified for this example
                                    pass
                            except:
                                pass
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks with dates found. Add task dates to view the Gantt chart.")
    
    with tab2:
        st.markdown("### Resource Utilization")
        
        if project['resources']:
            # Create resource utilization chart
            resource_df = generate_resource_utilization(project['resources'])
            
            if not resource_df.empty:
                # Pivot the data for plotting
                pivot_df = resource_df.pivot_table(
                    index='Date', 
                    columns='Resource', 
                    values='Hours',
                    fill_value=0
                ).reset_index()
                
                # Melt the data for easier plotting
                melted_df = pd.melt(
                    pivot_df,
                    id_vars='Date',
                    var_name='Resource',
                    value_name='Hours'
                )
                
                # Create the chart
                fig = px.bar(
                    melted_df, 
                    x='Date', 
                    y='Hours', 
                    color='Resource',
                    title='Daily Resource Allocation',
                    labels={'Hours': 'Hours Allocated', 'Date': 'Date', 'Resource': 'Team Member'},
                    height=500
                )
                
                # Highlight weekends
                for date in pivot_df['Date']:
                    if is_weekend(date):
                        fig.add_shape(
                            type="rect",
                            x0=date,
                            x1=date + pd.Timedelta(days=1),
                            y0=0,
                            y1=melted_df['Hours'].max() + 1,
                            fillcolor="lightgrey",
                            opacity=0.3,
                            layer="below",
                            line_width=0,
                        )
                
                # Add a horizontal line at 8 hours (standard workday)
                fig.add_shape(
                    type="line",
                    x0=pivot_df['Date'].min(),
                    y0=8,
                    x1=pivot_df['Date'].max(),
                    y1=8,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                # Format the chart
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Hours Allocated",
                    legend_title="Team Member",
                    barmode='stack',
                    height=500,
                    margin=dict(l=10, r=10, t=50, b=50),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show resource details
                st.markdown("### Resource Details")
                for resource in project['resources']:
                    st.markdown(f"""
                    <div class="resource-card">
                        <h4>{resource['name']}</h4>
                        <p><strong>Role:</strong> {resource['role']}</p>
                        <p><strong>Total Allocation:</strong> {sum(alloc['hours'] for alloc in resource.get('allocation', []))} hours</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No resource allocation data found.")
        else:
            st.info("No resources found for this project.")
    
    with tab3:
        st.markdown("### Task List")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["Not Started", "In Progress", "Completed"],
                default=["Not Started", "In Progress", "Completed"]
            )
        
        with col2:
            if project['resources']:
                resource_names = [resource['name'] for resource in project['resources']]
                resource_filter = st.multiselect(
                    "Resource",
                    resource_names,
                    default=resource_names
                )
            else:
                resource_filter = []
        
        # Apply filters
        filtered_tasks = project['tasks']
        
        if status_filter:
            status_map = {
                "Not Started": 0,
                "In Progress": lambda x: 0 < x < 100,
                "Completed": 100
            }
            
            filtered_tasks = [
                task for task in filtered_tasks
                if any(
                    status_map[status] == task.get('percentComplete', 0) 
                    if not callable(status_map[status]) 
                    else status_map[status](task.get('percentComplete', 0))
                    for status in status_filter
                )
            ]
        
        if resource_filter:
            filtered_tasks = [
                task for task in filtered_tasks
                if 'owner' in task and task['owner'] in resource_filter
            ]
        
        # Sort tasks by start date
        filtered_tasks = sorted(
            filtered_tasks, 
            key=lambda x: pd.to_datetime(x.get('startDate', '9999-12-31'))
        )
        
        # Display tasks
        for task in filtered_tasks:
            # Skip empty tasks
            if not task.get('title'):
                continue
                
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                task_class = "task-card"
                if task.get('milestone', False):
                    task_class += " milestone-card"
                    
                st.markdown(f"""
                <div class="{task_class}">
                    <h4>{task['title']}</h4>
                    <p><small>ID: {task.get('wbs', task['id'])}</small></p>
                    <p>{task.get('description', '')}</p>
                    <div style="display: flex; justify-content: space-between;">
                        <div><strong>Start:</strong> {task.get('startDate', 'N/A')}</div>
                        <div><strong>End:</strong> {task.get('endDate', 'N/A')}</div>
                        <div><strong>Duration:</strong> {task.get('duration', 'N/A')} days</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="task-card" style="text-align: center;">
                    <h4>Owner</h4>
                    <p>{task.get('owner', 'Unassigned')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="task-card" style="text-align: center;">
                    <h4>Progress</h4>
                    <p>{task.get('percentComplete', 0)}%</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(task.get('percentComplete', 0) / 100)
    
    with tab4:
        st.markdown("### Project Analytics")
        
        # Create columns for metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Task distribution by status
            status_data = {
                'Status': ['Not Started', 'In Progress', 'Completed'],
                'Count': [
                    sum(1 for task in project['tasks'] if task.get('percentComplete', 0) == 0),
                    sum(1 for task in project['tasks'] if 0 < task.get('percentComplete', 0) < 100),
                    sum(1 for task in project['tasks'] if task.get('percentComplete', 0) == 100)
                ]
            }
            
            status_df = pd.DataFrame(status_data)
            
            fig = px.pie(
                status_df, 
                values='Count', 
                names='Status',
                title='Task Status Distribution',
                color_discrete_sequence=px.colors.sequential.Blues,
                hole=0.4
            )
            
            fig.update_layout(margin=dict(t=50, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Task distribution by resource
            if project['resources']:
                resource_task_counts = {}
                for task in project['tasks']:
                    if 'owner' in task and task['owner']:
                        if task['owner'] in resource_task_counts:
                            resource_task_counts[task['owner']] += 1
                        else:
                            resource_task_counts[task['owner']] = 1
                
                resource_data = {
                    'Resource': list(resource_task_counts.keys()),
                    'Tasks': list(resource_task_counts.values())
                }
                
                resource_df = pd.DataFrame(resource_data)
                
                if not resource_df.empty:
                    fig = px.bar(
                        resource_df, 
                        x='Resource', 
                        y='Tasks',
                        title='Tasks per Resource',
                        color='Tasks',
                        color_continuous_scale='Blues'
                    )
                    
                    fig.update_layout(margin=dict(t=50, b=20), height=300)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No resource data available.")
        
        # Timeline of task completion
        st.markdown("### Task Completion Timeline")
        
        # Create a dataframe of tasks with dates
        timeline_tasks = [task for task in project['tasks'] if 'startDate' in task and 'endDate' in task]
        
        if timeline_tasks:
            # Create a dataframe for the timeline
            timeline_data = []
            
            for task in timeline_tasks:
                timeline_data.append({
                    'Task': task['title'],
                    'Start': pd.to_datetime(task['startDate']),
                    'End': pd.to_datetime(task['endDate']),
                    'Complete': task.get('percentComplete', 0),
                    'Milestone': task.get('milestone', False)
                })
            
            timeline_df = pd.DataFrame(timeline_data)
            
            # Sort by start date
            timeline_df = timeline_df.sort_values('Start')
            
            # Create the chart
            fig = px.timeline(
                timeline_df, 
                x_start='Start', 
                x_end='End', 
                y='Task',
                color='Complete',
                color_continuous_scale='Blues',
                hover_data=['Complete'],
                labels={'Task': 'Task Name', 'Start': 'Start Date', 'End': 'End Date', 'Complete': '% Complete'}
            )
            
            # Format the chart
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Task",
                height=500,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            
            # Add milestone markers
            for i, task in enumerate(timeline_df.itertuples()):
                if task.Milestone:
                    fig.add_scatter(
                        x=[task.End], 
                        y=[task.Task],
                        mode='markers',
                        marker=dict(symbol='diamond', size=12, color='red'),
                        name='Milestone',
                        showlegend=False
                    )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No task timeline data available.")

# Main application
def main():
    # Check if user is logged in
    if not st.session_state['logged_in']:
        login_screen()
        return
    
    # Sidebar for navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3209/3209265.png", width=100)
        st.markdown(f"<h2>Welcome, {st.session_state['username']}</h2>", unsafe_allow_html=True)
        
        # Navigation menu
        selected = option_menu(
            "Navigation",
            ["Dashboard", "Projects", "Resources", "Settings", "Logout"],
            icons=["house", "clipboard-data", "people", "gear", "box-arrow-right"],
            menu_icon="cast",
            default_index=0,
        )
        
        # Project selector (if on Projects page)
        if selected == "Projects" and st.session_state['projects']:
            st.divider()
            st.write("Select a project:")
            
            for project in st.session_state['projects']:
                if st.button(project['name'], key=f"btn_{project['id']}"):
                    st.session_state['current_project'] = project
                    st.session_state['selected_task'] = None
                    st.session_state['show_task_details'] = False
    
    # Main content area
    if selected == "Dashboard":
        st.markdown("# Dashboard")
        
        # Display summary of all projects
        if st.session_state['projects']:
            # Create metrics
            total_projects = len(st.session_state['projects'])
            total_tasks = sum(len(project['tasks']) for project in st.session_state['projects'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Projects", total_projects)
            
            with col2:
                st.metric("Total Tasks", total_tasks)
            
            with col3:
                st.metric("Active Projects", total_projects)
            
            # Project progress cards
            st.markdown("### Project Progress")
            
            for project in st.session_state['projects']:
                # Calculate project completion
                if project['tasks']:
                    completion = sum(task.get('percentComplete', 0) for task in project['tasks']) / len(project['tasks'])
                else:
                    completion = 0
                
                # Display project card
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"#### {project['name']}")
                    st.progress(completion / 100)
                
                with col2:
                    st.markdown(f"**{int(completion)}%**")
                    if st.button("View", key=f"view_{project['id']}"):
                        st.session_state['current_project'] = project
                        st.session_state['selected_task'] = None
                        st.session_state['show_task_details'] = False
                        st.experimental_rerun()
                
                st.divider()
        else:
            st.info("No projects found. Upload a project file to get started.")
            
            # Sample project card
            st.markdown("### Sample Project")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("#### Sample Project")
                st.progress(0.65)
            
            with col2:
                st.markdown("**65%**")
                st.button("View", key="view_sample", disabled=True)
    
    elif selected == "Projects":
        if st.session_state['current_project']:
            # Display the current project
            project_dashboard(st.session_state['current_project'])
        else:
            st.markdown("# Projects")
            st.info("No project selected. Upload a project file or select a project from the sidebar.")
            
            # Upload new project
            st.markdown("### Upload Project")
            uploaded_project = file_uploader()
            
            if uploaded_project:
                st.success("Project uploaded successfully!")
                st.experimental_rerun()
    
    elif selected == "Resources":
        st.markdown("# Resource Management")
        
        if st.session_state['current_project'] and st.session_state['current_project']['resources']:
            # Display resource information
            resources = st.session_state['current_project']['resources']
            
            # Resource metrics
            total_resources = len(resources)
            total_allocation = sum(
                sum(alloc['hours'] for alloc in resource.get('allocation', []))
                for resource in resources
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Resources", total_resources)
            
            with col2:
                st.metric("Total Allocation", f"{total_allocation} hours")
            
            with col3:
                avg_per_resource = total_allocation / total_resources if total_resources > 0 else 0
                st.metric("Avg. Per Resource", f"{int(avg_per_resource)} hours")
            
            # Resource utilization chart
            st.markdown("### Resource Utilization")
            
            # Create resource utilization chart
            resource_df = generate_resource_utilization(resources)
            
            if not resource_df.empty:
                # Pivot the data for plotting
                pivot_df = resource_df.pivot_table(
                    index='Date', 
                    columns='Resource', 
                    values='Hours',
                    fill_value=0
                ).reset_index()
                
                # Create chart for daily utilization
                daily_fig = px.area(
                    pivot_df,
                    x='Date',
                    y=pivot_df.columns[1:],  # All columns except 'Date'
                    title='Daily Resource Allocation',
                    labels={'value': 'Hours', 'variable': 'Resource'},
                    height=400
                )
                
                # Highlight weekends
                for date in pivot_df['Date']:
                    if is_weekend(date):
                        daily_fig.add_shape(
                            type="rect",
                            x0=date,
                            x1=date + pd.Timedelta(days=1),
                            y0=0,
                            y1=resource_df['Hours'].max() * len(resources) + 5,
                            fillcolor="lightgrey",
                            opacity=0.3,
                            layer="below",
                            line_width=0,
                        )
                
                # Add a horizontal line at 8 hours per resource (standard workday)
                daily_fig.add_shape(
                    type="line",
                    x0=pivot_df['Date'].min(),
                    y0=8 * len(resources),
                    x1=pivot_df['Date'].max(),
                    y1=8 * len(resources),
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                # Format the chart
                daily_fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Total Hours Allocated",
                    legend_title="Team Member",
                    height=400,
                    margin=dict(l=10, r=10, t=50, b=50),
                )
                
                st.plotly_chart(daily_fig, use_container_width=True)
                
                # Create chart for resource breakdown
                resource_summary = resource_df.groupby('Resource')['Hours'].sum().reset_index()
                
                breakdown_fig = px.pie(
                    resource_summary, 
                    values='Hours', 
                    names='Resource',
                    title='Resource Allocation Breakdown',
                    hole=0.4
                )
                
                breakdown_fig.update_layout(margin=dict(t=50, b=20), height=300)
                st.plotly_chart(breakdown_fig, use_container_width=True)
                
                # Resource details
                st.markdown("### Resource Details")
                
                for resource in resources:
                    # Calculate total allocation for this resource
                    total_hours = sum(alloc['hours'] for alloc in resource.get('allocation', []))
                    
                    # Display resource card
                    st.markdown(f"""
                    <div class="resource-card">
                        <h4>{resource['name']}</h4>
                        <p><strong>Role:</strong> {resource['role']}</p>
                        <p><strong>Total Allocation:</strong> {total_hours} hours</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show allocation chart for this resource
                    resource_alloc = [{'Date': pd.to_datetime(alloc['date']), 'Hours': alloc['hours']} 
                                    for alloc in resource.get('allocation', [])]
                    
                    if resource_alloc:
                        resource_alloc_df = pd.DataFrame(resource_alloc)
                        
                        fig = px.bar(
                            resource_alloc_df,
                            x='Date',
                            y='Hours',
                            title=f'Allocation for {resource["name"]}',
                            height=200
                        )
                        
                        # Add a horizontal line at 8 hours (standard workday)
                        fig.add_shape(
                            type="line",
                            x0=resource_alloc_df['Date'].min(),
                            y0=8,
                            x1=resource_alloc_df['Date'].max(),
                            y1=8,
                            line=dict(color="red", width=1, dash="dash"),
                        )
                        
                        fig.update_layout(margin=dict(l=10, r=10, t=30, b=20))
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No resource data available. Select a project with resources to view this page.")
    
    elif selected == "Settings":
        st.markdown("# Settings")
        
        # Application settings
        st.markdown("### Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Theme",
                ["Light", "Dark", "System Default"],
                index=0
            )
        
        with col2:
            date_format = st.selectbox(
                "Date Format",
                ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
                index=2
            )
        
        # User preferences
        st.markdown("### User Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            notifications = st.checkbox("Enable Notifications", value=True)
        
        with col2:
            email_reports = st.checkbox("Email Weekly Reports", value=False)
        
        # Save settings button
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    
    elif selected == "Logout":
        st.markdown("# Logout")
        st.warning("Are you sure you want to log out?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Yes, Logout"):
                logout()
                st.success("Logged out successfully!")
                time.sleep(1)
                st.experimental_rerun()
        
        with col2:
            if st.button("Cancel"):
                st.experimental_rerun()

if __name__ == "__main__":
    main()
