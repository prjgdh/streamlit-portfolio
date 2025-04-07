import streamlit as st
import pandas as pd
import io
import datetime
from project import save_project_data

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