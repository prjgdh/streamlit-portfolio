import streamlit as st
import pandas as pd
import numpy as np
import datetime
import base64
import json
import os

# Import custom modules
from auth import init_users, login_user, register_user, user_exists, authenticate_project
from project import (init_project_data, load_project_data, save_project_data, 
                   create_project, get_user_projects)
from utils import process_uploaded_excel, export_to_excel
from visualization import (create_gantt_chart, create_resource_utilization_chart, 
                         create_task_completion_chart, create_milestone_timeline)
from styles import load_css

# Set page config
st.set_page_config(
    page_title="Project Management App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS styles
load_css()

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
                            'scheduled_start': task_start.strftime('%d/%m/%Y'),
                            'scheduled_finish': task_finish.strftime('%d/%m/%Y'),
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
                            'start_date': ms_start.strftime('%d/%m/%Y'),
                            'end_date': ms_end.strftime('%d/%m/%Y'),
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
                                from utils import parse_date
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
                """)
                
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
    main()