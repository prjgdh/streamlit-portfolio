import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils_py import parse_date

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