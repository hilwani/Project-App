import streamlit as st 
import sqlite3 
import datetime 
import time
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import numpy as np
import statsmodels.api as sm
from streamlit_calendar import calendar
from calendar_page import show_calendar_page
# from workspace_page import workspace_page
import io  # For handling in-memory file buffers
import logging
import streamlit.components.v1 as components
import json
import base64 
import plotly.graph_objects as go 
from visualizations import ( 
    plot_project_timeline, 
    plot_budget_comparison,  
    plot_completion_heatmap, 
    plot_duration_variance,
    plot_project_health,
    plot_plan_vs_actual_gantt, 
    plot_duration_variance, 
    plot_duration_comparison 
)

import streamlit as st
st.set_page_config(
    page_title="Project Management App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Only THEN import other modules
from workspace_page import workspace_page



# # Page Config (MUST BE THE FIRST STREAMLIT COMMAND)
# st.set_page_config(page_title="Project Management App", layout="wide") 



hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
div[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="manage-app-button"] {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)



# Add this after your page config
components.html("""
<script>
    // Function to handle navigation from cards
    function navigateToPage(page) {
        window.parent.postMessage({
            streamlit: {
                type: 'streamlit:componentMessage',
                data: {page: page}
            }
        }, '*');
    }
</script>
""", height=0)



# Add this right after the page config
st.markdown("""
<style>
   /* Uniform button styling */
    .stButton>button {
        width: 200px !important;
        height: 42px !important;
        margin: 8px auto !important;
        display: block !important;
        background-color: #E1F0FF !important;
        color: #2c3e50 !important;
        border: 1px solid #B8D4FF !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
               
            
    .stButton>button:hover {
        background-color: #D0E2FF !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton>button[kind="primary"] {
        background-color: #4E8BF5 !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(78, 139, 245, 0.3) !important;
    }

    /* Ensures all columns use same spacing */
    [data-testid="column"] {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }        

    /* Remove default sidebar padding */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    
    /* Ensure title sticks to top */
    .stSidebar .stMarkdown:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }        

            /* Workspace icon styling */
    .stButton>button[kind="secondary"] div div {
        display: flex;
        align-items: center;
        justify-content: center;
    }

</style>
""", unsafe_allow_html=True)




# Define priority colors
priority_colors = {
            "High": "#FF0000",  # Red
            "Medium": "#FFA500",  # Orange
            "Low": "#32CD32"  # Green
        }        


# Initialize session state for color scheme
if "color_scheme" not in st.session_state:
    st.session_state.color_scheme = {
        "primary": "#4E8BF5",  # Cool blue
        "secondary": "#6BB9F0",  # Light blue
        "background": "#F5F9FF",  # Very light blue
        "text": "#333333",  # Dark gray for text
        "card": "#FFFFFF",  # White for cards
        "popup": "#FFFFFF"  # White for popups
    }

# Custom CSS
custom_css = f"""
<style>
/* Profile section styling */
    .sidebar-profile {{
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e0e0e0;
    }}
    .profile-pic {{
        border-radius: 50%;
        object-fit: cover;
        margin-right: 1rem;
    }}
    .profile-name {{
        font-weight: 600;
        margin-bottom: 0;
    }}
    .profile-role {{
        font-size: 0.8rem;
        color: #666;
        margin-top: 0;
    }}

    /* General App Styling */
    .stApp {{
        background-color: {st.session_state.color_scheme['background']};
        color: {st.session_state.color_scheme['text']};
        font-family: 'Roboto', sans-serif;
    }}

    /* Card Styling */
    .card {{
        background-color: {st.session_state.color_scheme['background']};
        border: 1px solid {st.session_state.color_scheme['primary']};
        border-radius: 8px;
        padding: 16px;
        margin: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }}

    .card-title {{
        color: {st.session_state.color_scheme['primary']};
        font-size: 1.25rem;
        font-weight: bold;
        margin-bottom: 10px;
    }}

    .card-content {{
        color: {st.session_state.color_scheme['text']};
        font-size: 0.9rem;
        margin-bottom: 10px;
    }}

    .card-footer {{
        margin-top: 10px;
        font-size: 0.8rem;
        color: {st.session_state.color_scheme['secondary']};
    }}

    /* Buttons */
    .stButton>button {{
        margin: 5px;
    }}

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        margin: 5px 0;
    }}

    /* Tables */
    .stDataFrame {{
        margin: 10px 0;
    }}

    /* Progress Bar */
    .stProgress>div>div>div {{
        margin: 5px 0;
    }}

    /* Media Queries for Responsive Design */
    @media (max-width: 768px) {{
        /* Adjust card layout for smaller screens */
        .card {{
            width: 100%;
            margin: 10px 0;
        }}

        /* Make buttons full width on small screens */
        .stButton>button {{
            width: 100%;
        }}

        /* Adjust font sizes for smaller screens */
        .card-title {{
            font-size: 1rem;
        }}

        .card-content {{
            font-size: 0.8rem;
        }}

        /* Stack columns vertically on small screens */
        .stColumns {{
            flex-direction: column;
        }}

    /* NEW TIMELINE VISUALIZATION STYLES */
    .stPlotlyChart {{
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .stDownloadButton>button {{
        width: 100% !important;
    }}

    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)



# Add this to your existing CSS section (after the existing card styles)
st.markdown("""
<style>
    /* Dashboard metric cards - matching admin style */
    .dashboard-metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.2rem;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        height: 100%;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .dashboard-metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .dashboard-metric-card .metric-title {
        display: flex; 
        align-items: center; 
        margin-bottom: 8px;
    }
    .dashboard-metric-card .metric-icon {
        font-size: 1.5rem; 
        margin-right: 8px;
    }
    .dashboard-metric-card .metric-name {
        font-size: 0.9rem; 
        color: #666;
    }
    .dashboard-metric-card .metric-value {
        font-size: 1.8rem; 
        font-weight: 700; 
        color: #2c3e50; 
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)




# Database Initialization
def init_db():
    conn = sqlite3.connect('project_management.db')
    c = conn.cursor()
    
    # Recreate tables with ON DELETE CASCADE
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            budget REAL,  
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if the budget column exists, and if not, add it
    c.execute("PRAGMA table_info(projects)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'budget' not in column_names:
        c.execute('ALTER TABLE projects ADD COLUMN budget REAL')  # Add budget column


    # Check if projects table has status column
    c.execute("PRAGMA table_info(projects)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
     
    if 'status' not in column_names:
       c.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'Planning'")
            

    
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deadline TEXT,
            time_spent INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'Medium',
            recurrence TEXT,
            assigned_to INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    ''')


    
    # Check if the actual_time_spent column exists, and if not, add to the tasks table:
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]

    if 'actual_time_spent' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN actual_time_spent REAL')  # Add actual_time_spent column
       
    
    # Check if the start_date column exists, and if not, add it
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]

    if 'start_date' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN start_date TEXT') 

    # In the init_db function, add these columns to the tasks table:
    if 'actual_start_date' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN actual_start_date TEXT')  
    if 'actual_deadline' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN actual_deadline TEXT')     
        
        # Check if the budget column exists, and if not, add it
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'budget' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN budget REAL') 


    # Check if the actual_cost and budget_variance columns exist, and if not, add them
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'actual_cost' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN actual_cost REAL')  # Add actual_cost column
    
    if 'budget_variance' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN budget_variance REAL')  # Add budget_variance column




    
    c.execute('''
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            depends_on_task_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_task_id) REFERENCES tasks (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    

    c.execute('''
        CREATE TABLE IF NOT EXISTS project_team (
            project_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            PRIMARY KEY (project_id, user_id)
        )
    ''')
    

    c.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    ''')
    
    # Add this new table for storing app settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE,
            setting_value BLOB
        )
    ''')

    # Create users table with additional columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User',  -- Default role is 'User'
            first_name TEXT,  -- New: First Name
            last_name TEXT,   -- New: Last Name
            company TEXT,     -- New: Company
            job_title TEXT,   -- New: Job Title
            department TEXT,  -- New: Department
            email TEXT,       -- New: Email
            phone TEXT        -- New: Phone
            profile_picture BLOB  -- New: Profile Picture (stored as binary data)  
            last_login TEXT,  -- New: Last login timestamp
            login_count INTEGER DEFAULT 0,  -- New: Total logins
            is_active BOOLEAN DEFAULT 1  -- New: Active status
              
        )
    ''')

    # Create table discussion topics
    c.execute('''
        CREATE TABLE IF NOT EXISTS discussion_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        
         )
    ''')
    
    # Create table discussion messages
    c.execute('''
        CREATE TABLE IF NOT EXISTS discussion_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES discussion_topics(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        
         )
    ''')



 # Update subtasks table with additional columns
    c.execute("PRAGMA table_info(subtasks)")
    columns = [column[1] for column in c.fetchall()]
    
    # Add missing columns if they don't exist
    new_columns = {
        "description": "TEXT",
        "start_date": "TEXT",
        "deadline": "TEXT",
        "priority": "TEXT DEFAULT 'Medium'",
        "assigned_to": "INTEGER",
        "budget": "REAL",
        "time_spent": "INTEGER DEFAULT 0"
    }
    
    for column_name, column_type in new_columns.items():
        if column_name not in columns:
            c.execute(f"ALTER TABLE subtasks ADD COLUMN {column_name} {column_type}")





    # Check if the project_id column exists, and if not, add it
    c.execute("PRAGMA table_info(attachments)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'project_id' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN project_id INTEGER') 


    # Check if the uploaded_by column exists, and if not, add it
    c.execute("PRAGMA table_info(attachments)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'uploaded_by' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN uploaded_by INTEGER') 


    # Check if the uploader_name column exists, and if not, add it
    c.execute("PRAGMA table_info(attachments)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'uploader_name' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN uploader_name TEXT')  


    # Check if the uploaded_at column exists, and if not, add it
    c.execute("PRAGMA table_info(attachments)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'uploaded_at' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN uploaded_at TEXT')
   




    # Check if the new columns exist, and if not, add them
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    new_columns = {
        "first_name": "TEXT",
        "last_name": "TEXT",
        "company": "TEXT",
        "job_title": "TEXT",
        "department": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "profile_picture":"BLOB"
    }
    
    for column_name, column_type in new_columns.items():
        if column_name not in column_names:
            c.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')

    



    # Check if the uploaded_by, uploaded_at and file_size columns exist, and if not, add them
    c.execute("PRAGMA table_info(attachments)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'uploaded_by' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN uploaded_by INTEGER')  # Add uploaded_by column
    
    if 'uploaded_at' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN uploaded_at ')  # Add uploaded_at column

    if 'file_size' not in column_names:
        c.execute('ALTER TABLE attachments ADD COLUMN file_size INTEGER')  # Add file_size column



    conn.commit()
    conn.close()



# Query Database
def query_db(query, args=(), one=False):
    conn = sqlite3.connect('project_management.db')
    cur = conn.cursor()
    
    # Debugging: Print the query and arguments
    print("Executing Query:", query)
    print("Query Arguments:", args)
    
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Initialize the database
init_db()



# Helper function to fetch projects
def fetch_tasks(project_id=None):
    """Fetch tasks with calculated budget variance and time tracking"""
    if project_id:
        query = """
            SELECT 
                t.title AS Task, 
                t.status, 
                assignee.username AS assignee, 
                t.time_spent AS "Planned Time Spent", 
                t.actual_time_spent AS "Actual Time Spent",
                p.name AS Project, 
                owner.username AS "Project Owner",  
                t.start_date AS "Planned Start Date",
                t.deadline AS "Planned Deadline",
                CASE 
                    WHEN t.start_date IS NULL OR t.deadline IS NULL THEN 'N/A'
                    ELSE ROUND(julianday(t.deadline) - julianday(t.start_date), 1) || ' days'
                END AS "Planned Duration",
                t.actual_start_date AS "Actual Start Date",
                t.actual_deadline AS "Actual Deadline",
                CASE 
                    WHEN t.actual_start_date IS NULL OR t.actual_deadline IS NULL THEN 'N/A'
                    ELSE ROUND(julianday(t.actual_deadline) - julianday(t.actual_start_date), 1) || ' days'
                END AS "Actual Duration",
                t.priority AS Priority,
                t.budget AS Budget,
                t.actual_cost AS "Actual Cost",
                CASE 
                    WHEN t.budget IS NULL OR t.actual_cost IS NULL THEN NULL
                    ELSE t.budget - t.actual_cost 
                END AS "Budget Variance"
            FROM tasks t
            LEFT JOIN users assignee ON t.assigned_to = assignee.id
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users owner ON p.user_id = owner.id
            WHERE t.project_id = ?
        """
        tasks = query_db(query, (project_id,))
    else:
        query = """
            SELECT 
                t.title AS Task, 
                t.status, 
                assignee.username AS assignee, 
                t.time_spent AS "Planned Time Spent", 
                t.actual_time_spent AS "Actual Time Spent",
                p.name AS Project, 
                owner.username AS "Project Owner",  
                t.start_date AS "Planned Start Date",
                t.deadline AS "Planned Deadline",
                CASE 
                    WHEN t.start_date IS NULL OR t.deadline IS NULL THEN 'N/A'
                    ELSE ROUND(julianday(t.deadline) - julianday(t.start_date), 1) || ' days'
                END AS "Planned Duration",
                t.actual_start_date AS "Actual Start Date",
                t.actual_deadline AS "Actual Deadline",
                CASE 
                    WHEN t.actual_start_date IS NULL OR t.actual_deadline IS NULL THEN 'N/A'
                    ELSE ROUND(julianday(t.actual_deadline) - julianday(t.actual_start_date), 1) || ' days'
                END AS "Actual Duration",
                t.priority AS Priority,
                t.budget AS Budget,
                t.actual_cost AS "Actual Cost",
                CASE 
                    WHEN t.budget IS NULL OR t.actual_cost IS NULL THEN NULL
                    ELSE t.budget - t.actual_cost 
                END AS "Budget Variance"
            FROM tasks t
            LEFT JOIN users assignee ON t.assigned_to = assignee.id
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users owner ON p.user_id = owner.id
        """
        tasks = query_db(query)
    
    return pd.DataFrame(tasks, columns=[
        "Task", "Status", "Assignee", "Planned Time Spent", "Actual Time Spent",
        "Project", "Project Owner", "Planned Start Date", "Planned Deadline", 
        "Planned Duration", "Actual Start Date", "Actual Deadline", "Actual Duration",
        "Priority", "Budget", "Actual Cost", "Budget Variance"
    ])




def display_task_table():
    """Display tasks in a table format with filtering capabilities"""
    # Fetch tasks with the updated function
    tasks_df = fetch_tasks()
    
    if tasks_df.empty:
        st.warning("No tasks found.")
        return tasks_df
    
    # Convert date columns
    tasks_df['Planned Start Date'] = pd.to_datetime(tasks_df['Planned Start Date'])
    tasks_df['Planned Deadline'] = pd.to_datetime(tasks_df['Planned Deadline'])
    tasks_df['Actual Start Date'] = pd.to_datetime(tasks_df['Actual Start Date'])
    tasks_df['Actual Deadline'] = pd.to_datetime(tasks_df['Actual Deadline'])
    
    # Create filter widgets
    with st.expander("🔍 Filter Tasks", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            project_options = ['All Projects'] + sorted(tasks_df['Project'].unique().tolist())
            selected_project = st.selectbox("Filter by Project", project_options)
        
        with col2:
            assignee_options = ['All Assignees'] + sorted(tasks_df['Assignee'].dropna().unique().tolist())
            selected_assignee = st.selectbox("Filter by Assignee", assignee_options)
        
        with col3:
            status_options = ['All Statuses'] + sorted(tasks_df['Status'].unique().tolist())
            selected_status = st.selectbox("Filter by Status", status_options)
        
        with col4:
            priority_options = ['All Priorities'] + sorted(tasks_df['Priority'].unique().tolist())
            selected_priority = st.selectbox("Filter by Priority", priority_options)

        with col5:
            owner_options = ['All Owners'] + sorted(tasks_df['Project Owner'].dropna().unique().tolist())
            selected_owner = st.selectbox("Filter by Project Owner", owner_options)
    
    # Apply filters
    filtered_df = tasks_df.copy()
    
    if selected_project != 'All Projects':
        filtered_df = filtered_df[filtered_df['Project'] == selected_project]
    
    if selected_assignee != 'All Assignees':
        filtered_df = filtered_df[filtered_df['Assignee'] == selected_assignee]
    
    if selected_status != 'All Statuses':
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    
    if selected_priority != 'All Priorities':
        filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]

    if selected_owner != 'All Owners':
        filtered_df = filtered_df[filtered_df['Project Owner'] == selected_owner]
    
    # Create a copy for display with formatted currency values
    display_df = filtered_df.copy()
    
    

 
    # Format currency columns as whole numbers
    display_df["Actual Cost"] = display_df["Actual Cost"].apply(
        lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
    )
    display_df["Budget Variance"] = display_df["Budget Variance"].apply(
        lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
    )
    display_df["Budget"] = display_df["Budget"].apply(
        lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
    )    
    
    
    
    
    # Display the formatted table
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Planned Start Date": st.column_config.DateColumn("Planned Start Date"),
            "Planned Deadline": st.column_config.DateColumn("Planned Deadline"),
            "Actual Start Date": st.column_config.DateColumn("Actual Start Date"),
            "Actual Deadline": st.column_config.DateColumn("Actual Deadline"),
            "Spent Time": st.column_config.NumberColumn("Spent Time (hours)"),
            # Note: We don't need column_config for the currency columns 
            # because we've already formatted them as strings
        }
    )
    
    # Return the original numeric DataFrame for visualizations
    return filtered_df



# Helper Functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by the user."""
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()




# Helper function to display projects as cards
def display_projects_as_cards():
    """Display projects in a professional dropdown interface for selection and management"""
    # Fetch all users for owner dropdown
    users = query_db("SELECT id, username FROM users")
    user_options = {user[0]: user[1] for user in users}

    projects = query_db("""
        SELECT id, user_id, name, description, start_date, end_date, budget 
        FROM projects
    """)
    
    if not projects:
        st.warning("No projects found in the database.")
        return

    # Success notifications
    if st.session_state.get('show_edit_success'):
        st.success("✓ Project updated successfully!")
        del st.session_state['show_edit_success']

    # Professional Project Selection Dropdown
    st.subheader("Project Management")
    project_options = {p[0]: f"{p[2]} (ID: {p[0]})" for p in projects}
    selected_project_id = st.selectbox(
        "Select Project to Manage",
        options=list(project_options.keys()),
        format_func=lambda x: project_options[x],
        placeholder="Choose a project...",
        key="project_selector"
    )
    
    # Get the selected project
    selected_project = next((p for p in projects if p[0] == selected_project_id), None)
    
    if selected_project:
        project_id, owner_id, name, description, start_date, end_date, budget = selected_project
        owner_username = user_options.get(owner_id, "Unknown")
        
        # Format budget display safely
        budget_display = "Not set"
        if budget is not None:
            try:
                budget_display = f"${float(budget):,.2f}"
            except (TypeError, ValueError):
                budget_display = "Invalid value"
        
        # Check if project is overdue
        today = datetime.now().date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today
        is_overdue = end_date_obj < today
        
        # Project Details Card with conditional coloring
        card_style = """
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        """
        
        if is_overdue:
            card_style = """
                border-left: 4px solid #ff4d4d;
                border-radius: 8px;
                padding: 16px;
                margin: 16px 0;
                background: #fff5f5;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            """
        
        with st.container():
            st.markdown(f"""
            <div style="{card_style}">
                <h3 style="margin-top:0;color:#2c3e50;">{name}</h3>
                <p><strong>Description:</strong> {description or "No description"}</p>
                <p><strong>Owner:</strong> {owner_username}</p>
                <p><strong>Start Date:</strong> {start_date}</p>
                <p><strong>Due Date:</strong> <span style="color: {'#ff4d4d' if is_overdue else 'inherit'}">{end_date}</span></p>
                <p><strong>Status:</strong> {'<span style="color:#ff4d4d">⚠️ Overdue</span>' if is_overdue else 'On track'}</p>
                <p><strong>Budget:</strong> {budget_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons - Only show if admin or project owner
            show_edit = st.session_state.user_role == "Admin" or owner_id == st.session_state.user_id
            show_delete = st.session_state.user_role == "Admin"
            
            if show_edit or show_delete:
                cols = st.columns([1,1,2])
                with cols[0]:
                    if show_edit and st.button("✏️ Edit Project", key=f"edit_{project_id}"):
                        st.session_state.editing_project_id = project_id
                        st.rerun()
                with cols[1]:
                    if show_delete and st.button("🗑️ Delete Project", type="primary", key=f"delete_{project_id}"):
                        st.session_state.deleting_project_id = project_id
                        st.rerun()

        # Edit Form
        if st.session_state.get('editing_project_id') == project_id and show_edit:
            with st.form(f"edit_form_{project_id}"):
                st.subheader(f"Edit Project: {name}")
                new_name = st.text_input("Name", value=name)
                new_desc = st.text_area("Description", value=description)
                
                if st.session_state.user_role == "Admin":
                    current_owner_name = user_options.get(owner_id, "Unknown")
                    new_owner_name = st.selectbox(
                        "Owner",
                        options=list(user_options.values()),
                        index=list(user_options.values()).index(current_owner_name) if current_owner_name in user_options.values() else 0
                    )
                    new_owner_id = [uid for uid, uname in user_options.items() if uname == new_owner_name][0]
                else:
                    new_owner_id = owner_id
                
                col1, col2 = st.columns(2)
                with col1:
                    new_start = st.date_input("Start Date", value=datetime.strptime(start_date, "%Y-%m-%d").date())
                with col2:
                    new_end = st.date_input("Due Date", value=datetime.strptime(end_date, "%Y-%m-%d").date())
                
                new_budget = st.number_input("Budget", value=float(budget) if budget else 0.0, step=0.01)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        query_db("""
                            UPDATE projects SET 
                            name=?, description=?, user_id=?, 
                            start_date=?, end_date=?, budget=?
                            WHERE id=?
                        """, (new_name, new_desc, new_owner_id, 
                              new_start, new_end, new_budget, project_id))
                        st.session_state.show_edit_success = True
                        st.session_state.editing_project_id = None
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.editing_project_id = None
                        st.rerun()

        # Delete Confirmation
        if st.session_state.get('deleting_project_id') == project_id and show_delete:
            st.warning(f"⚠️ Delete project '{name}'? This action cannot be undone!")
            st.error("All associated tasks and data will be permanently deleted!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Deletion", type="primary"):
                    delete_project(project_id)
                    st.success("Project deleted successfully")
                    st.session_state.deleting_project_id = None
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.deleting_project_id = None
                    st.rerun()
                                   
                
        





def display_tasks_as_cards(project_id):
    """Display tasks as cards for a specific project."""
    tasks = get_tasks(project_id)
    if not tasks:
        st.warning("No tasks found for this project.")
    else:
        for task in tasks:
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">{task[2]}</div>
                    <div class="card-content">
                        <p><strong>Description:</strong> {task[3]}</p>
                        <p><strong>Status:</strong> {task[4]}</p>
                        <p><strong>Priority:</strong> {task[8]}</p>
                        <p><strong>Deadline:</strong> {task[6]}</p>
                        <p><strong>Time Spent:</strong> {task[7]} hours</p>
                        <p><strong>Recurrence:</strong> {task[9] if task[9] else "None"}</p>
                        <p><strong>Assigned to:</strong> {query_db("SELECT username FROM users WHERE id=?", (task[10],), one=True)[0] if task[10] else "Unassigned"}</p>
                    </div>
                    <div class="card-footer">
                        <button onclick="editTask({task[0]})">Edit</button>
                        <button onclick="deleteTask({task[0]})">Delete</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Initialize session state for authentication, settings, and help
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "reminder_period" not in st.session_state:
    st.session_state.reminder_period = 7  # Default reminder period is 7 days
if "show_help" not in st.session_state:
    st.session_state.show_help = False  # Track help visibility
if "breadcrumbs" not in st.session_state:
    st.session_state.breadcrumbs = []  # Initialize breadcrumbs
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"  # Default page
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None
if "editing_task_project" not in st.session_state:
    st.session_state.editing_task_project = None
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True
if "color_scheme" not in st.session_state:
    # Initialize color_scheme with a default value
    st.session_state.color_scheme = {
        "primary": "#4CAF50",  # Default primary color
        "background": "#FFFFFF",  # Default background color
        "text": "#000000",  # Default text color,
    }


# Add JavaScript to detect screen size
screen_size_js = """
<script>
    function updateScreenSize() {
        const width = window.innerWidth;
        const isMobile = width <= 768;  // Define mobile screen width
        Streamlit.setComponentValue({ is_mobile: isMobile });
    }

    // Update screen size on load and resize
    window.addEventListener("load", updateScreenSize);
    window.addEventListener("resize", updateScreenSize);
</script>
"""

# Inject the JavaScript into the app
st.components.v1.html(screen_size_js, height=0)

# Get screen size from JavaScript
if "is_mobile" not in st.session_state:
    st.session_state.is_mobile = False  # Default to False (desktop)

# Update session state based on JavaScript output
screen_size = st.session_state.get("is_mobile", False)
if screen_size:
    st.session_state.is_mobile = True
else:
    st.session_state.is_mobile = False



# Custom CSS
custom_css = f"""
<style>
    .stApp {{
        background-color: {st.session_state.color_scheme['background']};
        color: {st.session_state.color_scheme['text']};
    }}
    .stButton>button {{
        background-color: {st.session_state.color_scheme['primary']};
        color: {st.session_state.color_scheme['text']};
    }}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: {st.session_state.color_scheme['background']};
        color: {st.session_state.color_scheme['text']};
    }}
    /* Add more CSS rules as needed */
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)



# User Profile Picture & Name Section at the top

with st.sidebar:
    # User Profile Section at the top - Perfectly aligned version
    if st.session_state.authenticated:
        user = query_db("""
            SELECT username, first_name, last_name, profile_picture, job_title 
            FROM users WHERE id=?
        """, (st.session_state.user_id,), one=True)
        
        if user:
            # Main container with perfect alignment
            st.markdown(f"""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 0;
                margin: -0.5rem 0 0.5rem 0;
                width: 100%;
            ">
            """, unsafe_allow_html=True)
            
            # Profile picture container (no unwanted blue circle)
            if user[3]:  # If profile picture exists
                st.markdown(f"""
                <div style="
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    overflow: hidden;
                    margin: 0 auto 8px auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #f8f9fa;    
                ">
                    <img src="data:image/png;base64,{base64.b64encode(user[3]).decode()}" 
                         style="width:100%; height:100%; object-fit: cover;"/>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Display initials if no picture (with consistent styling)
                initials = ""
                if user[1] and user[2]:
                    initials = f"{user[1][0]}{user[2][0]}".upper()
                elif user[0]:
                    initials = user[0][0:2].upper()
                
                st.markdown(f"""
                <div style="
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: #f0f0f0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 8px auto;
                    color: {st.session_state.color_scheme['primary']};
                    font-size: 1.25rem;
                    font-weight: bold;
                ">{initials}</div>
                """, unsafe_allow_html=True)
            
            # Display name and title (perfectly centered)
            display_name = f"{user[1]} {user[2]}" if (user[1] and user[2]) else user[0]
            title = user[4] if user[4] else st.session_state.user_role
            
            st.markdown(f"""
            <div style="
                text-align: center;
                width: 100%;
                padding: 0;
                margin: 0;
            ">
                <p style="
                    margin: 0 0 2px 0;
                    padding: 0;
                    font-weight: 600;
                    color: #2c3e50;
                    font-size: 1rem;
                    line-height: 1.2;
                ">{display_name}</p>
                <p style="
                    margin: 0;
                    padding: 0;
                    font-size: 0.8rem;
                    color: #666;
                    line-height: 1.2;
                ">{title}</p>
            </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Custom divider that matches sidebar style
        st.markdown("""
        <div style="
            height: 1px;
            width: calc(100% - 1rem);
            background-color: rgba(0,0,0,0.1);
            margin: 0.75rem auto;
        "></div>
        """, unsafe_allow_html=True)

        # Rest of your sidebar content
        # App Title (adjusted spacing)
        st.markdown("""
        <div style='text-align: center;
                    margin: 0 0 1rem 0;
                    padding-top: 0;
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #2c3e50;'>
            Project App
        </div>
        """, unsafe_allow_html=True)


# 2. MENU TITLE (only appears when authenticated)
        if st.session_state.authenticated:
            st.markdown("""
            <div style='text-align: center;
                        margin: 1rem 0 0.5rem 0;
                        font-size: 1.1rem;
                        color: #4E8BF5;
                        font-weight: 600;'>
                Menu
            </div>
            """, unsafe_allow_html=True)




# Only show full navigation if authenticated
if st.session_state.authenticated:
    # Define menu items based on user role
    if st.session_state.user_role == "Admin":
        menu_items = [
            {"icon": "🏠", "label": "Dashboard", "page": "Dashboard"},
            {"icon": "📂", "label": "Projects", "page": "Projects"},
            {"icon": "✅", "label": "Tasks", "page": "Tasks"},
            {"icon": "🖥️", "label": "Workspace", "page": "Workspace"},  # Add this line
            {"icon": "🔔", "label": "Notifications", "page": "Notifications"},
            {"icon": "📅", "label": "Calendar", "page": "Calendar"},
            {"icon": "👤", "label": "Admin", "page": "Admin"},
            {"icon": "👤", "label": "Profile", "page": "Profile"}
        ]
    else:
        menu_items = [
            {"icon": "🏠", "label": "Dashboard", "page": "Dashboard"},
            {"icon": "📂", "label": "Projects", "page": "Projects"},
            {"icon": "✅", "label": "Tasks", "page": "Tasks"},
            {"icon": "🖥️", "label": "Workspace", "page": "Workspace"},  # Add this line
            {"icon": "🔔", "label": "Notifications", "page": "Notifications"},
            {"icon": "📅", "label": "Calendar", "page": "Calendar"},
            {"icon": "👤", "label": "Profile", "page": "Profile"}
        ]

    # Create navigation buttons with the new centered layout
    for idx, item in enumerate(menu_items):
        is_active = st.session_state.get('page') == item['page']
        with st.sidebar:
            cols = st.columns([1,6,1])
            with cols[1]:
                if st.button(
                    f"{item['icon']} {item['label']}",
                    key=f"nav_{item['page']}_{idx}",  # Unique key with index
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.page = item['page']
                    st.rerun()


    # Update the sidebar organization (replace the relevant section)
    st.sidebar.markdown("---")  # First separator above documentation

    # Documentation Button
    if st.sidebar.button(
        "📚 Documentation",
        key="documentation_button",
        use_container_width=False,
        type="secondary"
    ):
        st.session_state.page = "Documentation"
        st.rerun()

    
    
    # Replace the existing help section in your app.py with this code:

    # Help Button (now below documentation)
    if st.sidebar.button(
        "❓ Help", 
        key="help_button",
        use_container_width=False
    ):
        st.session_state.show_help = not st.session_state.get('show_help', False)
        st.rerun()

    # Help content expander
    if st.session_state.get('show_help', False):
        with st.sidebar.expander("📚 Help Center", expanded=True):
            # Add CSS styling using st.markdown with unsafe_allow_html
            st.markdown("""
            <style>
                .help-section {
                    margin-bottom: 1.5rem;
                }
                .help-title {
                    font-size: 1.1rem;
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 0.3rem;
                }
                .help-subtitle {
                    font-weight: 500;
                    color: #4E8BF5;
                    margin: 0.8rem 0 0.3rem 0;
                }
                .help-list {
                    margin-left: 1rem;
                    padding-left: 0.5rem;
                }
                .help-list li {
                    margin-bottom: 0.4rem;
                }
                .help-note {
                    background-color: #E1F0FF;
                    padding: 0.8rem;
                    border-radius: 6px;
                    margin: 0.8rem 0;
                    font-size: 0.9rem;
                }
                .help-tip {
                    background-color: #E8F5E9;
                    padding: 0.8rem;
                    border-radius: 6px;
                    margin: 0.8rem 0;
                    font-size: 0.9rem;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Getting Started Section
            st.markdown("### Getting Started")
            st.write("Welcome to the Project Management App! This guide will help you navigate and use all the features effectively.")
            
            st.markdown("**First Steps**")
            st.markdown("""
            - **Create your first project**: Navigate to Projects → Add New Project
            - **Add team members**: Go to Admin → User Management to add collaborators
            - **Set up tasks**: In the Tasks section, create tasks and assign them to team members
            """)
            
            st.markdown('<div class="help-note">💡 <strong>Pro Tip</strong>: Use the Dashboard for a quick overview of all your projects and tasks.</div>', unsafe_allow_html=True)
            
            # Feature Guide Section
            st.markdown("### Feature Guide")
            
            st.markdown("**Dashboard**")
            st.markdown("""
            - View project health metrics and quick statistics
            - Track progress with visual charts and timelines
            - Filter data by project, status, or time period
            """)
            
            st.markdown("**Projects**")
            st.markdown("""
            - Create and manage all your projects in one place
            - Set budgets, timelines, and assign owners
            - View detailed analytics including budget tracking
            - Use Gantt charts to visualize project timelines
            """)
            
            st.markdown("**Tasks**")
            st.markdown("""
            - Create tasks with deadlines, priorities, and assignees
            - Track time spent and completion status
            - Add dependencies between tasks
            - Attach files and add comments for collaboration
            """)

            st.markdown("**Subtasks**")
            st.markdown("""
            - Break tasks into smaller actionable items
            - Set individual deadlines and assignees for each subtask
            - Track subtask status independently from the main task
            - View subtasks nested under their parent task for clarity
            - Automatically roll up progress to the parent task           
            """)

            st.markdown("**Workspace**")
            st.markdown("""
            - One stop centre to manage your tasks
            - Create task, assign, and track progress with deadlines and priorities
            - Upload and share project documents with team members
            - Start threaded conversations with your team
            - Visualize project deadlines and task dependencies
            - Track completion rates with visual metrics and charts
            - View and manage project members            
            """)
            
            st.markdown("**Calendar**")
            st.markdown("""
            - View all tasks in a calendar layout
            - Switch between month, week, and day views
            - Color-coded by status for easy identification
            """)
            
            st.markdown("**Notifications**")
            st.markdown("""
            - Get alerts for upcoming and overdue tasks
            - Customize notification preferences
            - Filter notifications by priority or project
            """)
            
            st.markdown('<div class="help-tip">🔍 <strong>Quick Search</strong>: Most tables support filtering - look for the filter icons in column headers.</div>', unsafe_allow_html=True)
            
            # Keyboard Shortcuts Section
            st.markdown("### Keyboard Shortcuts")
            st.markdown("""
            - `Ctrl` + `F` - Search current page
            - `Esc` - Close modals and popups
            - `Enter` - Submit forms
            """)
            
            # Troubleshooting Section
            st.markdown("### Troubleshooting")
            
            st.markdown("**Common Issues**")
            st.markdown("""
            - **Can't see a project?** Check if you're the owner or have been added to the project team
            - **Task not updating?** Try refreshing the page (F5)
            - **Missing features?** Admin features are only available to users with Admin role
            """)
            
            st.markdown('<div class="help-note">❓ <strong>Need more help?</strong> Contact support at support@projectapp.com or visit our documentation.</div>', unsafe_allow_html=True)

    st.sidebar.markdown("---")  # Separator before logout

    

    # Logout Section
    if st.session_state.authenticated:
        
        # In your sidebar section where the logout button is defined, replace the CSS with this:

        st.markdown("""
        <style>
            /* Unified button styling for ALL sidebar buttons */
            div[data-testid="stSidebar"] .stButton>button {
                width: 100% !important;
                height: 42px !important;
                margin: 8px 0 !important;
                background-color: #E1F0FF !important;
                color: #2c3e50 !important;
                border: 1px solid #B8D4FF !important;
                border-radius: 8px !important;
                transition: all 0.2s ease !important;
                font-family: 'Roboto', sans-serif !important;
            }
            
            div[data-testid="stSidebar"] .stButton>button:hover {
                background-color: #D0E2FF !important;
                transform: translateY(-1px) !important;
            }
            
            div[data-testid="stSidebar"] .stButton>button[kind="primary"] {
                background-color: #4E8BF5 !important;
                color: white !important;
                border: 1px solid #4E8BF5 !important;
            }

            /* Remove extra spacing above logout section */
            div[data-testid="stSidebar"] div:has(> .stButton > button[key="logout_button"]) {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
            
            /* Logout confirmation styling */
            .logout-confirmation-container {
                background-color: #ffffff;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 8px;
            }
        </style>
        """, unsafe_allow_html=True)

        
        # Initialize session state if not already done
        if "show_logout_confirmation" not in st.session_state:
            st.session_state.show_logout_confirmation = False


        # Logout Section - placed at the bottom of your sidebar code
        if st.session_state.authenticated:
            # Remove separators and adjust spacing by placing this at the very end of sidebar content
            if not st.session_state.show_logout_confirmation:
                if st.sidebar.button(
                    "🚪 Logout",
                    key="logout_button",
                    use_container_width=True
                ):
                    st.session_state.show_logout_confirmation = True
                    st.rerun()
            else:
                st.sidebar.markdown("""
                <div class="logout-confirmation-container">
                    <p style="text-align: center; margin-bottom: 12px;">Are you sure you want to logout?</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.sidebar.button(
                    "✅ Confirm Logout", 
                    key="logout_confirm", 
                    type="primary",
                    use_container_width=True
                ):
                    # Clear session state
                    st.session_state.authenticated = False
                    st.session_state.user_id = None
                    st.session_state.user_role = None
                    st.session_state.breadcrumbs = []
                    st.session_state.page = "Dashboard"
                    st.session_state.show_help = False
                    st.session_state.show_logout_confirmation = False
                    st.rerun()
                
                if st.sidebar.button(
                    "❌ Cancel", 
                    key="logout_cancel",
                    use_container_width=True
                ):
                    st.session_state.show_logout_confirmation = False
                    st.rerun()

    st.sidebar.markdown("---")  # Separator after logout


# Define status colors for tasks
status_colors = {
    "Pending": "#FFA500",  # Orange
    "In Progress": "#00BFFF",  # DeepSkyBlue
    "Completed": "#32CD32",  # LimeGreen
    "Overdue": "#FF4500"  # OrangeRed
}



# Reusable edit task form function
# First, update the edit_task_form function with a more professional design
def edit_task_form(task_id, project_id):
    task = query_db("SELECT * FROM tasks WHERE id=?", (task_id,), one=True)
    if not task:
        st.error("Task not found")
        return False
    
    # Main task editing form - using a container with consistent styling
    with st.container():
        st.markdown("### Edit Task")
        with st.form(key=f"edit_task_form_{task_id}"):
            # Two-column layout for better organization
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Task Title*", value=task[2])
                description = st.text_area("Description", value=task[3] or "")
                
                # Status and priority in the same row
                status_col, priority_col = st.columns(2)
                with status_col:
                    status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], 
                                        index=["Pending", "In Progress", "Completed"].index(task[4]))
                with priority_col:
                    priority = st.selectbox("Priority*", ["High", "Medium", "Low"], 
                                          index=["High", "Medium", "Low"].index(task[8]))
            
            with col2:
                # Date fields in the same row
                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    try:
                        task_start_date = datetime.strptime(task[5], "%Y-%m-%d").date() if task[5] else datetime.today().date()
                    except ValueError:
                        task_start_date = datetime.strptime(task[5], "%Y-%m-%d %H:%M:%S").date() if task[5] else datetime.today().date()
                    start_date = st.date_input("Start Date*", value=task_start_date)
                with date_col2:
                    try:
                        task_deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else datetime.today().date()
                    except ValueError:
                        task_deadline = datetime.strptime(task[6], "%Y-%m-%d %H:%M:%S").date() if task[6] else datetime.today().date()
                    deadline = st.date_input("Deadline*", value=task_deadline)
                
                # Budget and assignee
                budget = st.number_input("Budget ($)", min_value=0.0, value=float(task[12] or 0), step=0.01)
                
                team_members = query_db("SELECT id, username FROM users ORDER BY username")
                assigned_to = st.selectbox("Assign To", [member[1] for member in team_members], 
                                         index=[member[1] for member in team_members].index(
                                             query_db("SELECT username FROM users WHERE id=?", (task[10],), one=True)[0]))
            
            # Form submission buttons
            submit_col1, submit_col2 = st.columns(2)
            with submit_col1:
                submitted = st.form_submit_button("Update Task")
            with submit_col2:
                cancel = st.form_submit_button("Cancel")
            
            if submitted:
                if not title.strip():
                    st.error("Task title is required")
                elif deadline < start_date:
                    st.error("Deadline must be on or after the start date")
                else:
                    assigned_to_id = query_db(
                        "SELECT id FROM users WHERE username = ?", 
                        (assigned_to,), 
                        one=True
                    )[0]
                    
                    query_db("""
                        UPDATE tasks 
                        SET title=?, description=?, status=?, start_date=?, deadline=?, 
                        priority=?, assigned_to=?, budget=?
                        WHERE id=?
                    """, (
                        title.strip(), description, status, start_date, deadline, 
                        priority, assigned_to_id, budget, task_id
                    ))
                    
                    st.success("Task updated successfully!")
                    return True
            if cancel:
                return False
    
    # Subtask section - redesigned with consistent styling
    # Subtask section - completely reworked assignment handling
    st.markdown("---")
    st.subheader("Subtasks Management")
    
    # Get all subtasks with proper assignment handling
    subtasks = query_db("""
        SELECT s.id, s.title, s.description, s.status, s.start_date, s.deadline, 
               s.priority, s.assigned_to, s.budget, s.time_spent, u.username
        FROM subtasks s
        LEFT JOIN users u ON s.assigned_to = u.id
        WHERE s.task_id=?
        ORDER BY s.id
    """, (task_id,))
    
    if subtasks:
        st.write("### Current Subtasks")
        
        # Create a DataFrame with proper assignment display
        subtasks_df = pd.DataFrame(subtasks, columns=[
            "ID", "Title", "Description", "Status", "Start Date", "Deadline",
            "Priority", "Assigned To ID", "Budget", "Time Spent", "Assigned To"
        ])
        
        # Replace None with "Unassigned" for display
        subtasks_df["Assigned To"] = subtasks_df["Assigned To"].fillna("Unassigned")
        
        # Display the subtasks table
        st.dataframe(
            subtasks_df[["ID", "Title", "Status", "Priority", "Assigned To", 
                        "Start Date", "Deadline", "Budget", "Time Spent"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Start Date": st.column_config.DateColumn("Start Date"),
                "Deadline": st.column_config.DateColumn("Deadline"),
                "Budget": st.column_config.NumberColumn("Budget", format="$%.2f"),
                "Time Spent": st.column_config.NumberColumn("Time Spent (hrs)")
            }
        )
        
        # Subtask management form with reliable assignment handling
        st.markdown("---")
        st.subheader("Manage Subtask")
        
        if subtasks:
            selected_subtask = st.selectbox(
                "Select Subtask to Manage",
                [f"{subtask[0]}: {subtask[1]}" for subtask in subtasks],
                index=0,
                key="subtask_selector"
            )
            
            if selected_subtask:
                subtask_id = int(selected_subtask.split(":")[0])
                subtask = next((s for s in subtasks if s[0] == subtask_id), None)
                
                if subtask:
                    with st.form(key=f"manage_subtask_{subtask_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            subtask_title = st.text_input("Title", value=subtask[1])
                            subtask_description = st.text_area(
                                "Description", 
                                value=subtask[2] or ""
                            )
                            
                            status_col, priority_col = st.columns(2)
                            with status_col:
                                subtask_status = st.selectbox(
                                    "Status", 
                                    ["Pending", "In Progress", "Completed"], 
                                    index=["Pending", "In Progress", "Completed"].index(subtask[3])
                                )
                            with priority_col:
                                subtask_priority = st.selectbox(
                                    "Priority", 
                                    ["High", "Medium", "Low"], 
                                    index=["High", "Medium", "Low"].index(subtask[6])
                                )
                        
                        with col2:
                            date_col1, date_col2 = st.columns(2)
                            with date_col1:
                                subtask_start_date = st.date_input(
                                    "Start Date", 
                                    value=datetime.strptime(subtask[4], "%Y-%m-%d").date() if subtask[4] else start_date
                                )
                            with date_col2:
                                subtask_deadline = st.date_input(
                                    "Deadline", 
                                    value=datetime.strptime(subtask[5], "%Y-%m-%d").date() if subtask[5] else deadline
                                )
                            
                            subtask_budget = st.number_input(
                                "Budget ($)", 
                                min_value=0.0, 
                                value=float(subtask[8] or 0), 
                                step=0.01
                            )
                            
                            # Get all available users
                            team_members = query_db("SELECT id, username FROM users ORDER BY username")
                            assignee_options = ["Unassigned"] + [member[1] for member in team_members]
                            
                            # Find current assignee
                            current_assignee = "Unassigned"
                            if subtask[7]:  # If there's an assigned_to value
                                current_assignee = subtask[10] if subtask[10] else "Unassigned"
                            
                            subtask_assigned_to = st.selectbox(
                                "Assign To", 
                                assignee_options,
                                index=assignee_options.index(current_assignee) if current_assignee in assignee_options else 0
                            )
                        
                        col1, col2, col3 = st.columns([1,1,2])
                        with col1:
                            if st.form_submit_button("Update Subtask"):
                                try:
                                    # Handle assignment
                                    assigned_to_id = None
                                    if subtask_assigned_to != "Unassigned":
                                        assigned_to_id = query_db(
                                            "SELECT id FROM users WHERE username = ?", 
                                            (subtask_assigned_to,), 
                                            one=True
                                        )[0]
                                    
                                    query_db("""
                                        UPDATE subtasks 
                                        SET title=?, description=?, status=?, start_date=?, deadline=?, 
                                        priority=?, assigned_to=?, budget=?
                                        WHERE id=?
                                    """, (
                                        subtask_title, subtask_description, subtask_status, 
                                        subtask_start_date, subtask_deadline, subtask_priority, 
                                        assigned_to_id, subtask_budget, subtask_id
                                    ))
                                    st.success("Subtask updated!")
                                    st.rerun()  # Force complete refresh
                                except Exception as e:
                                    st.error(f"Error updating subtask: {str(e)}")
                        with col2:
                            if st.form_submit_button("Delete"):
                                query_db("DELETE FROM subtasks WHERE id=?", (subtask_id,))
                                st.success("Subtask deleted!")
                                st.rerun()  # Force complete refresh
    
    # Add new subtask form with reliable assignment handling
    st.markdown("---")
    st.subheader("Create New Subtask")
    with st.form(key=f"add_subtask_form_{task_id}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_subtask_title = st.text_input("Title*", placeholder="Enter subtask name")
            new_subtask_description = st.text_area("Description", placeholder="Enter subtask description")
            
            status_col, priority_col = st.columns(2)
            with status_col:
                new_subtask_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
            with priority_col:
                new_subtask_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        
        with col2:
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                new_subtask_start_date = st.date_input("Start Date", value=start_date)
            with date_col2:
                new_subtask_deadline = st.date_input("Deadline", value=deadline)
            
            new_subtask_budget = st.number_input("Budget ($)", min_value=0.0, value=0.0, step=0.01)
            
            team_members = query_db("SELECT id, username FROM users ORDER BY username")
            new_subtask_assigned_to = st.selectbox(
                "Assign To", 
                ["Unassigned"] + [member[1] for member in team_members]
            )
        
        submit_col1, submit_col2 = st.columns(2)
        with submit_col1:
            if st.form_submit_button("Create Subtask"):
                if not new_subtask_title.strip():
                    st.error("Subtask title is required")
                elif new_subtask_deadline < new_subtask_start_date:
                    st.error("Deadline must be on or after the start date")
                else:
                    assigned_to_id = None
                    if new_subtask_assigned_to != "Unassigned":
                        assigned_to_id = query_db(
                            "SELECT id FROM users WHERE username = ?", 
                            (new_subtask_assigned_to,), 
                            one=True
                        )[0]
                    
                    query_db("""
                        INSERT INTO subtasks 
                        (task_id, title, description, status, start_date, deadline, 
                         priority, assigned_to, budget)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task_id, new_subtask_title.strip(), new_subtask_description, 
                        new_subtask_status, new_subtask_start_date, new_subtask_deadline,
                        new_subtask_priority, assigned_to_id, new_subtask_budget
                    ))
                    st.success("Subtask created successfully!")
                    st.rerun()  # Force complete refresh
        with submit_col2:
            if st.form_submit_button("Cancel"):
                st.rerun()
    
    return False

# Update the plot_subtask_analytics function with filters and budget column
def plot_subtask_analytics(tasks_df):
    if not tasks_df.empty:
        # Try to get extended subtask info first
        try:
            subtasks = query_db("""
                SELECT 
                    p.name as project_name,
                    t.id as task_id, 
                    t.title as task_title,
                    s.id as subtask_id, 
                    s.title as subtask_title, 
                    s.description,
                    s.status,
                    s.start_date,
                    s.deadline,
                    s.priority,
                    u.username as assigned_to
                FROM subtasks s
                JOIN tasks t ON s.task_id = t.id
                JOIN projects p ON t.project_id = p.id
                LEFT JOIN users u ON s.assigned_to = u.id
                ORDER BY p.name, t.id, s.id
            """)
            
            if subtasks:
                # Create DataFrame with project as first column
                subtasks_df = pd.DataFrame(subtasks, columns=[
                    "Project", "Task ID", "Task Title", "Subtask ID", 
                    "Subtask Title", "Description", "Status", "Start Date",
                    "Deadline", "Priority", "Assigned To"
                ])
                
                # Add filter controls with unique keys
                st.subheader("Filters")
                col1, col2, col3 = st.columns(3)
                with col1:
                    project_filter = st.selectbox(
                        "Filter by Project",
                        ["All Projects"] + sorted(subtasks_df['Project'].unique().tolist()),
                        key="subtask_project_filter"
                    )
                with col2:
                    status_filter = st.selectbox(
                        "Filter by Status",
                        ["All Statuses"] + sorted(subtasks_df['Status'].unique().tolist()),
                        key="subtask_status_filter"
                    )
                with col3:
                    priority_filter = st.selectbox(
                        "Filter by Priority",
                        ["All Priorities"] + sorted(subtasks_df['Priority'].unique().tolist()),
                        key="subtask_priority_filter"
                    )
                
                # Apply filters
                if project_filter != "All Projects":
                    subtasks_df = subtasks_df[subtasks_df['Project'] == project_filter]
                if status_filter != "All Statuses":
                    subtasks_df = subtasks_df[subtasks_df['Status'] == status_filter]
                if priority_filter != "All Priorities":
                    subtasks_df = subtasks_df[subtasks_df['Priority'] == priority_filter]
                
                # Display the full subtasks table with Project first
                st.subheader("Subtasks Overview")
                st.dataframe(
                    subtasks_df,
                    use_container_width=True,
                    hide_index=True,
                    column_order=["Project", "Task ID", "Task Title", "Subtask ID", 
                                 "Subtask Title", "Status", "Priority", "Assigned To",
                                 "Start Date", "Deadline", "Description"],
                    key="subtasks_dataframe"  # Unique key for the dataframe
                )
                
                # Completion analysis
                st.subheader("Completion Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    status_counts = subtasks_df['Status'].value_counts()
                    fig = px.pie(
                        status_counts, 
                        values=status_counts.values, 
                        names=status_counts.index,
                        title="Subtask Status Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="status_pie_chart")
                
                with col2:
                    completion_rate = (len(subtasks_df[subtasks_df['Status'] == 'Completed']) / len(subtasks_df)) * 100
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=completion_rate,
                        title={'text': "Overall Completion Rate"},
                        gauge={'axis': {'range': [0, 100]}}
                    ))
                    st.plotly_chart(fig, use_container_width=True, key="completion_gauge")
                
                # Timeline analysis by project
                st.subheader("Timeline Analysis by Project")
                if 'Start Date' in subtasks_df.columns and 'Deadline' in subtasks_df.columns:
                    subtasks_df['Duration'] = (pd.to_datetime(subtasks_df['Deadline']) - 
                                             pd.to_datetime(subtasks_df['Start Date'])).dt.days
                    fig = px.bar(
                        subtasks_df,
                        x='Subtask Title',
                        y='Duration',
                        color='Project',
                        title="Subtask Durations by Project",
                        hover_data=['Task Title', 'Priority', 'Assigned To']
                    )
                    st.plotly_chart(fig, use_container_width=True, key="duration_bar_chart")
            else:
                st.warning("No subtasks found in the database")
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {str(e)}")
            # Fallback to basic subtask info with project
            subtasks = query_db("""
                SELECT 
                    p.name as project_name,
                    t.id as task_id, 
                    t.title as task_title,
                    s.id as subtask_id, 
                    s.title as subtask_title, 
                    s.status
                FROM subtasks s
                JOIN tasks t ON s.task_id = t.id
                JOIN projects p ON t.project_id = p.id
                ORDER BY p.name, t.id, s.id
            """)
            
            if subtasks:
                subtasks_df = pd.DataFrame(subtasks, columns=[
                    "Project", "Task ID", "Task Title", "Subtask ID", "Subtask Title", "Status"
                ])
                
                st.subheader("Subtasks Overview")
                st.dataframe(
                    subtasks_df,
                    use_container_width=True,
                    hide_index=True,
                    column_order=["Project", "Task ID", "Task Title", "Subtask ID", "Subtask Title", "Status"],
                    key="basic_subtasks_dataframe"
                )
                
                st.subheader("Completion Analysis")
                status_counts = subtasks_df['Status'].value_counts()
                fig = px.pie(
                    status_counts, 
                    values=status_counts.values, 
                    names=status_counts.index,
                    title="Subtask Status Distribution",
                    key="basic_status_pie"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No subtasks found in the database")
    else:
        st.warning("No tasks available for subtask analysis")


# Add this helper function somewhere in your helper functions section (before the page routing)
def display_project_analytics_table(projects_data):
    """Display the project analytics table with consistent styling"""
    # Convert to DataFrame with correct column names
    project_df = pd.DataFrame(projects_data, columns=[
        "ID", "Owner ID", "Project", "Description", "Start Date", "End Date",
        "Budget", "Actual Cost", "Budget Variance", "Total Tasks",
        "Completed Tasks", "Owner", "Completion %",
        "Planned Duration (days)", "Actual Duration (days)"
    ])

    # Ensure date columns are proper datetime objects
    project_df["Start Date"] = pd.to_datetime(project_df["Start Date"])
    project_df["End Date"] = pd.to_datetime(project_df["End Date"])

    def format_date(date_val):
        if pd.isna(date_val):
            return ""
        if isinstance(date_val, (pd.Timestamp, datetime.date)):
            return date_val.strftime('%Y-%m-%d')
        try:
            return pd.to_datetime(date_val).strftime('%Y-%m-%d')
        except:
            return str(date_val)

    def style_project_table(df):
        """Style the project table with robust duration column handling"""
        styled_df = df.copy()
        
        # Safely format dates
        styled_df["Start Date"] = pd.to_datetime(styled_df["Start Date"], errors='coerce').dt.strftime('%Y-%m-%d')
        styled_df["End Date"] = pd.to_datetime(styled_df["End Date"], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Robust duration formatting with error handling
        def safe_duration_format(x):
            try:
                if pd.isna(x):
                    return "N/A"
                # Check if value is already numeric
                if isinstance(x, (int, float)):
                    return f"{float(x):.1f} days"
                # Handle string representations of numbers
                if isinstance(x, str) and x.replace('.', '', 1).isdigit():
                    return f"{float(x):.1f} days"
                return "N/A"
            except (ValueError, TypeError):
                return "N/A"
        
        # Apply safe formatting to duration columns
        styled_df["Planned Duration"] = styled_df["Planned Duration (days)"].apply(safe_duration_format)
        styled_df["Actual Duration"] = styled_df["Actual Duration (days)"].apply(safe_duration_format)
        
        # Format other columns with error handling
        def safe_currency_format(x):
            try:
                return f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() else "$0.00"
            except (ValueError, TypeError):
                return "$0.00"
        
        styled_df["Budget"] = styled_df["Budget"].apply(safe_currency_format)
        styled_df["Actual Cost"] = styled_df["Actual Cost"].apply(safe_currency_format)
        styled_df["Budget Variance"] = styled_df["Budget Variance"].apply(safe_currency_format)
        
        # Safely format progress percentage
        def safe_progress_format(x):
            try:
                return f"{float(x):.1f}%" if pd.notnull(x) and str(x).strip() else "0.0%"
            except (ValueError, TypeError):
                return "0.0%"
        
        styled_df["Progress"] = styled_df["Completion %"].apply(safe_progress_format)
        
        return styled_df[[
            "Project", "Owner", "Start Date", "End Date",
            "Planned Duration", "Actual Duration",
            "Budget", "Actual Cost", "Budget Variance",
            "Total Tasks", "Progress"
        ]]

    styled_df = style_project_table(project_df)

    # Display the styled table with container styling
    st.markdown("""
    <div style="border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="background-color: #f8f9fa; padding: 15px; border-bottom: 1px solid #e0e0e0;">
            <h3 style="margin: 0; color: #2c3e50;">Project Analytics</h3>
        </div>
    """, unsafe_allow_html=True)

    # Display the dataframe with Streamlit
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Start Date": st.column_config.DateColumn("Start Date"),
            "End Date": st.column_config.DateColumn("End Date"),
            "Budget Variance": st.column_config.TextColumn("Budget Variance"),
            "Planned Duration": st.column_config.TextColumn("Planned Duration"),
            "Actual Duration": st.column_config.TextColumn("Actual Duration")
        }
    )

    st.write("</div>", unsafe_allow_html=True)  # Close the styled container








# Helper function to get tasks
def get_tasks(project_id=None):
    """Fetch only tasks where current user is assignee"""
    if project_id:
        return query_db(
            "SELECT * FROM tasks WHERE project_id=? AND assigned_to=?",
            (project_id, st.session_state.user_id)
        )
    
    return query_db(
        "SELECT * FROM tasks WHERE assigned_to=?",
        (st.session_state.user_id,)
    )

# Helper function if task under assignee
def is_task_assignee(task):
    """Check if current user is task assignee"""
    return task[10] == st.session_state.user_id  # assigned_to is index 10


# Helper function if user can edit task
def user_can_edit_task(task):
    """Check if current user can edit this task"""
    if st.session_state.user_role == "Admin":
        return True
    
    # User is the assignee
    if task[10] == st.session_state.user_id:  # assigned_to is at index 10
        return True
    
    # User is project owner
    project_owner = query_db(
        "SELECT user_id FROM projects WHERE id=?",
        (task[1],), one=True
    )
    if project_owner and project_owner[0] == st.session_state.user_id:
        return True
    
    # User is in project team
    return query_db(
        "SELECT 1 FROM project_team WHERE project_id=? AND user_id=?",
        (task[1], st.session_state.user_id), one=True
    )



# Helper function user can modify task
def user_can_modify_task(task):
    """Check if user can edit/delete this task"""
    if st.session_state.user_role == "Admin":
        return True
    if task[10] == st.session_state.user_id:  # User is assignee
        return True
    # Check if user is project owner
    return query_db(
        "SELECT 1 FROM projects WHERE id=? AND user_id=?", 
        (task[1], st.session_state.user_id), 
        one=True
    )

# Helper function to get upcoming and overdue tasks
def get_upcoming_and_overdue_tasks():
    today = datetime.today().date()
    tasks = get_tasks()
    upcoming_tasks = []
    overdue_tasks = []

    for task in tasks:
        deadline = datetime.strptime(task[6], "%Y-%m-%d").date()
        if deadline < today and task[4] != "Completed":
            overdue_tasks.append(task)
        elif (deadline - today).days <= st.session_state.reminder_period and task[4] != "Completed":
            upcoming_tasks.append(task)

    return upcoming_tasks, overdue_tasks

# Helper function to create a new instance of a recurring task
def create_recurring_task(task):
    """Create a new instance of a recurring task."""
    recurrence = task[9]  # Recurrence pattern (e.g., daily, weekly, monthly)
    if not recurrence:
        return  # Not a recurring task
    
    # Calculate the new deadline based on the recurrence pattern
    deadline = datetime.strptime(task[6], "%Y-%m-%d").date()
    if recurrence == "daily":
        new_deadline = deadline + timedelta(days=1)
    elif recurrence == "weekly":
        new_deadline = deadline + timedelta(weeks=1)
    elif recurrence == "monthly":
        new_deadline = deadline + timedelta(days=30)  # Approximate
    else:
        return  # Invalid recurrence pattern
    
    # Create a new task with the updated deadline
    query_db("INSERT INTO tasks (project_id, title, description, status, deadline, priority, recurrence) VALUES (?, ?, ?, ?, ?, ?, ?)",
             (task[1], task[2], task[3], "Pending", new_deadline, task[8], recurrence))

# Helper function to get task dependencies
def get_task_dependencies(task_id):
    """Get the list of tasks that the given task depends on."""
    return query_db("SELECT depends_on_task_id FROM task_dependencies WHERE task_id=?", (task_id,))

# Helper function to check if a task can be completed
def can_complete_task(task_id):
    """Check if a task can be completed (all dependencies are met)."""
    dependencies = get_task_dependencies(task_id)
    for dep_task_id in dependencies:
        dep_task = query_db("SELECT status FROM tasks WHERE id=?", (dep_task_id[0],), one=True)
        if not dep_task or dep_task[0] != "Completed":
            return False
    return True


def fetch_calendar_events():
    """
    Fetch tasks and prepare them for the calendar visualization.
    Now includes tasks where current user is either project owner OR assignee.
    """
    # Fetch tasks from the database based on user role
    if st.session_state.user_role == "Admin":
        # Admin can see all tasks
        query = """
            SELECT t.id, t.title AS Task, t.deadline AS Date, t.status, p.name AS Project
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
        """
        tasks = query_db(query)
    else:
        # Regular users can see tasks where they're either:
        # 1. Project owner, 2. Task assignee, or 3. Project team member
        query = """
            SELECT t.id, t.title AS Task, t.deadline AS Date, t.status, p.name AS Project
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.assigned_to = ?  -- User is task assignee
               OR p.user_id = ?      -- User is project owner
               OR p.id IN (          -- User is in project team
                   SELECT project_id FROM project_team WHERE user_id = ?
               )
        """
        tasks = query_db(query, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id))
    
    # Prepare events for the calendar
    events = []
    for task in tasks:
        event = {
            "title": f"{task[1]} ({task[4]})",  # Task title (Project name)
            "start": task[2],                   # Task deadline
            "color": status_colors.get(task[3], "#f0f0f0"),  # Color based on status
            "extendedProps": {
                "status": task[3],
                "project": task[4],
                "task_id": task[0]
            }
        }
        events.append(event)
    
    return events



def update_user_profile(user_id):
    """
    Allow users to update their profile information, including profile picture.
    """
    st.subheader("Update Your Profile")
    
    # Fetch current user data
    user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    if not user:
        st.error("User not found.")
        return
    
    # Debugging: Print the user tuple to verify its structure
    print("User Data:", user)
    print("Number of Columns in User Tuple:", len(user))
    
    with st.form(key="update_profile_form"):
        # Display current profile picture (if available)
        if len(user) > 11 and user[11]:  # Check if profile_picture exists
            st.image(user[11], width=100, caption="Current Profile Picture")
        else:
            st.write("No profile picture uploaded.")
        
        # Upload new profile picture
        uploaded_file = st.file_uploader("Upload a new profile picture", type=["jpg", "jpeg", "png"])
        
        # Input fields for profile details
        first_name = st.text_input("First Name", value=user[4] if len(user) > 4 else "")
        last_name = st.text_input("Last Name", value=user[5] if len(user) > 5 else "")
        company = st.text_input("Company", value=user[6] if len(user) > 6 else "")
        job_title = st.text_input("Job Title", value=user[7] if len(user) > 7 else "")
        department = st.text_input("Department", value=user[8] if len(user) > 8 else "")
        email = st.text_input("Email", value=user[9] if len(user) > 9 else "")
        phone = st.text_input("Phone", value=user[10] if len(user) > 10 else "")
        
        if st.form_submit_button("Update Profile"):
            # Update profile picture if a new file is uploaded
            profile_picture = user[11] if len(user) > 11 else None  # Keep the existing picture by default
            if uploaded_file is not None:
                profile_picture = uploaded_file.read()  # Read the file as binary data
            
            # Debugging: Print the values being passed to the UPDATE query
            print("Updating Profile with the following values:")
            print("First Name:", first_name)
            print("Last Name:", last_name)
            print("Company:", company)
            print("Job Title:", job_title)
            print("Department:", department)
            print("Email:", email)
            print("Phone:", phone)
            print("Profile Picture:", profile_picture)
            
            # Update the user's profile in the database
            query_db('''
                UPDATE users
                SET first_name=?, last_name=?, company=?, job_title=?, department=?, email=?, phone=?, profile_picture=?
                WHERE id=?
            ''', (
                first_name if first_name else user[4],  # Use existing value if new value is None
                last_name if last_name else user[5],
                company if company else user[6],
                job_title if job_title else user[7],
                department if department else user[8],
                email if email else user[9],
                phone if phone else user[10],
                profile_picture if profile_picture else user[11],  # Use existing picture if new picture is None
                user_id
            ))
            
            st.success("Profile updated successfully!")
            st.rerun()  # Rerun the app to reflect changes


def display_user_profile(user_id):
    """
    Display the user's profile information.
    """
    st.subheader("Your Profile")
    
    # Fetch user data
    user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    if not user:
        st.error("User not found.")
        return
    
    # Debugging: Print the user tuple to verify its structure
    print("User Data:", user)
    
    # Display profile picture
    if len(user) > 11 and user[11]:  # Check if profile_picture exists
        st.image(user[11], width=100, caption="Profile Picture")
    else:
        st.write("No profile picture uploaded.")
    
    # Display profile details
    st.write(f"**Username:** {user[1]}")
    st.write(f"**First Name:** {user[4]}")
    st.write(f"**Last Name:** {user[5]}")
    st.write(f"**Company:** {user[6]}")
    st.write(f"**Job Title:** {user[7]}")
    st.write(f"**Department:** {user[8]}")
    st.write(f"**Email:** {user[9]}")
    st.write(f"**Phone:** {user[10]}")




# Breadcrumbs Functionality
def update_breadcrumbs(page):
    """Update the breadcrumbs in session state."""
    if page not in st.session_state.breadcrumbs:
        st.session_state.breadcrumbs.append(page)

def display_breadcrumbs():
    """Display breadcrumbs as clickable links."""
    if st.session_state.breadcrumbs:
        breadcrumb_links = " > ".join([
            f'<a href="#{crumb}" style="text-decoration: none; color: inherit;">{crumb}</a>'
            for crumb in st.session_state.breadcrumbs
        ])
        st.markdown(f"**Navigation:** {breadcrumb_links}", unsafe_allow_html=True)


def save_logo_to_db(logo_bytes):
    """Save logo to database"""
    query_db(
        "INSERT OR REPLACE INTO app_settings (setting_name, setting_value) VALUES (?, ?)",
        ("login_logo", logo_bytes)
    )

def get_logo_from_db():
    """Retrieve logo from database"""
    result = query_db(
        "SELECT setting_value FROM app_settings WHERE setting_name=?",
        ("login_logo",),
        one=True
    )
    return result[0] if result else None




# User Authentication
if not st.session_state.authenticated:
    # ===== NEW CODE START =====
    # Initialize logo in session state if not exists
    if 'login_logo' not in st.session_state:
        # Try to load logo from database
        logo_data = query_db("SELECT setting_value FROM app_settings WHERE setting_name='login_logo'", one=True)
        st.session_state.login_logo = logo_data[0] if logo_data else None
    
    # Create columns for logo + title
    logo_col, title_col = st.columns([1, 4])
    
    with logo_col:
        # Show logo uploader if no logo exists
        if st.session_state.login_logo is None:
            uploaded_logo = st.file_uploader("Upload Company Logo", 
                                           type=["png", "jpg", "jpeg"],
                                           key="logo_uploader")
            if uploaded_logo is not None:
                # Save to session state and database
                st.session_state.login_logo = uploaded_logo.read()
                query_db("""
                    INSERT OR REPLACE INTO app_settings (setting_name, setting_value) 
                    VALUES ('login_logo', ?)
                """, (st.session_state.login_logo,))
                st.rerun()
        else:
            # Display the logo
            st.image(st.session_state.login_logo, width=100)
    
    with title_col:
        st.title("Project Management App")
    # ===== NEW CODE END =====
    
    # Center the login form (existing code)
    col1, col2, col3 = st.columns([1,3,1])
    
    with col2:
        # Rest of your existing login/register code remains exactly the same
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form(key="login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    user = query_db("SELECT * FROM users WHERE username=?", (username,), one=True)
                    if user and verify_password(user[2], password):
                        st.session_state.authenticated = True
                        st.session_state.user_id = user[0]
                        st.session_state.user_role = user[3]

                        # ADD THIS CODE BLOCK - Records login time and increments count
                        query_db("""
                            UPDATE users 
                            SET last_login = datetime('now'), 
                                login_count = COALESCE(login_count, 0) + 1,
                                is_active = 1
                            WHERE id=?
                        """, (user[0],))

                        st.success("Login successful!")
                        st.session_state.show_welcome = True  # Set flag to show welcome message
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Register"):
                    if new_password != confirm_password:
                        st.error("Passwords don't match!")
                    elif query_db("SELECT * FROM users WHERE username=?", (new_username,), one=True):
                        st.error("Username already exists.")
                    else:
                        role = "Admin" if len(query_db("SELECT * FROM users")) == 0 else "User"
                        query_db("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                (new_username, hash_password(new_password), role))
                        st.success("Registration successful! Please login.")
                        st.rerun()


else:
    
    # Main App
    # Main App
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"

    # Display welcome message if flag is set
    if st.session_state.get('show_welcome', False):
        user = query_db("SELECT username, first_name, last_name FROM users WHERE id=?", (st.session_state.user_id,), one=True)
        if user:
            # Use first name if available, otherwise username
            welcome_name = user[1] if user[1] else user[0]
            # Add last name if available
            if user[1] and user[2]:  # If both first and last name exist
                welcome_name = f"{user[1]} {user[2]}"
        else:
            welcome_name = "there"
        
        # Create columns for centering
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            # Create container with button inside
            container = st.container(border=True)
            with container:
                # Welcome message content
                st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    margin-bottom: 0.5rem;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    ">
                        <h3 style="
                            color: #2c3e50; 
                            margin: 0;
                            font-size: 1rem;
                            font-weight: 600;
                            white-space: nowrap;
                        ">
                            👋 Welcome, {welcome_name}
                        </h3>
                    </div>
                    <div>
                        <span style="
                            background: #f0f4f8;
                            color: #4E8BF5;
                            padding: 0.15rem 0.5rem;
                            border-radius: 10px;
                            font-size: 0.7rem;
                            font-weight: 500;
                        ">
                            {st.session_state.user_role}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button placed inside the container
                if st.button("Got it", key="dismiss_welcome"):
                    st.session_state.show_welcome = False
                    st.rerun()

            # Custom styling for the container
            st.markdown("""
            <style>
                div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
                    padding: 1rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                    border: 1px solid #e1e4e8 !important;
                    background: white;
                    width: 100%;
                }
            </style>
            """, unsafe_allow_html=True)

    page = st.session_state.page
    

    # Update breadcrumbs
    update_breadcrumbs(page)
    display_breadcrumbs()
    

    # Helper Functions
    def get_projects():
        if st.session_state.user_role == "Admin":
            return query_db("SELECT * FROM projects")
        else:
            return query_db("""
                SELECT DISTINCT p.* FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
                WHERE p.user_id = ?  -- User owns project
                OR t.assigned_to = ? -- User has tasks in project
                OR p.id IN (        -- User is in project team
                    SELECT project_id FROM project_team WHERE user_id = ?
                )
            """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id))
    

    
    def get_username(user_id):
        result = query_db("SELECT username FROM users WHERE id=?", (user_id,), one=True)
        return result[0] if result else "Unknown"


    def delete_task(task_id):
        query_db("DELETE FROM tasks WHERE id=?", (task_id,))

    def delete_project(project_id):
        """
        Delete a project and all its associated tasks, subtasks, comments, attachments, and task dependencies.
        """
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        
        try:
            # Delete all task dependencies for tasks in this project
            cursor.execute("DELETE FROM task_dependencies WHERE task_id IN (SELECT id FROM tasks WHERE project_id=?)", (project_id,))
            
            # Delete all comments for tasks in this project
            cursor.execute("DELETE FROM comments WHERE task_id IN (SELECT id FROM tasks WHERE project_id=?)", (project_id,))
            
            # Delete all subtasks for tasks in this project
            cursor.execute("DELETE FROM subtasks WHERE task_id IN (SELECT id FROM tasks WHERE project_id=?)", (project_id,))
            
            # Delete all attachments for tasks in this project
            cursor.execute("DELETE FROM attachments WHERE task_id IN (SELECT id FROM tasks WHERE project_id=?)", (project_id,))
            
            # Delete all tasks for this project
            cursor.execute("DELETE FROM tasks WHERE project_id=?", (project_id,))
            
            # Finally, delete the project itself
            cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
            
            # Commit the transaction
            conn.commit()
            print(f"Project {project_id} and all associated tasks deleted successfully.")
        
        except sqlite3.Error as e:
            # Handle any errors
            print(f"An error occurred: {e}")
        
        finally:
            # Close the database connection
            conn.close()

    # Helper function to check if a task is upcoming or overdue
    def get_task_status(task_deadline):
        today = datetime.today().date()
        deadline = datetime.strptime(task_deadline, "%Y-%m-%d").date()
        if deadline < today:
            return "Overdue"
        elif (deadline - today).days <= st.session_state.reminder_period:  # Upcoming if within reminder period
            return "Upcoming"
        else:
            return "On Track"
        


   
    
    # Helper function for task status distribution (Pie Chart)
    def plot_task_status_distribution(tasks_df):
        """
        Create a pie chart showing the distribution of tasks by status.
        """
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Count tasks by status
        status_counts = tasks_df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        # Create pie chart
        fig = px.pie(
            status_counts,
            names="Status",
            values="Count",
            title="Task Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig)
        

    # Helper function for task priority distribution (Bar Chart)
    def plot_task_priority_distribution(tasks_df):
        """Professional priority distribution visualization with enhanced insights"""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Define professional color scheme
        priority_colors = {
            "High": "#E74C3C",  # Vibrant red
            "Medium": "#F39C12",  # Orange
            "Low": "#2ECC71"  # Green
        }
        
        # Count tasks by priority
        priority_counts = tasks_df["Priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]
        
        # Calculate percentages
        total_tasks = priority_counts["Count"].sum()
        priority_counts["Percentage"] = (priority_counts["Count"] / total_tasks * 100).round(1)
        
        # Create a 2-column layout for metrics and chart
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display key metrics in cards
            st.markdown("### Priority Metrics")
            
            # Calculate average completion by priority (if status data exists)
            if "Status" in tasks_df.columns:
                completion_rates = tasks_df.groupby("Priority")["Status"].apply(
                    lambda x: (x == "Completed").mean() * 100
                ).round(1).reset_index()
                completion_rates.columns = ["Priority", "Completion Rate"]
                
                # Merge with counts
                priority_stats = priority_counts.merge(completion_rates, on="Priority", how="left")
            else:
                priority_stats = priority_counts.copy()
                priority_stats["Completion Rate"] = "N/A"
            
            # Display metrics cards
            for _, row in priority_stats.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid {priority_colors[row['Priority']]};
                        padding: 12px;
                        margin-bottom: 12px;
                        background: #FFFFFF;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <h4 style="margin:0;color:#2C3E50;">{row['Priority']}</h4>
                        <p style="margin:4px 0;font-size:0.9rem;">
                            <strong>Count:</strong> {row['Count']} ({row['Percentage']}%)<br>
                            <strong>Completion:</strong> {row['Completion Rate'] if row['Completion Rate'] != 'N/A' else 'N/A'}{'%' if row['Completion Rate'] != 'N/A' else ''}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            # Create donut chart with Plotly
            fig = go.Figure()
            
            fig.add_trace(go.Pie(
                labels=priority_counts["Priority"],
                values=priority_counts["Count"],
                hole=0.5,
                marker_colors=[priority_colors[p] for p in priority_counts["Priority"]],
                textinfo='label+percent',
                textposition='inside',
                insidetextorientation='radial',
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
                sort=False
            ))
            
            # Update layout for professional appearance
            fig.update_layout(
                title='<b>Task Priority Distribution</b>',
                title_font_size=18,
                title_x=0.5,
                showlegend=False,
                margin=dict(t=50, b=20, l=20, r=20),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                ),
                annotations=[dict(
                    text=f"Total<br>{total_tasks}",
                    x=0.5, y=0.5,
                    font_size=16,
                    showarrow=False
                )]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Add trend analysis section
        st.markdown("---")
        st.markdown("### Priority Trends Over Time")
        
        # If date information is available, show trends
        if 'Planned Start Date' in tasks_df.columns:
            try:
                # Convert to datetime and extract month/year
                tasks_df['Month'] = pd.to_datetime(tasks_df['Planned Start Date']).dt.to_period('M')
                
                # Group by month and priority
                trend_data = tasks_df.groupby(['Month', 'Priority']).size().unstack().fillna(0)
                
                # Convert Period index to string for plotting
                trend_data.index = trend_data.index.astype(str)
                
                # Create area chart
                fig_trend = go.Figure()
                
                for priority in ["High", "Medium", "Low"]:
                    if priority in trend_data.columns:
                        fig_trend.add_trace(go.Scatter(
                            x=trend_data.index,
                            y=trend_data[priority],
                            name=priority,
                            stackgroup='one',
                            mode='lines',
                            line=dict(width=0.5, color=priority_colors[priority]),
                            fillcolor=priority_colors[priority],
                            hovertemplate=f"<b>{priority}</b><br>Month: %{{x}}<br>Tasks: %{{y}}<extra></extra>",
                            opacity=0.8
                        ))
                
                fig_trend.update_layout(
                    title='<b>Monthly Priority Distribution</b>',
                    xaxis_title='Month',
                    yaxis_title='Number of Tasks',
                    hovermode="x unified",
                    plot_bgcolor='rgba(245,245,245,1)',
                    paper_bgcolor='rgba(255,255,255,1)',
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
            except Exception as e:
                st.warning(f"Could not generate trends: {str(e)}")
        else:
            st.info("Add date information to tasks to enable priority trend analysis")
        
        # Add export options
        with st.expander("📤 Export Data", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Download Priority Data (CSV)",
                    data=priority_counts.to_csv(index=False),
                    file_name="task_priority_distribution.csv",
                    mime="text/csv"
                )
            
            with col2:
                buf = io.BytesIO()
                fig.write_image(buf, format="png", width=800)
                st.download_button(
                    label="Download Chart (PNG)",
                    data=buf.getvalue(),
                    file_name="priority_distribution.png",
                    mime="image/png"
                )


    # Helper function for task progress over time (Line Chart)
    # Replace the existing plot_task_progress_over_time function with this new version
    def plot_task_progress_over_time(tasks_df):
        """Enhanced professional visualization of task completion trends over time"""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Convert date columns to datetime with error handling
        tasks_df['Planned Start Date'] = pd.to_datetime(tasks_df['Planned Start Date'], errors='coerce')
        
        # Filter out invalid dates and only completed tasks
        completed_tasks = tasks_df[
            (tasks_df['Status'] == 'Completed') & 
            (tasks_df['Planned Start Date'].notna())
        ].copy()
        
        if completed_tasks.empty:
            st.warning("No completed tasks with valid dates found.")
            return
        
        # Group by date and count completed tasks
        progress_data = completed_tasks.groupby(
            pd.Grouper(key='Planned Start Date', freq='W-MON')  # Weekly grouping starting Monday
        ).size().reset_index(name='Completed Tasks')
        
        # Calculate 4-week moving average
        progress_data['4-Week Avg'] = progress_data['Completed Tasks'].rolling(4).mean()
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add bar chart for weekly completions
        fig.add_trace(go.Bar(
            x=progress_data['Planned Start Date'],
            y=progress_data['Completed Tasks'],
            name='Weekly Completed',
            marker_color='#4E8BF5',  # Primary blue
            opacity=0.7,
            hovertemplate='<b>Week of %{x|%b %d}</b><br>Tasks: %{y}<extra></extra>'
        ))
        
        # Add line chart for moving average
        fig.add_trace(go.Scatter(
            x=progress_data['Planned Start Date'],
            y=progress_data['4-Week Avg'],
            name='4-Week Average',
            line=dict(color='#FFA500', width=3),
            mode='lines',
            hovertemplate='<b>4-Week Avg</b>: %{y:.1f} tasks<extra></extra>'
        ))
        
        # Add target line (average completion rate)
        avg_completion = progress_data['Completed Tasks'].mean()
        fig.add_hline(
            y=avg_completion,
            line_dash="dot",
            line_color="#32CD32",
            annotation_text=f"Average: {avg_completion:.1f} tasks/week",
            annotation_position="top right"
        )
        
        # Calculate and display key metrics
        total_completed = completed_tasks.shape[0]
        completion_rate = (total_completed / tasks_df.shape[0]) * 100 if tasks_df.shape[0] > 0 else 0
        current_week = datetime.now().isocalendar()[1]
        current_week_completed = progress_data[progress_data['Planned Start Date'].dt.isocalendar().week == current_week]['Completed Tasks'].sum()
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Completed Tasks", total_completed)
        with col2:
            st.metric("Overall Completion Rate", f"{completion_rate:.1f}%")
        with col3:
            st.metric("This Week's Completions", current_week_completed if not pd.isna(current_week_completed) else 0)
        
        # Update layout for professional appearance
        fig.update_layout(
            title='<b>Task Completion Trends</b>',
            title_font_size=20,
            xaxis_title='Week Starting',
            yaxis_title='Tasks Completed',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='rgba(245,245,245,1)',
            paper_bgcolor='rgba(255,255,255,1)',
            margin=dict(l=50, r=50, b=100, t=100, pad=10),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(200,200,200,0.2)',
                tickformat='%b %d<br>%Y'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(200,200,200,0.2)',
                rangemode='tozero'
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Add detailed data table
        with st.expander("📊 View Detailed Data", expanded=False):
            # Format dates for display
            display_df = progress_data.copy()
            display_df['Week Starting'] = display_df['Planned Start Date'].dt.strftime('%b %d, %Y')
            display_df = display_df[['Week Starting', 'Completed Tasks', '4-Week Avg']]
            display_df['4-Week Avg'] = display_df['4-Week Avg'].round(1)
            
            st.dataframe(
                display_df,
                column_config={
                    "Week Starting": "Week Starting",
                    "Completed Tasks": st.column_config.NumberColumn("Tasks Completed", format="%d"),
                    "4-Week Avg": st.column_config.NumberColumn("4-Week Average", format="%.1f")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Export options
            st.download_button(
                label="📥 Download Data as CSV",
                data=display_df.to_csv(index=False),
                file_name="task_completion_trends.csv",
                mime="text/csv"
            )


    # Helper function for upcoming vs overdue tasks (Bar Chart)
    def plot_upcoming_vs_overdue_tasks(tasks_df):
        """
        Create a bar chart comparing the number of upcoming and overdue tasks.
        """
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Get today's date
        today = datetime.today().date()
        
        # Convert "Deadline" to datetime and extract the date part
        tasks_df["Deadline"] = pd.to_datetime(tasks_df["Deadline"]).dt.date
        
        # Categorize tasks as upcoming or overdue
        tasks_df["Status Category"] = tasks_df.apply(
            lambda row: "Overdue" if row["Deadline"] < today else "Upcoming",
            axis=1
        )
        
        # Count tasks by status category
        status_counts = tasks_df["Status Category"].value_counts().reset_index()
        status_counts.columns = ["Status Category", "Count"]
        
        # Create bar chart
        fig = px.bar(
            status_counts,
            x="Status Category",
            y="Count",
            title="Upcoming vs Overdue Tasks",
            labels={"Status Category": "Task Status", "Count": "Number of Tasks"},
            color="Status Category",
            color_discrete_map={
                "Upcoming": "#00BFFF",  # Blue
                "Overdue": "#FF4500",   # Red
            },
        )
        st.plotly_chart(fig)



    # Helper function to track budget tracking visualization
    def plot_budget_tracking(tasks_df):
        """Professional budget tracking dashboard with variance analysis"""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Check for required columns
        required_cols = ['Budget', 'Actual Cost', 'Budget Variance', 'Project']
        if not all(col in tasks_df.columns for col in required_cols):
            st.error("Missing required budget data columns")
            return
        
        # Convert currency columns to numeric
        tasks_df['Budget'] = pd.to_numeric(tasks_df['Budget'], errors='coerce')
        tasks_df['Actual Cost'] = pd.to_numeric(tasks_df['Actual Cost'], errors='coerce')
        tasks_df['Budget Variance'] = pd.to_numeric(tasks_df['Budget Variance'], errors='coerce')
        
        # Filter out rows with missing budget data
        budget_data = tasks_df.dropna(subset=['Budget', 'Actual Cost'])
        
        if budget_data.empty:
            st.warning("No valid budget data available")
            return
        
        # Professional color scheme
        color_under = "#2ECC71"  # Green for under budget
        color_over = "#E74C3C"   # Red for over budget
        color_planned = "#3498DB" # Blue for planned
        
        # Calculate aggregate metrics
        total_budget = budget_data['Budget'].sum()
        total_actual = budget_data['Actual Cost'].sum()
        total_variance =total_budget - total_actual
        variance_pct = (total_variance / total_budget * 100) if total_budget > 0 else 0
        
        # Create dashboard layout
        st.markdown("## Budget Performance Dashboard")
        
        # Top KPI metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"${total_budget:,.2f}")
        with col2:
            st.metric("Actual Spend", 
                    f"${total_actual:,.2f}",
                    delta=f"{variance_pct:.1f}% {'under' if total_variance >=0 else 'over'} budget",
                    delta_color="inverse")
        with col3:
            st.metric("Variance", 
                    f"${abs(total_variance):,.2f}",
                    help="Positive = under budget, Negative = over budget")
        
        st.markdown("---")
        
        # Main visualization section
        tab1, tab2, tab3 = st.tabs(["Project Breakdown", "Variance Analysis", "Trend Analysis"])
        
        with tab1:
            # Project-level budget comparison
            st.markdown("### Budget vs Actual by Project")
            
            # Aggregate by project
            project_data = budget_data.groupby('Project').agg({
                'Budget': 'sum',
                'Actual Cost': 'sum'
            }).reset_index()
            
            # Calculate variance and sort
            project_data['Variance'] = (project_data['Budget'] - project_data['Actual Cost']).round(2)
            project_data['Variance Pct'] = (project_data['Variance'] / project_data['Budget'] * 100)
            project_data = project_data.sort_values('Budget', ascending=False)
            
            # Create waterfall chart
            fig = go.Figure()
            
            # Add budget bars
            fig.add_trace(go.Bar(
                x=project_data['Project'],
                y=project_data['Budget'],
                name='Planned Budget',
                marker_color=color_planned,
                opacity=0.7,
                hovertemplate="<b>%{x}</b><br>Budget: $%{y:,.2f}<extra></extra>"
            ))
            
            # Add actual cost bars
            fig.add_trace(go.Bar(
                x=project_data['Project'],
                y=project_data['Actual Cost'],
                name='Actual Cost',
                marker_color=np.where(project_data['Variance'] >= 0, color_under, color_over),
                hovertemplate="<b>%{x}</b><br>Actual: $%{y:,.2f}<br>Variance: $%{text:,.2f}<extra></extra>",
                text=project_data['Variance']
            ))
            
            # Add variance indicators
            for i, row in project_data.iterrows():
                fig.add_shape(
                    type="line",
                    x0=i-0.4, x1=i+0.4,
                    y0=row['Budget'], y1=row['Budget'],
                    line=dict(color="#7F8C8D", width=2, dash="dot"),
                    opacity=0.5
                )
            
            # Update layout
            fig.update_layout(
                barmode='group',
                plot_bgcolor='rgba(245,245,245,1)',
                paper_bgcolor='rgba(255,255,255,1)',
                hovermode="x unified",
                xaxis_title="Project",
                yaxis_title="Amount ($)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(t=50, b=100, l=50, r=50),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Project variance table
            with st.expander("View Detailed Project Data", expanded=False):
                display_df = project_data.copy()
                display_df['Budget'] = display_df['Budget'].apply(lambda x: f"${x:,.2f}")
                display_df['Actual Cost'] = display_df['Actual Cost'].apply(lambda x: f"${x:,.2f}")
                display_df['Variance'] = display_df['Variance'].apply(lambda x: f"${x:,.2f}")
                display_df['Variance Pct'] = display_df['Variance Pct'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    display_df,
                    column_config={
                        "Project": "Project",
                        "Budget": st.column_config.NumberColumn("Budget", format="$%.2f"),
                        "Actual Cost": st.column_config.NumberColumn("Actual Cost", format="$%.2f"),
                        "Variance": st.column_config.NumberColumn("Variance", format="$%.2f"),
                        "Variance Pct": "Variance %"
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        with tab2:
            # Variance analysis
            st.markdown("### Budget Variance Analysis")
            
            # Create scatter plot of variance vs budget
            fig = px.scatter(
                project_data,
                x='Budget',
                y='Variance Pct',
                color='Variance',
                color_continuous_scale=[color_over, color_under],
                size='Budget',
                hover_name='Project',
                labels={
                    'Budget': 'Project Budget ($)',
                    'Variance Pct': 'Variance Percentage',
                    'Variance': 'Variance ($)'
                },
                trendline="lowess",
                trendline_color_override="#7F8C8D"
            )
            
            # Add reference lines
            fig.update_layout(
                shapes=[
                    # Zero variance line
                    dict(
                        type="line",
                        x0=0, x1=project_data['Budget'].max()*1.1,
                        y0=0, y1=0,
                        line=dict(color="#7F8C8D", width=2)
                    ),
                    # 10% variance threshold
                    dict(
                        type="line",
                        x0=0, x1=project_data['Budget'].max()*1.1,
                        y0=10, y1=10,
                        line=dict(color="#E74C3C", width=1, dash="dot")
                    ),
                    dict(
                        type="line",
                        x0=0, x1=project_data['Budget'].max()*1.1,
                        y0=-10, y1=-10,
                        line=dict(color="#E74C3C", width=1, dash="dot")
                    )
                ],
                annotations=[
                    dict(
                        x=project_data['Budget'].max()*0.8,
                        y=11,
                        text="10% Variance Threshold",
                        showarrow=False,
                        font=dict(color="#E74C3C")
                    )
                ],
                plot_bgcolor='rgba(245,245,245,1)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Variance insights
            over_budget = project_data[project_data['Variance'] < 0]
            under_budget = project_data[project_data['Variance'] > 0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Over Budget Projects")
                if not over_budget.empty:
                    over_budget = over_budget.sort_values('Variance Pct')
                    for _, row in over_budget.iterrows():
                        st.metric(
                            row['Project'],
                            f"${abs(row['Variance']):,.2f}",
                            delta=f"{row['Variance Pct']:.1f}% over",
                            delta_color="inverse"
                        )
                else:
                    st.success("No projects over budget")
            
            with col2:
                st.markdown("#### Under Budget Projects")
                if not under_budget.empty:
                    under_budget = under_budget.sort_values('Variance Pct', ascending=False)
                    for _, row in under_budget.iterrows():
                        st.metric(
                            row['Project'],
                            f"${row['Variance']:,.2f}",
                            delta=f"{row['Variance Pct']:.1f}% under"
                        )
                else:
                    st.info("No projects under budget")
        
        with tab3:
            # Time-based trend analysis (if date available)
            if 'Planned Start Date' in budget_data.columns:
                try:
                    st.markdown("### Budget Performance Over Time")
                    
                    # Extract month/year from dates
                    budget_data['Month'] = pd.to_datetime(budget_data['Planned Start Date']).dt.to_period('M')
                    
                    # Group by month
                    trend_data = budget_data.groupby('Month').agg({
                        'Budget': 'sum',
                        'Actual Cost': 'sum'
                    }).reset_index()
                    trend_data['Month'] = trend_data['Month'].astype(str)
                    trend_data['Variance'] = trend_data['Budget'] - trend_data['Actual Cost']
                    
                    # Create time series chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=trend_data['Month'],
                        y=trend_data['Budget'],
                        name='Planned Budget',
                        line=dict(color=color_planned, width=3),
                        mode='lines+markers',
                        hovertemplate="<b>%{x}</b><br>Budget: $%{y:,.2f}<extra></extra>"
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=trend_data['Month'],
                        y=trend_data['Actual Cost'],
                        name='Actual Cost',
                        line=dict(color=color_over, width=3),
                        mode='lines+markers',
                        hovertemplate="<b>%{x}</b><br>Actual: $%{y:,.2f}<br>Variance: $%{text:,.2f}<extra></extra>",
                        text=trend_data['Variance']
                    ))
                    
                    # Add variance area
                    fig.add_trace(go.Scatter(
                        x=trend_data['Month'],
                        y=trend_data['Budget'],
                        fill='tonexty',
                        fillcolor='rgba(46, 204, 113, 0.2)',
                        line=dict(width=0),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    fig.update_layout(
                        plot_bgcolor='rgba(245,245,245,1)',
                        xaxis_title="Month",
                        yaxis_title="Amount ($)",
                        hovermode="x unified",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Monthly variance table
                    with st.expander("View Monthly Variance Data", expanded=False):
                        display_df = trend_data.copy()
                        display_df['Budget'] = display_df['Budget'].apply(lambda x: f"${x:,.2f}")
                        display_df['Actual Cost'] = display_df['Actual Cost'].apply(lambda x: f"${x:,.2f}")
                        display_df['Variance'] = display_df['Variance'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(
                            display_df,
                            column_config={
                                "Month": "Month",
                                "Budget": st.column_config.NumberColumn("Budget", format="$%.2f"),
                                "Actual Cost": st.column_config.NumberColumn("Actual Cost", format="$%.2f"),
                                "Variance": st.column_config.NumberColumn("Variance", format="$%.2f")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                
                except Exception as e:
                    st.warning(f"Could not generate trend analysis: {str(e)}")
            else:
                st.info("Date information not available for trend analysis")
        
        # Export options
        st.markdown("---")
        with st.expander("📤 Export Budget Data", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Download Project Budget Data (CSV)",
                    data=project_data.to_csv(index=False),
                    file_name="project_budget_data.csv",
                    mime="text/csv"
                )
            
            with col2:
                if 'fig' in locals():
                    buf = io.BytesIO()
                    fig.write_image(buf, format="png", width=1000)
                    st.download_button(
                        label="Download Budget Chart (PNG)",
                        data=buf.getvalue(),
                        file_name="budget_analysis.png",
                        mime="image/png"
                    )


    # Helper function to visualize task timeline (Gantt chart)
    def plot_task_timeline(tasks_df):
        """Enhanced professional timeline visualization for tasks"""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Prepare data
        timeline_df = tasks_df.copy()
        
        # Convert date columns to datetime, coercing errors to NaT
        timeline_df['Planned Start Date'] = pd.to_datetime(timeline_df['Planned Start Date'], errors='coerce')
        timeline_df['Planned Deadline'] = pd.to_datetime(timeline_df['Planned Deadline'], errors='coerce')
        
        # Filter out tasks with invalid/missing planned dates
        timeline_df = timeline_df.dropna(subset=['Planned Start Date', 'Planned Deadline'])
        
        if timeline_df.empty:
            st.warning("No valid tasks with complete date information found.")
            return
        
        # Calculate duration in milliseconds for Plotly
        timeline_df['Planned Duration'] = (
            timeline_df['Planned Deadline'] - timeline_df['Planned Start Date']
        ).dt.total_seconds() * 1000  # Convert to milliseconds
        
        # Handle actual dates if available
        has_actual_dates = False
        if 'Actual Start Date' in timeline_df.columns and 'Actual Deadline' in timeline_df.columns:
            timeline_df['Actual Start Date'] = pd.to_datetime(timeline_df['Actual Start Date'], errors='coerce')
            timeline_df['Actual Deadline'] = pd.to_datetime(timeline_df['Actual Deadline'], errors='coerce')
            
            # Only consider actual dates if both are present
            actual_dates_mask = timeline_df['Actual Start Date'].notna() & timeline_df['Actual Deadline'].notna()
            if actual_dates_mask.any():
                has_actual_dates = True
                timeline_df.loc[actual_dates_mask, 'Actual Duration'] = (
                    timeline_df.loc[actual_dates_mask, 'Actual Deadline'] - 
                    timeline_df.loc[actual_dates_mask, 'Actual Start Date']
                ).dt.total_seconds() * 1000  # Convert to milliseconds
        
        # Helper function to safely format dates
        def safe_strftime(date, default="Not set"):
            if pd.isna(date):
                return default
            try:
                return date.strftime('%b %d, %Y')
            except:
                return default
        
        # Create custom hover text with safe numeric conversion
        def create_hover_text(row):
            base_text = (
                f"<b>{row['Task']}</b><br>"
                f"<b>Project:</b> {row['Project']}<br>"
                f"<b>Status:</b> {row['Status']}<br>"
                f"<b>Priority:</b> {row['Priority']}<br>"
                f"<b>Assignee:</b> {row['Assignee']}<br>"
                f"<b>Planned:</b> {safe_strftime(row['Planned Start Date'])} - {safe_strftime(row['Planned Deadline'])}<br>"
                f"<b>Duration:</b> {(float(row['Planned Duration']) / (1000 * 60 * 60 * 24)):.1f} days"
            )
            
            if has_actual_dates and 'Actual Duration' in row:
                try:
                    actual_duration = float(row['Actual Duration'])
                    actual_text = (
                        f"<br><b>Actual:</b> {safe_strftime(row['Actual Start Date'])} - {safe_strftime(row['Actual Deadline'])}<br>"
                        f"<b>Actual Duration:</b> {(actual_duration / (1000 * 60 * 60 * 24)):.1f} days"
                    )
                except (ValueError, TypeError):
                    actual_text = "<br><b>Actual Duration:</b> Invalid data"
                return base_text + actual_text
            return base_text
        
        timeline_df['Hover Text'] = timeline_df.apply(create_hover_text, axis=1)
        
        # Create figure
        fig = go.Figure()
        
        # Add planned timeline bars
        fig.add_trace(go.Bar(
            y=timeline_df['Task'],
            x=timeline_df['Planned Duration'].astype(float),  # Ensure numeric
            base=timeline_df['Planned Start Date'].astype('int64') // 10**6,  # Convert to milliseconds
            orientation='h',
            name='Planned',
            marker_color='rgba(78, 139, 245, 0.6)',  # Semi-transparent blue
            marker_line_color='rgba(78, 139, 245, 1.0)',
            marker_line_width=1,
            hoverinfo='text',
            hovertext=timeline_df['Hover Text'],
            customdata=timeline_df[['Status', 'Priority']]
        ))
        
        # Add actual timeline bars if available
        if has_actual_dates:
            fig.add_trace(go.Bar(
                y=timeline_df.loc[actual_dates_mask, 'Task'],
                x=timeline_df.loc[actual_dates_mask, 'Actual Duration'].astype(float),  # Ensure numeric
                base=timeline_df.loc[actual_dates_mask, 'Actual Start Date'].astype('int64') // 10**6,  # Convert to milliseconds
                orientation='h',
                name='Actual',
                marker_color='rgba(50, 205, 50, 0.6)',  # Semi-transparent green
                marker_line_color='rgba(50, 205, 50, 1.0)',
                marker_line_width=1,
                hoverinfo='text',
                hovertext=timeline_df.loc[actual_dates_mask, 'Hover Text']
            ))
        
        # Add today's line - convert datetime to milliseconds since epoch
        today = datetime.now()
        today_ms = today.timestamp() * 1000  # Convert to milliseconds
        
        fig.add_vline(
            x=today_ms,
            line_width=2,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Today: {today.strftime('%b %d, %Y')}",
            annotation_position="top right",
            annotation_font_size=12,
            annotation_font_color="red"
        )
        
        # Update layout for professional appearance
        fig.update_layout(
            title='<b>Task Timeline Comparison</b>',
            title_font_size=20,
            title_x=0.05,
            title_y=0.95,
            barmode='overlay',
            height=max(600, len(timeline_df) * 30),  # Dynamic height based on number of tasks
            hovermode='closest',
            xaxis_title='Timeline',
            yaxis_title='Tasks',
            yaxis=dict(
                autorange=True,
                showgrid=True,
                zeroline=True,
                gridcolor='rgba(0, 0, 0, 0.05)'
            ),
            xaxis=dict(
                type='date',  # Tell Plotly this is a date axis
                showgrid=True,
                zeroline=True,
                gridcolor='rgba(0, 0, 0, 0.05)',
                tickformat='%b %d, %Y'  # Format dates nicely
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=100, r=50, b=100, t=100, pad=10),
            plot_bgcolor='rgba(255, 255, 255, 0.9)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        # Add status-based color coding
        for status, color in status_colors.items():
            status_tasks = timeline_df[timeline_df['Status'] == status]
            if not status_tasks.empty:
                fig.add_trace(go.Scatter(
                    x=[None],  # These won't be visible
                    y=[None],
                    mode='markers',
                    marker=dict(size=10, color=color),
                    name=status,
                    hoverinfo='none',
                    showlegend=True
                ))
        
        # Display the figure
        st.plotly_chart(fig, use_container_width=True)
        
        # Add download button
        with st.expander("📥 Export Options", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download Data as CSV",
                    data=timeline_df.to_csv(index=False),
                    file_name="task_timeline_data.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    label="Download Chart as PNG",
                    data=fig.to_image(format="png"),
                    file_name="task_timeline.png",
                    mime="image/png"
                )


    #helper function to visualize assignee workload (Sunburst chart)
    def plot_assignee_workload(tasks_df):
        """Professional workload visualization with capacity analysis"""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Professional color palette
        status_colors = {
            "Completed": "#2ECC71",  # Green
            "In Progress": "#3498DB",  # Blue
            "Pending": "#F39C12",  # Orange
            "Overdue": "#E74C3C"  # Red
        }
        
        # Ensure we have required columns
        if "Assignee" not in tasks_df.columns or "Status" not in tasks_df.columns:
            st.error("Assignee or Status data missing")
            return
        
        # Calculate workload metrics
        workload_data = tasks_df.groupby(['Assignee', 'Status']).size().unstack().fillna(0)
        
        # Calculate totals and percentages
        workload_data['Total Tasks'] = workload_data.sum(axis=1)
        workload_data = workload_data.sort_values('Total Tasks', ascending=False)
        
        # Convert to long format for visualization
        workload_long = workload_data.drop(columns=['Total Tasks']).reset_index().melt(
            id_vars='Assignee', 
            var_name='Status', 
            value_name='Count'
        )
        
        # Create a 2-column layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Workload metrics summary
            st.markdown("### Workload Summary")
            
            # Calculate capacity metrics
            avg_tasks = workload_data['Total Tasks'].mean()
            max_tasks = workload_data['Total Tasks'].max()
            min_tasks = workload_data['Total Tasks'].min()
            
            st.metric("Average Tasks per Assignee", round(avg_tasks, 1))
            st.metric("Most Loaded Assignee", 
                    f"{workload_data['Total Tasks'].idxmax()} ({max_tasks})",
                    help="Assignee with highest task count")
            st.metric("Least Loaded Assignee", 
                    f"{workload_data['Total Tasks'].idxmin()} ({min_tasks})",
                    help="Assignee with lowest task count")
            
            # Workload distribution stats
            st.markdown("#### Distribution")
            st.write(f"**Std Dev:** {workload_data['Total Tasks'].std():.1f}")
            st.write(f"**25th Percentile:** {workload_data['Total Tasks'].quantile(0.25):.1f}")
            st.write(f"**75th Percentile:** {workload_data['Total Tasks'].quantile(0.75):.1f}")
            
            # Export raw data
            with st.expander("📤 Export Data", expanded=False):
                st.download_button(
                    label="Download Workload Data",
                    data=workload_data.reset_index().to_csv(index=False),
                    file_name="workload_analysis.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Interactive stacked bar chart
            fig = px.bar(
                workload_long,
                x='Assignee',
                y='Count',
                color='Status',
                color_discrete_map=status_colors,
                title='<b>Task Distribution by Assignee</b>',
                labels={'Count': 'Number of Tasks'},
                hover_data=['Status', 'Count'],
                category_orders={"Status": ["Completed", "In Progress", "Pending", "Overdue"]}
            )
            
            # Add reference line for average workload
            fig.add_hline(
                y=avg_tasks,
                line_dash="dot",
                line_color="#7F8C8D",
                annotation_text=f"Average: {avg_tasks:.1f}",
                annotation_position="top right"
            )
            
            # Professional styling
            fig.update_layout(
                plot_bgcolor='rgba(245,245,245,1)',
                paper_bgcolor='rgba(255,255,255,1)',
                margin=dict(t=50, b=100, l=50, r=50),
                hovermode="x unified",
                xaxis_title=None,
                yaxis_title="Number of Tasks",
                legend_title="Task Status",
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                bargap=0.2,
                height=600
            )
            
            # Rotate x-axis labels for better readability
            fig.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Workload balance analysis
        st.markdown("---")
        st.markdown("### Workload Balance Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Workload distribution pie chart
            fig_pie = px.pie(
                workload_data.reset_index(),
                names='Assignee',
                values='Total Tasks',
                title='<b>Workload Distribution</b>',
                hover_data=['Total Tasks'],
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>%{value} tasks (%{percent})<extra></extra>"
            )
            
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(t=50, b=50, l=50, r=50),
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Completion rate analysis
            if "Status" in tasks_df.columns:
                completion_rates = tasks_df.groupby('Assignee')['Status'].apply(
                    lambda x: (x == 'Completed').mean() * 100
                ).reset_index(name='Completion Rate')
                
                fig_completion = px.bar(
                    completion_rates.sort_values('Completion Rate'),
                    x='Completion Rate',
                    y='Assignee',
                    orientation='h',
                    title='<b>Completion Rates by Assignee</b>',
                    labels={'Completion Rate': 'Completion Rate (%)'},
                    color='Completion Rate',
                    color_continuous_scale='Blues'
                )
                
                fig_completion.update_layout(
                    plot_bgcolor='rgba(245,245,245,1)',
                    yaxis_title=None,
                    xaxis_title="Completion Rate (%)",
                    height=400,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                
                st.plotly_chart(fig_completion, use_container_width=True)
            else:
                st.warning("Status data not available for completion analysis")
        
        # Capacity planning section
        st.markdown("---")
        st.markdown("### Capacity Planning Insights")
        
        # Calculate workload balance score (Gini coefficient)
        def gini_coefficient(x):
            x = sorted(x)
            n = len(x)
            s = sum(x)
            if s == 0:
                return 0
            r = range(1, n+1)
            num = 2 * sum(i*j for i,j in zip(r, x))
            den = n * sum(x)
            return (num / den) - (n + 1) / n
        
        gini = gini_coefficient(workload_data['Total Tasks'])
        
        cols = st.columns(3)
        with cols[0]:
            st.metric("Workload Balance Score", 
                    f"{gini:.2f}",
                    help="0 = perfect balance, 1 = maximum imbalance")
        with cols[1]:
            overload_threshold = avg_tasks * 1.5
            overloaded = sum(workload_data['Total Tasks'] > overload_threshold)
            st.metric("Overloaded Assignees", 
                    f"{overloaded}",
                    help=f"> {overload_threshold:.1f} tasks (1.5x avg)")
        with cols[2]:
            underload_threshold = avg_tasks * 0.5
            underloaded = sum(workload_data['Total Tasks'] < underload_threshold)
            st.metric("Underloaded Assignees", 
                    f"{underloaded}",
                    help=f"< {underload_threshold:.1f} tasks (0.5x avg)")
        
        # Recommendations
        if gini > 0.3:
            st.warning("⚠️ Significant workload imbalance detected. Consider redistributing tasks.")
        elif gini > 0.15:
            st.info("ℹ️ Moderate workload imbalance. Monitor for potential bottlenecks.")
        else:
            st.success("✓ Workload is well balanced across team members")


    # Helper function to visualize budget variance (Waterfall chart)
    def plot_budget_variance(tasks_df):
        """Plot budget variance with proper null handling"""
        if tasks_df.empty or 'Budget Variance' not in tasks_df.columns:
            st.warning("No budget variance data available")
            return
        
        # Filter out tasks with no variance data
        variance_df = tasks_df[tasks_df['Budget Variance'].notna()].copy()
        
        if variance_df.empty:
            st.warning("No tasks with complete budget data available")
            return
        
        # Create waterfall chart
        fig = go.Figure(go.Waterfall(
            name="Budget Variance",
            orientation="v",
            measure=["relative"] * len(variance_df),
            x=variance_df['Task'] + "<br>(" + variance_df['Project'] + ")",
            textposition="outside",
            text=[f"${x:,.2f}" for x in variance_df['Budget Variance']],
            y=variance_df['Budget Variance'],
            connector={"line":{"color":"rgb(63, 63, 63)"}},
            increasing={"marker":{"color":"#00CC96"}},  # Green for positive variance
            decreasing={"marker":{"color":"#EF553B"}},  # Red for negative variance
        ))
        
        fig.update_layout(
            title="Task Budget Variance (Budget - Actual Cost)",
            yaxis_title="Amount ($)",
            showlegend=False,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)



    def display_project_card(project):
        """Helper function to display a project card"""
        # Unpack only the needed values
        project_id = project[0]
        name = project[2]
        description = project[3]
        start_date = project[4]
        end_date = project[5]
        budget = project[6] if len(project) > 6 else None  # Safely get budget
        
        with st.container():
            # Format budget display safely
            budget_display = "Not set"
            if budget is not None:
                try:
                    budget_display = f"${float(budget):,.2f}"
                except (TypeError, ValueError):
                    budget_display = "Invalid value"
            
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h3>{name}</h3>
                <p><strong>Description:</strong> {description or "No description"}</p>
                <p><strong>Timeline:</strong> {start_date} to {end_date}</p>
                <p><strong>Budget:</strong> {budget_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Fetch tasks for the current project
            tasks = get_tasks(project_id)
            if not tasks:
                st.warning("No tasks found for this project.")
            else:
                # Calculate progress
                completed_tasks = len([task for task in tasks if task[4] == "Completed"])
                total_tasks = len(tasks)
                progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                st.progress(int(progress))
                st.write(f"**Progress:** {completed_tasks}/{total_tasks} tasks completed ({progress:.1f}%)")


    def display_project_card_with_gantt(project):
        """Helper function to display a project card with Gantt chart"""
        project_id = project[0]
        name = project[2]
        description = project[3]
        start_date = project[4]
        end_date = project[5]
        budget = project[6] if len(project) > 6 else None
        
        with st.container():
            # Format budget display safely
            budget_display = "Not set"
            if budget is not None:
                try:
                    budget_display = f"${float(budget):,.2f}"
                except (TypeError, ValueError):
                    budget_display = "Invalid value"
            
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h3>{name}</h3>
                <p><strong>Description:</strong> {description or "No description"}</p>
                <p><strong>Timeline:</strong> {start_date} to {end_date}</p>
                <p><strong>Budget:</strong> {budget_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Fetch tasks for the current project
            tasks = get_tasks(project_id)
            if not tasks:
                st.warning("No tasks found for this project.")
            else:
                # Calculate progress
                completed_tasks = len([task for task in tasks if task[4] == "Completed"])
                total_tasks = len(tasks)
                progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                st.progress(int(progress))
                st.write(f"**Progress:** {completed_tasks}/{total_tasks} tasks completed ({progress:.1f}%)")

                # Prepare Gantt chart data
                gantt_data = []
                for task in tasks:
                    task_start = datetime.strptime(task[11], "%Y-%m-%d").date() if task[11] else datetime.strptime(start_date, "%Y-%m-%d").date()
                    task_end = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else task_start
                    
                    gantt_data.append({
                        "Task": task[2],
                        "Start": task_start,
                        "Finish": task_end,
                        "Status": task[4],
                        "Color": status_colors.get(task[4], "#f0f0f0")
                    })

                # Create Gantt chart if there are tasks
                if gantt_data:
                    st.subheader("📅 Project Timeline")
                    gantt_df = pd.DataFrame(gantt_data)
                    fig = px.timeline(
                        gantt_df,
                        x_start="Start",
                        x_end="Finish",
                        y="Task",
                        color="Status",
                        color_discrete_map=status_colors,
                        title=f"Gantt Chart for {name}"
                    )
                    fig.update_yaxes(autorange="reversed")  # Show tasks in order
                    st.plotly_chart(fig, use_container_width=True) 
    

 
    
     # Dashboard Page 
    if page == "Dashboard":
        st.markdown("---")
      
        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .dashboard-metric-card {
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                border-left: 5px solid;
                cursor: pointer;
            }
            
            .dashboard-metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            
            .metric-title {
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
                font-size: 1rem;
                color: #555;
            }
            
            .metric-icon {
                font-size: 1.5rem;
                margin-right: 0.75rem;
            }
            
            .metric-name {
                font-weight: 600;
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
                color: #333;
            }
            
            @media (max-width: 768px) {
                .dashboard-metric-card {
                    margin-bottom: 1rem;
                }
                
                .metric-value {
                    font-size: 1.75rem;
                }
            }
        </style>
        """, unsafe_allow_html=True)

        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">🏠 Dashboard</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  

        # ======= Project Summary Statistics =======
        st.subheader("📊 Project Overview")

        # Calculate project metrics
        total_projects = len(query_db("SELECT * FROM projects"))
        active_projects = len(query_db("SELECT * FROM projects WHERE end_date >= ?", (datetime.today().date(),)))
        overdue_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE p.end_date < ? 
            AND EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """, (datetime.today().date(),)))
        completed_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE NOT EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """))

        # Create columns with gaps between them
        cols = st.columns(4, gap="large")  # Added gap between columns

        # Project cards with improved styling
        with cols[0]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4E8BF5;">
                <div class="metric-title"> 
                    <span class="metric-icon">📂</span>
                    <span class="metric-name">Total Projects</span>
                </div>
                <p class="metric-value">{total_projects}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #32CD32;">
                <div class="metric-title"> 
                    <span class="metric-icon">🟢</span>
                    <span class="metric-name">Active Projects</span>
                </div>
                <p class="metric-value">{active_projects}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FF4500;">
                <div class="metric-title"> 
                    <span class="metric-icon">⚠️</span>
                    <span class="metric-name">Overdue Projects</span>
                </div>
                <p class="metric-value">{overdue_projects}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:  
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #9d50bb;">
                <div class="metric-title"> 
                    <span class="metric-icon">✅</span>
                    <span class="metric-name">Completed Projects</span>
                </div>
                <p class="metric-value">{completed_projects}</p>
            </div>
            """, unsafe_allow_html=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        # ======= Task Summary Statistics =======
        st.subheader("✅ Task Overview")

        # Calculate task metrics
        total_tasks = query_db("SELECT COUNT(*) FROM tasks")[0][0]
        overdue_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Completed' AND deadline < DATE('now')
        """)[0][0]
        upcoming_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Completed' 
            AND deadline BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
        """, (st.session_state.reminder_period,))[0][0]
        completed_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status = 'Completed'
        """)[0][0]

        # Create task metric cards with improved styling
        cols = st.columns(4, gap="large")  # Added gap between columns
        
        with cols[0]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4E8BF5;">
                <div class="metric-title">
                    <span class="metric-icon">📝</span>
                    <span class="metric-name">Total Tasks</span>
                </div>
                <p class="metric-value">{total_tasks}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FF4500;">
                <div class="metric-title">
                    <span class="metric-icon">⚠️</span>
                    <span class="metric-name">Overdue Tasks</span>
                </div>
                <p class="metric-value">{overdue_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FFA500;">
                <div class="metric-title">
                    <span class="metric-icon">🔜</span>
                    <span class="metric-name">Upcoming Tasks</span>
                </div>
                <p class="metric-value">{upcoming_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:                                                                                                                                                                                                   
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4CAF50;">
                <div class="metric-title">
                    <span class="metric-icon">✔️</span>
                    <span class="metric-name">Completed Tasks</span>
                </div>
                <p class="metric-value">{completed_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)

        # Add JavaScript to handle card clicks
        components.html("""
        <script>
            // Handle clicks on metric cards
            document.addEventListener('click', function(e) {
                if (e.target.closest('.dashboard-metric-card')) {
                    const card = e.target.closest('.dashboard-metric-card');
                    const page = card.getAttribute('data-page');
                    if (page) {
                        window.parent.postMessage({
                            'streamlit:setComponentValue': {
                                'page': page
                            }
                        }, '*');
                    }
                }
            });
            
            // Listen for messages from Streamlit
            window.addEventListener('message', function(event) {
                if (event.data && event.data.page) {
                    // This will trigger Streamlit to update the page
                    window.parent.postMessage({
                        streamlit: {
                            type: 'streamlit:componentMessage',
                            data: {page: event.data.page}
                        }
                    }, '*');
                }
            });
        </script>
        """, height=0)



        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        

        # ======= Project Health Dashboard =======
        st.subheader("📈 Project Health")
        
        # Project Selection (single selection point for entire dashboard)
        projects = get_projects()
        project_options = ["All Projects"] + [p[2] for p in projects]
        selected_project = st.selectbox("Select Project", project_options, key="health_project_select")
        
        # Filter tasks based on selection
        if selected_project == "All Projects":
            tasks_df = fetch_tasks()  
            selected_project_id = None
        else:
            selected_project_id = query_db("SELECT id FROM projects WHERE name=?", (selected_project,), one=True)[0]
            tasks_df = fetch_tasks(selected_project_id)

        # Divider with spacing
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
        
        # Create tabs (always show all tabs)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Progress", 
            "Distribution", 
            "Budget", 
            "Assignees", 
            "Productivity"
        ])
        
        # Helper function to export data and images
        def export_tab_data(tab_name, data, fig=None):
            with st.expander(f"📤 Export {tab_name} Data", expanded=False):
                col1, col2 = st.columns(2)
                
                # Export as CSV
                with col1:
                    st.download_button(
                        label="Download as CSV",
                        data=data.to_csv(index=False),
                        file_name=f"{tab_name.lower().replace(' ', '_')}_data.csv",
                        mime="text/csv"
                    )
                
                # Export image if figure exists
                if fig:
                    with col2:
                        buf = io.BytesIO()
                        fig.write_image(buf, format="png", width=1000)
                        st.download_button(
                            label="Download as PNG",
                            data=buf.getvalue(),
                            file_name=f"{tab_name.lower().replace(' ', '_')}_chart.png",
                            mime="image/png"
                        )
        
        # Tab1
        with tab1:  # Progress tab
            st.write("### Project Progress with Gantt Chart")
            
            if selected_project_id:
                # Get the selected project's details
                project_data = query_db("""
                    SELECT p.name, p.start_date, p.end_date, 
                        COUNT(t.id) as total_tasks,
                        SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
                    FROM projects p
                    LEFT JOIN tasks t ON p.id = t.project_id
                    WHERE p.id = ?
                    GROUP BY p.id
                """, (selected_project_id,), one=True)
                
                if project_data:
                    name, start_date, end_date, total_tasks, completed_tasks = project_data
                    
                    # Fetch tasks for the selected project with both planned and actual dates
                    tasks = query_db("""
                        SELECT id, title, 
                            start_date as planned_start_date, 
                            deadline as planned_deadline, 
                            actual_start_date,
                            actual_deadline,
                            status, priority 
                        FROM tasks 
                        WHERE project_id = ?
                        ORDER BY deadline
                    """, (selected_project_id,))
                    
                    if tasks:
                        # Prepare Gantt chart data
                        gantt_data = []
                        today = datetime.now().date()
                        
                        for task in tasks:
                            task_id, title, planned_start, planned_end, actual_start, actual_end, status, priority = task
                            
                            # Convert dates to datetime.date objects with fallbacks
                            planned_start_date = pd.to_datetime(planned_start).date() if planned_start else pd.to_datetime(start_date).date()
                            planned_deadline = pd.to_datetime(planned_end).date() if planned_end else pd.to_datetime(end_date).date()
                            actual_start_date = pd.to_datetime(actual_start).date() if actual_start else planned_start_date
                            actual_deadline = pd.to_datetime(actual_end).date() if actual_end else planned_deadline
                            
                            # Add both planned and actual tasks to the data
                            gantt_data.append({
                                "Task": title,
                                "Start": planned_start_date,
                                "Finish": planned_deadline,
                                "Type": "Planned",
                                "Status": status,
                                "Priority": priority
                            })
                            
                            if actual_start and actual_end:  # Only add actual timeline if dates exist
                                gantt_data.append({
                                    "Task": title,
                                    "Start": actual_start_date,
                                    "Finish": actual_deadline,
                                    "Type": "Actual",
                                    "Status": status,
                                    "Priority": priority
                                })
                        
                        gantt_df = pd.DataFrame(gantt_data)
                        
                        # Convert dates to strings for Plotly timeline
                        gantt_df['Start'] = gantt_df['Start'].astype(str)
                        gantt_df['Finish'] = gantt_df['Finish'].astype(str)


                        

                        
                        # Create Gantt chart with proper bar sizing                                     
                        fig = px.timeline(
                            gantt_df,
                            x_start="Start",
                            x_end="Finish",
                            y="Task",
                            color="Type",
                            color_discrete_map={
                                "Planned": "rgba(158, 202, 225, 0.7)",  # Semi-transparent light blue
                                "Actual": "rgba(78, 121, 167, 0.9)"     # Darker blue with slight transparency
                            },
                            title=f"Gantt Chart for {name}",
                            hover_data=["Status", "Priority"],
                            width=1000  # Fixed width for better control
                        )

                        # Reverse the y-axis to show tasks in correct order
                        fig.update_yaxes(autorange="reversed")
                        
                        # Customize the chart appearance with better bar sizing
                        fig.update_traces(
                            marker_line_color='rgba(0,0,0,0.5)',  # Add border to bars
                            marker_line_width=1,                  # Border width
                            width=0.4                            # Make bars thicker (0-1 scale)
                        )

                        # Calculate today's position correctly
                        min_date = pd.to_datetime(gantt_df['Start'].min())
                        max_date = pd.to_datetime(gantt_df['Finish'].max())
                        today_dt = pd.to_datetime(today)
                        
                        # Convert to milliseconds since epoch for precise positioning
                        min_ms = min_date.value // 10**6  # Convert nanoseconds to milliseconds
                        max_ms = max_date.value // 10**6
                        today_ms = today_dt.value // 10**6
                        
                        # Calculate position (0-1 range)
                        if max_ms > min_ms:
                            today_position = (today_ms - min_ms) / (max_ms - min_ms)
                        else:
                            today_position = 0.5  # Default to middle if no date range

                        # Add today's line with precise positioning
                        fig.add_vline(
                            x=today_position * (max_ms - min_ms) + min_ms,  # Convert back to absolute position
                            line_dash="dot",
                            line_color="red",
                            line_width=3,  # Thicker line
                            annotation_text=f"Today: {today.strftime('%b %d, %Y')}",
                            annotation_position="top right",
                            annotation_font_size=12,
                            annotation_font_color="red"
                        )

                        # Adjust layout for better readability
                        fig.update_layout(
                            height=max(800, len(tasks) * 50),  # Taller chart with more space per task
                            bargap=0.2,                       # Space between bars
                            xaxis_range=[min_ms, max_ms],     # Set exact date range
                            xaxis_tickformat='%b %d, %Y',     # Better date formatting
                            hoverlabel=dict(
                                bgcolor="white",
                                font_size=12,
                                font_family="Arial"
                            )
                        )

                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True, use_container_height=True)
                        
                        # Project summary metrics
                        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                        status = "Completed" if progress == 100 else "In Progress" if progress > 0 else "Not Started"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Tasks", total_tasks)
                        with col2:
                            st.metric("Completed Tasks", completed_tasks)
                        with col3:
                            st.metric("Progress", f"{progress:.1f}%", status)
                        
                        # Task timeline details table with standardized column names
                        st.write("### Task Timeline Details")
                        display_df = pd.DataFrame([{
                            "Task": task[1],
                            "Status": task[6],
                            "Priority": task[7],
                            "Planned Start Date": pd.to_datetime(task[2]).date() if task[2] else pd.to_datetime(start_date).date(),
                            "Planned Deadline": pd.to_datetime(task[3]).date() if task[3] else pd.to_datetime(end_date).date(),
                            "Actual Start Date": pd.to_datetime(task[4]).date() if task[4] else "Not started",
                            "Actual Deadline": pd.to_datetime(task[5]).date() if task[5] else "Not completed",
                            "Planned Duration": (pd.to_datetime(task[3]).date() - pd.to_datetime(task[2]).date()).days if task[2] and task[3] else "N/A",
                            "Actual Duration": (pd.to_datetime(task[5]).date() - pd.to_datetime(task[4]).date()).days if task[4] and task[5] else "N/A",
                            "Variance": "N/A" if not task[4] or not task[5] else 
                                ((pd.to_datetime(task[5]).date() - pd.to_datetime(task[4]).date()).days - 
                                (pd.to_datetime(task[3]).date() - pd.to_datetime(task[2]).date()).days)
                        } for task in tasks])
                        
                        st.dataframe(
                            display_df,
                            column_config={
                                "Planned Start Date": st.column_config.DateColumn("Planned Start Date"),
                                "Planned Deadline": st.column_config.DateColumn("Planned Deadline"),
                                "Actual Start Date": st.column_config.DateColumn("Actual Start Date"),
                                "Actual Deadline": st.column_config.DateColumn("Actual Deadline"),
                                "Planned Duration": st.column_config.NumberColumn("Planned Duration (days)"),
                                "Actual Duration": st.column_config.NumberColumn("Actual Duration (days)"),
                                "Variance": st.column_config.NumberColumn("Variance (days)")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Export functionality
                        export_tab_data("Progress", display_df, fig)                                                           
                    else:
                        st.warning(f"No tasks found for project {name}")
                else:
                    st.warning("Project data not available")
            else:
                st.warning("Please select a specific project to view the Gantt chart (not 'All Projects')")


        with tab2:  # Distribution tab
            if not tasks_df.empty:
                # Status/Priority Distribution
                col1, col2 = st.columns(2)
                with col1:
                    fig_status = px.pie(
                        tasks_df,
                        names="Status",
                        title="Task Status Distribution",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                    
                    # Prepare status data for export
                    status_counts = tasks_df["Status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    export_tab_data("Status Distribution", status_counts, fig_status)
                    
                with col2:
                    fig_priority = px.pie(
                        tasks_df,
                        names="Priority",
                        title="Task Priority Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig_priority, use_container_width=True)
                    
                    # Prepare priority data for export
                    priority_counts = tasks_df["Priority"].value_counts().reset_index()
                    priority_counts.columns = ["Priority", "Count"]
                    export_tab_data("Priority Distribution", priority_counts, fig_priority)
            else:
                st.warning("No tasks found for visualization")

        with tab3:  # Budget tab
            if not tasks_df.empty:
                # Budget Variance Visualization
                st.write("### Budget Variance by Project")
                budget_data = tasks_df.groupby("Project").agg({
                    "Budget": "sum",
                    "Actual Cost": "sum"
                }).reset_index()
                budget_data["Variance"] = budget_data["Budget"] - budget_data["Actual Cost"]
                
                fig_budget = px.bar(
                    budget_data,
                    x="Project",
                    y=["Budget", "Actual Cost"],
                    title="Budget vs Actual Cost",
                    barmode="group",
                    labels={"value": "Amount ($)", "variable": "Type"},
                    color_discrete_map={
                        "Budget": '#3498db',
                        "Actual Cost": '#e74c3c'
                    }
                )
                st.plotly_chart(fig_budget, use_container_width=True)
                
                # Variance breakdown
                fig_variance = px.bar(
                    budget_data,
                    x="Project",
                    y="Variance",
                    title="Budget Variance (Budget - Actual)",
                    color="Variance",
                    color_continuous_scale=px.colors.diverging.RdBu,
                    labels={"Variance": "Amount ($)"}
                )
                st.plotly_chart(fig_variance, use_container_width=True)
                
                # Export functionality
                export_tab_data("Budget Analysis", budget_data, fig_budget)
                export_tab_data("Budget Variance", budget_data, fig_variance)
            else:
                st.warning("No tasks found for budget analysis")

        with tab4:  # Assignees tab
            if not tasks_df.empty and "Assignee" in tasks_df.columns:
                # Task Distribution by Assignee
                st.write("### Task Distribution by Assignee")
                assignee_dist = tasks_df["Assignee"].value_counts().reset_index()
                assignee_dist.columns = ["Assignee", "Task Count"]
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_assignee_pie = px.pie(
                        assignee_dist,
                        names="Assignee",
                        values="Task Count",
                        title="Tasks per Assignee",
                        hole=0.4
                    )
                    st.plotly_chart(fig_assignee_pie, use_container_width=True)
                    export_tab_data("Assignee Distribution", assignee_dist, fig_assignee_pie)
                
                with col2:
                    fig_assignee_bar = px.bar(
                        assignee_dist,
                        x="Assignee",
                        y="Task Count",
                        title="Task Count by Assignee",
                        color="Assignee"
                    )
                    st.plotly_chart(fig_assignee_bar, use_container_width=True)
                    export_tab_data("Assignee Task Count", assignee_dist, fig_assignee_bar)
            else:
                st.warning("No assignee data available")

        with tab5:  # Productivity tab
            if not tasks_df.empty:
                st.write("### Assignee Productivity Metrics")
                
                # Fetch assignee productivity data
                if st.session_state.user_role == "Admin":
                    productivity_query = """
                        SELECT 
                            u.username as Assignee,
                            COUNT(t.id) as TotalTasks,
                            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                            SUM(t.time_spent) as TotalTimeSpent,
                            AVG(julianday(t.deadline) - julianday(t.start_date)) as AvgDuration
                        FROM tasks t
                        LEFT JOIN users u ON t.assigned_to = u.id
                        GROUP BY u.username
                        ORDER BY CompletedTasks DESC
                    """
                    productivity_data = query_db(productivity_query)
                else:
                    productivity_query = """
                        SELECT 
                            u.username as Assignee,
                            COUNT(t.id) as TotalTasks,
                            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                            SUM(t.time_spent) as TotalTimeSpent,
                            AVG(julianday(t.deadline) - julianday(t.start_date)) as AvgDuration
                        FROM tasks t
                        LEFT JOIN users u ON t.assigned_to = u.id
                        WHERE t.assigned_to = ?
                        GROUP BY u.username
                        ORDER BY CompletedTasks DESC
                    """
                    productivity_data = query_db(productivity_query, (st.session_state.user_id,))
                
                if productivity_data:
                    # Create DataFrame
                    productivity_df = pd.DataFrame(productivity_data, columns=[
                        "Assignee", "Total Tasks", "Completed Tasks", "Time Spent (hours)", "Avg Duration (days)"
                    ])
                    
                    # Calculate completion rate and efficiency
                    productivity_df["Completion Rate"] = (productivity_df["Completed Tasks"] / productivity_df["Total Tasks"] * 100).round(1)
                    productivity_df["Tasks/Hour"] = (productivity_df["Completed Tasks"] / productivity_df["Time Spent (hours)"]).round(2)
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Most Productive", productivity_df.iloc[0]["Assignee"])
                    with col2:
                        st.metric("Highest Completion Rate", 
                                f"{productivity_df['Completion Rate'].max()}%")
                    with col3:
                        st.metric("Most Efficient", 
                                f"{productivity_df['Tasks/Hour'].max()} tasks/hour")
                    
                    # Display the productivity table
                    st.dataframe(
                        productivity_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Visualizations
                    col1, col2 = st.columns(2)
                    with col1:
                        # Completion Rate by Assignee
                        fig_completion = px.bar(
                            productivity_df,
                            x="Assignee",
                            y="Completion Rate",
                            title="Completion Rate by Assignee",
                            color="Completion Rate",
                            color_continuous_scale=px.colors.sequential.Blues
                        )
                        st.plotly_chart(fig_completion, use_container_width=True)
                        export_tab_data("Completion Rate", productivity_df, fig_completion)
                    
                    with col2:
                        # Efficiency by Assignee
                        fig_efficiency = px.bar(
                            productivity_df,
                            x="Assignee",
                            y="Tasks/Hour",
                            title="Task Efficiency (Tasks per Hour)",
                            color="Tasks/Hour",
                            color_continuous_scale=px.colors.sequential.Greens
                        )
                        st.plotly_chart(fig_efficiency, use_container_width=True)
                        export_tab_data("Efficiency", productivity_df, fig_efficiency)
                    
                    # Time Spent vs Tasks Completed
                    fig_time_vs_tasks = px.scatter(
                        productivity_df,
                        x="Time Spent (hours)",
                        y="Completed Tasks",
                        size="Total Tasks",
                        color="Assignee",
                        title="Time Spent vs Tasks Completed",
                        hover_name="Assignee",
                        labels={
                            "Time Spent (hours)": "Time Spent (hours)",
                            "Completed Tasks": "Completed Tasks"
                        }
                    )
                    st.plotly_chart(fig_time_vs_tasks, use_container_width=True)
                    export_tab_data("Time vs Tasks", productivity_df, fig_time_vs_tasks)
                else:
                    st.warning("No productivity data available")
            else:
                st.warning("No tasks found for productivity analysis")

        # ======= Global Export Options =======
        st.markdown("---")
        st.subheader("📤 Export All Data")
        with st.expander("💾 Comprehensive Export Options", expanded=False):
            if not tasks_df.empty:
                st.download_button(
                    label="Download All Task Data as CSV",
                    data=tasks_df.to_csv(index=False),
                    file_name="all_task_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No task data available for export")




    # Projects Page
    elif page == "Projects":
        st.markdown("---")
        

        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">📂 Projects</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)


        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  
        
        # Initialize success message state
        if 'show_project_success' not in st.session_state:
            st.session_state.show_project_success = False
        
        # Display success message if flag is True
        if st.session_state.show_project_success:
            st.success("Project added successfully!")
            st.session_state.show_project_success = False
        
        # Fetch all users for owner dropdown
        users = query_db("SELECT id, username FROM users")
        user_options = {user[0]: user[1] for user in users}

        
        # In the Projects page section, modify the "Add New Project" form as follows:

        # ======= Add New Project Section =======
        st.subheader("➕ Add New Project")

        # Only show the project creation form if user is admin
        if st.session_state.user_role == "Admin":

            with st.expander("Create New Project", expanded=False):
                with st.form(key="add_project_form", clear_on_submit=True):
                    name = st.text_input("Project Name*", help="Project name must be unique (case-insensitive)")
                    description = st.text_area("Description")
                    
                    # Project Owner Dropdown
                    project_owner = st.selectbox(
                        "Project Owner*",
                        options=list(user_options.values()),
                        format_func=lambda x: user_options.get(x, x)
                    )
                    
                    # Project Dates
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Start Date*")
                    with col2:
                        due_date = st.date_input("Due Date*")
                    
                    # Project Budget
                    budget = st.number_input("Project Budget", min_value=0.0, value=0.0)
                    
                    if st.form_submit_button("Add Project"):
                        # Validate required fields
                        if not name.strip():
                            st.error("Project name is required")
                        elif due_date < start_date:
                            st.error("Due date must be on or after the start date")
                        else:
                            # Check for existing project name (case-insensitive)
                            existing_project = query_db(
                                "SELECT 1 FROM projects WHERE LOWER(name) = LOWER(?)", 
                                (name.strip(),), 
                                one=True
                            )
                            
                            if existing_project:
                                st.error(f"A project with name '{name.strip()}' already exists (case-insensitive check)")
                            else:
                                project_owner_id = [user_id for user_id, username in user_options.items() if username == project_owner][0]
                                query_db("""
                                    INSERT INTO projects (user_id, name, description, start_date, end_date, budget)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (project_owner_id, name.strip(), description, start_date, due_date, budget))
                                st.session_state.show_project_success = True
                                st.rerun()

        else:
            st.warning("⛔ Only administrators can create new projects. Please contact your admin.")                       
        
        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        

        
        # ======= Project Analytics Section =======
        st.subheader("📂 Select Project")


        # First fetch all project data (same as before)
        projects_data = query_db("""
            SELECT 
                p.id, 
                p.user_id as owner_id, 
                p.name, 
                p.description, 
                p.start_date as planned_start_date,
                p.end_date as planned_deadline,
                p.budget,
                ROUND(COALESCE(SUM(t.actual_cost), 0)) as actual_cost,
                ROUND(p.budget - COALESCE(SUM(t.actual_cost), 0)) as budget_variance,
                COUNT(t.id) as task_count,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                u.username as owner_name,
                (ROUND(SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(t.id), 0), 2)) as completion_pct,
                julianday(p.end_date) - julianday(p.start_date) as planned_duration,
                CASE
                    WHEN MIN(t.actual_start_date) IS NULL OR MAX(t.actual_deadline) IS NULL THEN NULL
                    ELSE julianday(MAX(t.actual_deadline)) - julianday(MIN(t.actual_start_date))
                END as actual_duration
            FROM projects p
            LEFT JOIN tasks t ON t.project_id = p.id
            LEFT JOIN users u ON p.user_id = u.id
            GROUP BY p.id
        """)

        # Convert to DataFrame
        project_df = pd.DataFrame(projects_data, columns=[
            "ID", "Owner ID", "Project", "Description", "Planned Start Date", "Planned Deadline",
            "Budget", "Actual Cost", "Budget Variance", "Total Tasks",
            "Completed Tasks", "Owner", "Completion %",
            "Planned Duration (days)", "Actual Duration (days)"
        ])

        # Ensure date columns are proper datetime objects
        project_df["Planned Start Date"] = pd.to_datetime(project_df["Planned Start Date"])
        project_df["Planned Deadline"] = pd.to_datetime(project_df["Planned Deadline"])

        # Create filter widgets - matching your task page style but simplified
        with st.expander("🔍 Filter Projects", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Project filter - matches your task page dropdown style
                project_options = ['All Projects'] + sorted(project_df['Project'].unique().tolist())
                selected_project = st.selectbox(
                    "Filter by Project", 
                    project_options,
                    key="project_filter"
                )
            
            with col2:
                # Owner filter - matches your task page dropdown style
                owner_options = ['All Owners'] + sorted(project_df['Owner'].dropna().unique().tolist())
                selected_owner = st.selectbox(
                    "Filter by Owner",
                    owner_options,
                    key="owner_filter"
                )

        # Apply filters - same logic as your task page but simplified
        filtered_df = project_df.copy()

        if selected_project != 'All Projects':
            filtered_df = filtered_df[filtered_df['Project'] == selected_project]

        if selected_owner != 'All Owners':
            filtered_df = filtered_df[filtered_df['Owner'] == selected_owner]

        # Display the filtered table with same styling as your task page
        st.subheader("📊 Project Analytics")

        # Create a copy for display with formatted currency values
        display_df = filtered_df.copy()

        # Format currency columns as whole numbers (matches your task page style)
        display_df["Actual Cost"] = display_df["Actual Cost"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )
        display_df["Budget Variance"] = display_df["Budget Variance"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )
        display_df["Budget"] = display_df["Budget"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )

        # Format durations (matches your task page style)
        display_df["Planned Duration"] = display_df["Planned Duration (days)"].apply(
            lambda x: f"{float(x):.1f} days" if pd.notnull(x) else "N/A"
        )
        display_df["Actual Duration"] = display_df["Actual Duration (days)"].apply(
            lambda x: f"{float(x):.1f} days" if pd.notnull(x) else "N/A"
        )

        # Display the formatted table (matches your task page style)
        st.dataframe(
            display_df[[
                "Project", "Owner", "Planned Start Date", "Planned Deadline",
                "Planned Duration", "Actual Duration", "Total Tasks",
                "Completed Tasks", "Completion %", "Budget", "Actual Cost",
                "Budget Variance"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Planned Start Date": st.column_config.DateColumn("Planned Start Date"),
                "Planned Deadline": st.column_config.DateColumn("Planned Deadline"),
                "Completion %": st.column_config.NumberColumn(
                    "Completion %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

        st.write("</div>", unsafe_allow_html=True)  # Close the styled container


        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)


        # Visualization Tabs (controlled by the same filters)
        tab1, tab2, tab3, tab4 = st.tabs(["Timeline", "Budget", "Analytics", "Duration"])

        # In your Projects page section where you have tabs:
        with tab1:  # Timeline tab
            # First ensure the dataframe has the correct columns
            if all(col in project_df.columns for col in ['Planned Start Date', 'Planned Deadline']):
                plot_project_timeline(project_df)
            else:
                st.error("Required columns for timeline visualization not found in data")

        with tab2:  # Budget tab
            plot_budget_comparison(project_df)
            plot_project_health(project_df)

        with tab3:  # Analytics tab
            plot_completion_heatmap(project_df)
            plot_duration_variance(project_df)

        with tab4:  # Add this as a new tab in your existing tab structure
            st.subheader("⏱️ Duration Analysis")
            # plot_plan_vs_actual_gantt(project_df)
            # plot_duration_variance(project_df)
            plot_duration_comparison(project_df)
                

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)


        
        
        # ======= Project List Section =======
        # ======= Project List Section =======
        st.subheader("📋 Project List")

        # Add custom CSS for card styling
        st.markdown("""
        <style>
            /* Card styling */
            .project-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
                background-color: #FFFFFF;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            
            .project-card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            
            .project-card-title {
                margin: 0;
                color: #2c3e50;
                font-size: 1.1rem;
                font-weight: 600;
                flex-grow: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .project-card-body {
                flex-grow: 1;
                margin-bottom: 12px;
            }
            
            .project-card-description {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 12px;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            
            .project-card-detail {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                font-size: 0.85rem;
            }
            
            .project-card-detail-icon {
                margin-right: 8px;
                color: #666;
            }
            
            .project-card-footer {
                margin-top: auto;
                padding-top: 12px;
                border-top: 1px solid #f0f0f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .project-status {
                font-size: 0.8rem;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
            }
            
            .status-overdue {
                background-color: #FFEBEE;
                color: #D32F2F;
            }
            
            .status-ontrack {
                background-color: #E8F5E9;
                color: #388E3C;
            }
            
            .project-card-actions {
                display: flex;
                gap: 8px;
            }
            
            /* Ensure columns have equal height */
            [data-testid="column"] {
                display: flex;
                flex-direction: column;
            }
            
            /* Make sure all cards in a row have equal height */
            .stColumn > div {
                height: 100%;
            }
        </style>
        """, unsafe_allow_html=True)            

        # Fetch all projects with additional details
        projects = query_db("""
            SELECT p.id, p.user_id, p.name, p.description, p.start_date, p.end_date, p.budget, 
                u.username as owner_name
            FROM projects p
            LEFT JOIN users u ON p.user_id = u.id
            ORDER BY p.name
        """)

        # Get user options for owner dropdown
        users = query_db("SELECT id, username FROM users")
        user_options = {user[0]: user[1] for user in users}

        # Replace text search with dropdown selection
        project_names = ["All Projects"] + [p[2] for p in projects]  # p[2] is the project name
        selected_project = st.selectbox("🔍 Filter Projects", project_names)

        # Get filtered projects
        if selected_project == "All Projects":
            filtered_projects = projects
        else:
            filtered_projects = [p for p in projects if p[2] == selected_project]

        if not filtered_projects:
            st.info("No projects found matching your selection.")
        else:
            # Display projects in a grid of cards
            cols = st.columns(3)  # 3 columns for the grid
            for idx, project in enumerate(filtered_projects):
                project_id, owner_id, name, description, start_date, end_date, budget, owner_username = project
                
                # Format dates and budget
                start_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%b %d, %Y") if start_date else "Not set"
                end_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%b %d, %Y") if end_date else "Not set"
                budget_fmt = f"${float(budget):,.2f}" if budget else "Not set"
                
                # Check if project is overdue
                today = datetime.now().date()
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today
                is_overdue = end_date_obj < today
                status_class = "status-overdue" if is_overdue else "status-ontrack"
                status_text = "⚠️ Overdue" if is_overdue else "🟢 On track"
                
                with cols[idx % 3]:  # Distribute across columns
                    # Create a card container
                    st.markdown(f"""
                    <div class="project-card">
                        <div class="project-card-header">
                            <h3 class="project-card-title" title="{name}">{name}</h3>
                        </div>
                        <div class="project-card-body">
                            <p class="project-card-description" title="{description or 'No description provided'}">
                                {description or "No description provided"}
                            </p>
                            <div class="project-card-detail">
                                <span class="project-card-detail-icon">👤</span>
                                <span>{owner_username}</span>
                            </div>
                            <div class="project-card-detail">
                                <span class="project-card-detail-icon">📅</span>
                                <span>{start_fmt} → {end_fmt}</span>
                            </div>
                            <div class="project-card-detail">
                                <span class="project-card-detail-icon">💰</span>
                                <span>{budget_fmt}</span>
                            </div>
                        </div>
                        <div class="project-card-footer">
                            <span class="project-status {status_class}">{status_text}</span>
                            <div class="project-card-actions">
                    """, unsafe_allow_html=True)
                    
                    # Action buttons - Only show if admin or project owner
                    show_edit = st.session_state.user_role == "Admin" or owner_id == st.session_state.user_id
                    show_delete = st.session_state.user_role == "Admin"
                    
                    if show_edit:
                        if st.button("✏️ Edit", key=f"edit_{project_id}"):
                            st.session_state['editing_project_id'] = project_id
                            st.rerun()
                    
                    if show_delete:
                        if st.button("🗑️ Delete", key=f"delete_{project_id}"):
                            st.session_state['deleting_project_id'] = project_id
                            st.rerun()
                    
                    st.markdown("""
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)



        # Edit Form Modal - This needs to be OUTSIDE the card display loop
        if 'editing_project_id' in st.session_state and st.session_state.editing_project_id:
            project_id = st.session_state.editing_project_id
            project = next((p for p in projects if p[0] == project_id), None)
            
            if project:
                # Create a modal-like container
                with st.expander(f"✏️ Editing Project: {project[2]}", expanded=True):
                    with st.form(f"edit_form_{project_id}"):
                        new_name = st.text_input("Name", value=project[2])
                        new_desc = st.text_area("Description", value=project[3])
                        
                        if st.session_state.user_role == "Admin":
                            current_owner_name = user_options.get(project[1], "Unknown")
                            new_owner_name = st.selectbox(
                                "Owner",
                                options=list(user_options.values()),
                                index=list(user_options.values()).index(current_owner_name) if current_owner_name in user_options.values() else 0
                            )
                            new_owner_id = [uid for uid, uname in user_options.items() if uname == new_owner_name][0]
                        else:
                            new_owner_id = project[1]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            new_start = st.date_input("Start Date", value=datetime.strptime(project[4], "%Y-%m-%d").date())
                        with col2:
                            new_end = st.date_input("Due Date", value=datetime.strptime(project[5], "%Y-%m-%d").date())
                        
                        new_budget = st.number_input("Budget", value=float(project[6]) if project[6] else 0.0, step=0.01)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save Changes"):
                                query_db("""
                                    UPDATE projects SET 
                                    name=?, description=?, user_id=?, 
                                    start_date=?, end_date=?, budget=?
                                    WHERE id=?
                                """, (new_name, new_desc, new_owner_id, 
                                    new_start, new_end, new_budget, project_id))
                                st.session_state.pop('editing_project_id', None)
                                st.success("Project updated successfully!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state.pop('editing_project_id', None)
                                st.rerun()

        # Delete Confirmation Modal - Also needs to be OUTSIDE the card display loop
        if 'deleting_project_id' in st.session_state and st.session_state.deleting_project_id:
            project_id = st.session_state.deleting_project_id
            project = next((p for p in projects if p[0] == project_id), None)
            
            if project:
                # Create a modal-like container
                with st.expander(f"🗑️ Delete Project: {project[2]}", expanded=True):
                    st.warning("⚠️ This action cannot be undone!")
                    st.error("All associated tasks and data will be permanently deleted!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm Deletion", key=f"confirm_delete_{project_id}", type="primary"):
                            delete_project(project_id)
                            st.session_state.pop('deleting_project_id', None)
                            st.success("Project deleted successfully!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_delete_{project_id}"):
                            st.session_state.pop('deleting_project_id', None)
                            st.rerun()


 

    
    # Tasks Page
    elif page == "Tasks":
        st.markdown("---")
        
        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .task-grid-container {
                position: relative;
                margin-bottom: 20px;
            }
            
            .task-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 0;
            }
            
            .task-column {
                flex: 1;
                min-width: 0;
                padding: 0 15px;
                position: relative;
            }
            
            .task-column:not(:last-child)::after {
                content: "";
                position: absolute;
                right: 0;
                top: 0;
                bottom: 0;
                width: 1px;
                background: linear-gradient(to bottom, 
                    rgba(0,0,0,0) 0%, 
                    rgba(224,224,224,1) 10%, 
                    rgba(224,224,224,1) 90%, 
                    rgba(0,0,0,0) 100%);
            }
            
            .task-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                height: 100%;
                margin-bottom: 20px;
            }
            
            .task-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .task-card-overdue {
                border-left: 4px solid #ff4d4d;
                background: #fff5f5;
            }
            
            .task-card-content {
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            
            .task-card-buttons {
                margin-top: auto;
                padding-top: 10px;
                display: flex;
                justify-content: space-between;
            }
            
            @media (max-width: 900px) {
                .task-column {
                    flex: 100%;
                    padding: 0;
                    margin-bottom: 20px;
                }
                
                .task-column:not(:last-child) {
                    padding-bottom: 20px;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                .task-column:not(:last-child)::after {
                    display: none;
                }
            }
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">✅ Task Management</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)
        
        # ======= Section Divider =======
        st.markdown("---")
        st.header("📂 Create New Tasks")

        # Get all projects for admin, or only owned projects for non-admin
        if st.session_state.user_role == "Admin":
            projects = query_db("SELECT id, name, user_id FROM projects ORDER BY name")
        else:
            projects = query_db("SELECT id, name, user_id FROM projects WHERE user_id = ? ORDER BY name", 
                            (st.session_state.user_id,))

        # Only show the task creation form if user is admin or has owned projects
        if st.session_state.user_role == "Admin" or projects:
            with st.expander("➕ Create New Task", expanded=False):
                with st.form(key="create_task_form", clear_on_submit=True):
                    # Create project dropdown options
                    if st.session_state.user_role == "Admin":
                        project_options = [project[1] for project in projects]  # All projects for admin
                    else:
                        project_options = [project[1] for project in projects]  # Only owned projects
                    
                    selected_project = st.selectbox("Project*", project_options)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        title = st.text_input("Task Title*", placeholder="Enter task name")
                        start_date = st.date_input("Start Date*")
                    with col2:
                        priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
                        deadline = st.date_input("Deadline*")
                        budget = st.number_input("Budget ($)", min_value=0.0, value=0.0, step=0.01)
                    
                    description = st.text_area("Description", placeholder="Enter detailed task description")
                    
                    spent_time = st.number_input("Time Spent (hours)", min_value=0.0, value=0.0, step=0.5)
                    
                    # Get all users for assignment dropdown
                    team_members = query_db("SELECT id, username FROM users ORDER BY username")
                    assigned_to = st.selectbox("Assign To*", [member[1] for member in team_members])
                    
                    submitted = st.form_submit_button("Create Task")
                    
                    if submitted:
                        # Validate all required fields
                        if not title.strip():
                            st.error("Task title is required")
                        elif deadline < start_date:
                            st.error("Deadline must be on or after the start date")
                        else:
                            project_id = query_db("SELECT id FROM projects WHERE name = ?", (selected_project,), one=True)[0]
                            assigned_to_id = query_db("SELECT id FROM users WHERE username = ?", (assigned_to,), one=True)[0]
                            
                            query_db("""
                                INSERT INTO tasks 
                                (project_id, title, description, start_date, deadline, priority, 
                                assigned_to, budget, time_spent)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                project_id, title.strip(), description, start_date, deadline, 
                                priority, assigned_to_id, budget, spent_time
                            ))
                            
                            # Show both toast and success message for reliability
                            try:
                                st.toast("✅ Task created successfully!", icon="✅")
                            except:
                                pass  # Fallback if toast isn't available
                            
                            st.success("Task created successfully!")
                            
                            # Add slight delay before refresh to ensure message is seen
                            time.sleep(1.5)
                            st.rerun()
        else:
            st.warning("⛔ You don't have permission to create tasks. Only project owners can create tasks for their projects.")

        # ======= Section Divider =======
        
        # ======= Project Tasks Section =======

        # Display Project Tasks Section
        # Display Project Tasks Section
        st.markdown("---")
        st.header("📋 Project Tasks")

        projects = get_projects()

        if not projects:
            st.warning("No projects found in the database.")
        else:
            # Create dropdown for project selection
            project_options = ["Select a project..."] + [project[2] for project in projects]
            selected_project = st.selectbox("Select Project to View Tasks", project_options)
            
            if selected_project != "Select a project...":
                project_id = query_db("SELECT id FROM projects WHERE name=?", (selected_project,), one=True)[0]
                tasks = query_db("SELECT * FROM tasks WHERE project_id=?", (project_id,))
                
                st.write(f"### Tasks for: {selected_project}")
                
                if not tasks:
                    st.warning("No tasks found for this project.")
                else:
                    # Custom CSS for visible dividers
                    st.markdown("""
                    <style>
                        .task-column {
                            position: relative;
                            padding: 0 15px;
                        }
                        .task-column:not(:last-child)::after {
                            content: "";
                            position: absolute;
                            right: 0;
                            top: 10%;
                            bottom: 10%;
                            width: 1px;
                            background-color: #e0e0e0;
                        }
                        .task-card {
                            border: 1px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 16px;
                            margin-bottom: 20px;
                            background: white;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    # Create columns for the grid
                    cols = st.columns(3)
                    
                    for i, task in enumerate(tasks):
                        task_id = task[0]
                        is_overdue = (datetime.strptime(task[6], "%Y-%m-%d").date() < datetime.today().date() 
                                    if task[6] else False) and task[4] != "Completed"
                        
                        # Get assigned user's name
                        assigned_to_id = task[10]
                        assigned_user = query_db("SELECT username FROM users WHERE id = ?", (assigned_to_id,), one=True)
                        assigned_to_name = assigned_user[0] if assigned_user else "Unassigned"
                        
                        # Get the current column (0, 1, or 2)
                        col = cols[i % 3]
                        
                        with col:
                            # Task card with conditional overdue styling
                            card_border = "4px solid #ff4d4d" if is_overdue else "1px solid #e0e0e0"
                            card_bg = "#fff5f5" if is_overdue else "white"
                            
                            st.markdown(
                                f'<div style="border-left:{card_border}; border-radius:8px; padding:16px; '
                                f'margin-bottom:20px; background:{card_bg}; box-shadow:0 2px 8px rgba(0,0,0,0.1)">'
                                f'<h3 style="margin-top:0;color:#2c3e50;">{task[2]}</h3>'
                                f'<p><strong>Status:</strong> {task[4]} {"⚠️ OVERDUE" if is_overdue else ""}</p>'
                                f'<p><strong>Priority:</strong> <span style="color:{priority_colors.get(task[8], "#000000")}">{task[8]}</span></p>'
                                f'<p><strong>Deadline:</strong> {task[6]}</p>'
                                f'<p><strong>Budget:</strong> ${task[12]}</p>'
                                f'<p><strong>Assigned to: </strong>{assigned_to_name}</p>'
                                f'<div style="display:flex; justify-content:space-between; margin-top:15px;">',
                                unsafe_allow_html=True
                            )
                            
                            # Determine button visibility
                            is_admin = st.session_state.user_role == "Admin"
                            is_project_owner = query_db(
                                "SELECT user_id FROM projects WHERE id=?", 
                                (task[1],), one=True
                            )[0] == st.session_state.user_id
                            is_task_assignee = task[10] == st.session_state.user_id
                            
                            # Edit button
                            if is_admin or is_project_owner or is_task_assignee:
                                if st.button("✏️ Edit", key=f"edit_{task_id}"):
                                    st.session_state.editing_task_id = task_id
                                    st.session_state.editing_task_project = task[1]
                                    st.rerun()
                            
                            # Delete button
                            if is_admin or is_project_owner:
                                if st.button("🗑️ Delete", key=f"delete_{task_id}"):
                                    st.session_state.deleting_task_id = task_id
                                    st.rerun()
                            
                            st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Close the grid containers
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Edit Task Form (shown after all cards if editing)
                    if 'editing_task_id' in st.session_state:
                        task_id = st.session_state.editing_task_id
                        project_id = st.session_state.editing_task_project
                        task = query_db("SELECT * FROM tasks WHERE id=?", (task_id,), one=True)
                        
                        if task:
                            project_owner = query_db(
                                "SELECT user_id FROM projects WHERE id=?",
                                (project_id,), one=True
                            )
                            is_project_owner = (project_owner and project_owner[0] == st.session_state.user_id) or st.session_state.user_role == "Admin"
                            is_task_assignee = task[10] == st.session_state.user_id
                            
                            if is_admin or is_project_owner or is_task_assignee:
                                with st.expander(f"✏️ Editing Task: {task[2]}", expanded=True):
                                    if edit_task_form(task_id, project_id):
                                        del st.session_state.editing_task_id
                                        st.rerun()
                                    elif st.button("Close Without Saving"):
                                        del st.session_state.editing_task_id
                                        st.rerun()

                    # Delete Confirmation (shown after all cards if deleting)
                    if 'deleting_task_id' in st.session_state:
                        task_id = st.session_state.deleting_task_id
                        task = query_db("SELECT * FROM tasks WHERE id=?", (task_id,), one=True)
                        
                        if task:
                            is_admin = st.session_state.user_role == "Admin"
                            is_project_owner = query_db(
                                "SELECT user_id FROM projects WHERE id=?", 
                                (task[1],), one=True
                            )[0] == st.session_state.user_id
                            
                            if is_admin or is_project_owner:
                                with st.container():
                                    st.warning(f"⚠️ Are you sure you want to delete task: {task[2]}?")
                                    st.error("This action cannot be undone and will delete all associated data!")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("✅ Confirm Delete", key=f"confirm_delete_{task_id}", type="primary"):
                                            query_db("DELETE FROM task_dependencies WHERE task_id=? OR depends_on_task_id=?", (task_id, task_id))
                                            query_db("DELETE FROM comments WHERE task_id=?", (task_id,))
                                            query_db("DELETE FROM subtasks WHERE task_id=?", (task_id,))
                                            query_db("DELETE FROM attachments WHERE task_id=?", (task_id,))
                                            query_db("DELETE FROM tasks WHERE id=?", (task_id,))
                                            st.success("Task deleted successfully!")
                                            del st.session_state.deleting_task_id
                                            st.rerun()
                                    with col2:
                                        if st.button("❌ Cancel", key=f"cancel_delete_{task_id}"):
                                            del st.session_state.deleting_task_id
                                            st.rerun()




        # ======= Section Divider =======
        st.markdown("---")
        st.header("📊 Task Analytics")

        tasks_df = display_task_table()

        # Simplified tabs without project filter
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Timeline", "Progress", "Priority Breakdown", 
    "Budget Tracking", "Budget Variance", "Workload", 
    "Subtask Analytics"
        ])

        with tab1:
            st.markdown("""
            <style>
                .stPlotlyChart {
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .stDownloadButton>button {
                    width: 100% !important;
                }
            </style>
            """, unsafe_allow_html=True)

            plot_task_timeline(tasks_df)
        
        with tab2:
            plot_task_progress_over_time(tasks_df)

        with tab3:
            plot_task_priority_distribution(tasks_df)

        with tab4:
            plot_budget_tracking(tasks_df)

        with tab5:
            plot_budget_variance(tasks_df)        

        with tab6:
            plot_assignee_workload(tasks_df)

        with tab7:
            plot_subtask_analytics(tasks_df)

        


    # Notifications Page
    elif page == "Notifications":
        st.markdown("---")
        

        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">🔔 Notifications Center</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)

        

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  
        
        # Initialize session state for viewing task details
        if 'viewing_task_id' not in st.session_state:
            st.session_state.viewing_task_id = None

        # Custom CSS for notifications
        st.markdown("""
        <style>
            .notification-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                margin: 16px 0;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .overdue {
                border-left: 4px solid #ff4d4d;
                background: #fff5f5;
            }
            .upcoming {
                border-left: 4px solid #ffa500;
                background: #fffaf0;
            }
            .notification-header {
                font-weight: bold;
                font-size: 1.1rem;
                margin-bottom: 8px;
                color: #2c3e50;
            }
        </style>
        """, unsafe_allow_html=True)

        # Function to get tasks with proper project name handling
        def get_upcoming_and_overdue_tasks():
            today = datetime.today().date()
            
            if st.session_state.user_role == "Admin":
                tasks = query_db("""
                    SELECT t.*, p.name as project_name 
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.status != 'Completed'
                """)
            else:
                tasks = query_db("""
                    SELECT t.*, p.name as project_name 
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.status != 'Completed'
                    AND (t.assigned_to = ? OR p.user_id = ?)
                """, (st.session_state.user_id, st.session_state.user_id))
            
            overdue_tasks = []
            upcoming_tasks = []

            for task in tasks:
                deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else today
                project_name = task[-1] if task[-1] else "Unassigned Project"
                
                if deadline < today:
                    overdue_tasks.append(task)
                elif (deadline - today).days <= st.session_state.reminder_period:
                    upcoming_tasks.append(task)

            return upcoming_tasks, overdue_tasks

        upcoming_tasks, overdue_tasks = get_upcoming_and_overdue_tasks()

        # Summary Cards
        st.subheader("📊 Notification Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="notification-card" style="background-color: #F5F5F5;">
                <div style="font-size: 0.9rem; color: #666;">Total Notifications</div>
                <div style="font-size: 1.8rem; font-weight: 700;">{len(overdue_tasks) + len(upcoming_tasks)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="notification-card" style="background-color: #FFF5F5;">
                <div style="font-size: 0.9rem; color: #666;">Overdue Tasks</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #D32F2F;">{len(overdue_tasks)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="notification-card" style="background-color: #FFF9E6;">
                <div style="font-size: 0.9rem; color: #666;">Upcoming Deadlines</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #FF8F00;">{len(upcoming_tasks)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Filters Section
        st.markdown("---")
        st.subheader("🔍 Filter Notifications")
        
        with st.expander("Filter Options", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                priority_filter = st.multiselect(
                    "Priority Level",
                    options=["High", "Medium", "Low"],
                    default=["High", "Medium", "Low"],
                    key="priority_filter"
                )
            
            with col2:
                # Handle None project names safely
                project_options = sorted(list(set(
                    [task[-1] if task[-1] else "Unassigned Project" for task in overdue_tasks + upcoming_tasks]
                )))
                project_filter = st.multiselect(
                    "Project",
                    options=project_options,
                    default=project_options,
                    key="project_filter"
                )
            
            with col3:
                min_date = datetime.today().date()
                max_date = min_date + timedelta(days=st.session_state.reminder_period)
                deadline_filter = st.date_input(
                    "Deadline Range",
                    value=[min_date, max_date],
                    key="deadline_filter"
                )

        # Apply filters
        def apply_filters(task_list):
            filtered = []
            for task in task_list:
                priority = task[8] if len(task) > 8 else "Medium"
                project_name = task[-1] if task[-1] else "Unassigned Project"
                deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else datetime.today().date()
                
                if (priority in priority_filter and
                    project_name in project_filter and
                    (len(deadline_filter) == 2 and deadline_filter[0] <= deadline <= deadline_filter[1])):
                    filtered.append(task)
            return filtered

        filtered_overdue = apply_filters(overdue_tasks)
        filtered_upcoming = apply_filters(upcoming_tasks)

        # Notifications Display
        st.markdown("---")
        st.subheader("📨 Your Notifications")

        # Overdue Tasks Section
        with st.expander(f"⚠️ Overdue Tasks ({len(filtered_overdue)})", expanded=True):
            if filtered_overdue:
                for task in filtered_overdue:
                    with st.container():
                        deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else "No deadline"
                        days_overdue = (datetime.today().date() - deadline).days if task[6] else 0
                        project_name = task[-1] if task[-1] else "Unassigned Project"
                        
                        st.markdown(f"""
                        <div class="notification-card overdue">
                            <div class="notification-header">
                                {task[2]}
                            </div>
                            <div style="margin-bottom: 8px;">
                                <strong>Project:</strong> {project_name} | 
                                <strong>Deadline:</strong> {deadline} ({days_overdue} days overdue)
                            </div>
                            <div style="margin-bottom: 8px;">{task[3] or "No description"}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Use Streamlit button instead of HTML button
                        if st.button("View Details", key=f"view_{task[0]}"):
                            st.session_state.viewing_task_id = task[0]
                            st.rerun()
            else:
                st.info("No overdue tasks matching your filters.")

        # Upcoming Tasks Section
        with st.expander(f"🔜 Upcoming Deadlines ({len(filtered_upcoming)})", expanded=True):
            if filtered_upcoming:
                for task in filtered_upcoming:
                    with st.container():
                        deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else "No deadline"
                        days_remaining = (deadline - datetime.today().date()).days if task[6] else 0
                        project_name = task[-1] if task[-1] else "Unassigned Project"
                        
                        st.markdown(f"""
                        <div class="notification-card upcoming">
                            <div class="notification-header">
                                {task[2]}
                            </div>
                            <div style="margin-bottom: 8px;">
                                <strong>Project:</strong> {project_name} | 
                                <strong>Deadline:</strong> {deadline} (in {days_remaining} days)
                            </div>
                            <div style="margin-bottom: 8px;">{task[3] or "No description"}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("View Details", key=f"view_{task[0]}_upcoming"):
                            st.session_state.viewing_task_id = task[0]
                            st.rerun()
            else:
                st.info("No upcoming tasks matching your filters.")

        # Display task details at the BOTTOM of the page if a task is selected
        if st.session_state.viewing_task_id:
            task_id = st.session_state.viewing_task_id
            task = query_db("""
                SELECT t.*, p.name as project_name, u.username as assignee_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                LEFT JOIN users u ON t.assigned_to = u.id
                WHERE t.id = ?
            """, (task_id,), one=True)
            
            if task:
                st.markdown("---")  # Add a divider before the task details
                with st.expander(f"📝 Task Details: {task[2]}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Project:** {task[-2] if task[-2] else 'No project'}")
                        st.write(f"**Title:** {task[2]}")
                        st.write(f"**Status:** {task[4]}")
                    with col2:
                        st.write(f"**Assignee:** {task[-1] if task[-1] else 'Unassigned'}")
                        st.write(f"**Start Date:** {task[11] if task[11] else 'Not set'}")
                        st.write(f"**Deadline:** {task[6]}")
                    
                    st.divider()
                    st.write("**Description:**")
                    st.write(task[3] or "No description available")
                    
                    st.divider()
                    st.write(f"**Time Spent:** {task[7]} hours")
                    
                    if st.button("Close Details"):
                        st.session_state.viewing_task_id = None
                        st.rerun()
            else:
                st.warning("Task not found")
                st.session_state.viewing_task_id = None
                st.rerun()

        # JavaScript to handle button clicks
        components.html("""
        <script>
            window.addEventListener('message', function(event) {
                if (event.data.taskId) {
                    // This will trigger Streamlit to update the viewing_task state
                    window.parent.postMessage({
                        streamlit: {
                            type: 'streamlit:componentMessage',
                            data: {taskId: event.data.taskId}
                        }
                    }, '*');
                }
            });
        </script>
        """, height=0)



    
    # Calendar Page
    elif page == "Calendar":
        st.markdown("---")

        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">📅 Project Calendar</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        show_calendar_page()



   
   
    # Admin Page
    elif page == "Admin":
        st.markdown("---")
        
        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">👤 Admin Dashboard</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)



        
        # Initialize the database to ensure schema is up-to-date
        init_db()
        
        # ======= Quick Overview Section =======
        st.markdown("---")
        st.subheader("📊 User Overview")
        

        # Calculate metrics
        total_users = query_db("SELECT COUNT(*) FROM users")[0][0]
        active_users = query_db("""SELECT COUNT(*) FROM users 
                                WHERE last_login IS NOT NULL 
                                AND last_login != 'Never'
                                AND datetime(last_login) > datetime('now', '-7 days')""")[0][0]
        inactive_users = total_users - active_users
        admins = query_db("SELECT COUNT(*) FROM users WHERE role='Admin'")[0][0]
        
        # Create metric cards with the same style as Dashboard
        metric_cards = [
            {"title": "Total Users", "value": total_users, "color": "#4E8BF5", "icon": "👥"},
            {"title": "Active Users", "value": active_users, "color": "#6BB9F0", "icon": "👥"},
            {"title": "Inactive Users", "value": inactive_users, "color": "#32CD32", "icon": "👥"},
            {"title": "Admins", "value": admins, "color": "#FF4500", "icon": "👥"}
        ]

        # Display metrics in columns with consistent styling
        cols = st.columns(4)
        for i, card in enumerate(metric_cards):
            with cols[i]:
                st.markdown(f"""
                <div style='
                    background-color: #FFFFFF;
                    border-radius: 10px;
                    padding: 1.2rem;
                    border-left: 4px solid {card['color']};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    height: 100%;
                '>
                    <div style='display: flex; align-items: center; margin-bottom: 8px;'>
                        <span style='font-size: 1.5rem; margin-right: 8px;'>{card['icon']}</span>
                        <span style='font-size: 0.9rem; color: #666;'>{card['title']}</span>
                    </div>
                    <p style='font-size: 1.8rem; font-weight: 700; color: #2c3e50; margin: 0;'>{card['value']}</p>
                </div>
                """, unsafe_allow_html=True)



        
        # ======= User Activity Functions =======
        def get_activity_status(last_login):
            if not last_login or last_login == 'Never':
                return "Inactive"
            try:
                last_login_dt = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
                delta = datetime.now() - last_login_dt
                if delta.days == 0:
                    if delta.seconds < 300:  # 5 minutes
                        return "Active now"
                    return "Active today"
                elif delta.days == 1:
                    return "Yesterday"
                elif delta.days < 7:
                    return "This week"
                else:
                    return "Inactive"
            except:
                return "Inactive"

        # ======= Fetch User Data =======
        try:
            users = query_db("""
                SELECT id, username, role, email, phone, first_name, last_name, 
                    company, job_title, department, 
                    CASE WHEN last_login IS NULL THEN 'Never' ELSE last_login END as last_login, 
                    COALESCE(login_count, 0) as login_count, 
                    COALESCE(is_active, 1) as is_active
                FROM users
                ORDER BY username
            """)
        except sqlite3.OperationalError as e:
            st.error("Database schema needs update. Attempting to fix...")
            init_db()
            users = query_db("""
                SELECT id, username, role, email, phone, first_name, last_name, 
                    company, job_title, department, 
                    CASE WHEN last_login IS NULL THEN 'Never' ELSE last_login END as last_login, 
                    COALESCE(login_count, 0) as login_count, 
                    COALESCE(is_active, 1) as is_active
                FROM users
                ORDER BY username
            """)

        if users:
            # Convert to DataFrame
            users_df = pd.DataFrame(users, columns=[
                "ID", "Username", "Role", "Email", "Phone", "First Name", "Last Name",
                "Company", "Job Title", "Department", "Last Login", "Login Count", "Is Active"
            ])
            
            # Add activity status column
            users_df["Activity"] = users_df["Last Login"].apply(get_activity_status)
            
            
            # Display user table
            st.markdown("---")
            st.subheader("👥 User Activity")

            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                role_filter = st.multiselect(
                    "Filter by Role",
                    options=users_df["Role"].unique(),
                    default=users_df["Role"].unique()
                )
            with col2:
                activity_filter = st.multiselect(
                    "Filter by Activity",
                    options=["Active now", "Active today", "Yesterday", "This week", "Inactive"],
                    default=["Active now", "Active today", "Yesterday", "This week", "Inactive"]
                )
            with col3:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["Active", "Inactive"],
                    default=["Active", "Inactive"]
                )

            # Apply filters
            filtered_users = users_df[
                (users_df["Role"].isin(role_filter)) &
                (users_df["Activity"].isin(activity_filter)) &
                (users_df["Is Active"].isin([1 if s == "Active" else 0 for s in status_filter]))
            ]

            
            
            # When displaying the user table:
            st.dataframe(
                users_df,
                column_config={
                    "Last Login": st.column_config.DatetimeColumn(
                        "Last Active",
                        format="YYYY-MM-DD HH:mm",
                    )
                }
            )



        
        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)


        # ======= User Management Section ======= 
        st.subheader("👥 User Management")
        # st.markdown("---")
        
        # Add New User Form
        st.markdown("---")
        st.subheader("➕ Add New User")

        with st.expander("➕ Add New User", expanded=False):
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_username = st.text_input("Username*")
                    new_first_name = st.text_input("First Name")
                    new_last_name = st.text_input("Last Name")
                    new_company = st.text_input("Company")
                with col2:
                    new_role = st.selectbox("Role*", ["User", "Admin"])
                    new_job_title = st.text_input("Job Title")
                    new_department = st.text_input("Department")
                    new_email = st.text_input("Email")
                    new_phone = st.text_input("Phone")
                
                new_password = st.text_input("Password*", type="password")

                if st.form_submit_button("Add User"):
                    if not new_username or not new_password:
                        st.error("Username and password are required fields")
                    elif query_db("SELECT * FROM users WHERE username=?", (new_username,), one=True):
                        st.error("Username already exists.")
                    else:
                        query_db("""
                            INSERT INTO users (username, password, role, email, phone, 
                                            first_name, last_name, company, job_title, department)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            new_username,
                            hash_password(new_password),
                            new_role,
                            new_email,
                            new_phone,
                            new_first_name,
                            new_last_name,
                            new_company,
                            new_job_title,
                            new_department
                        ))
                        st.success("User added successfully!")
                        st.rerun()



        # Divider with spacing
        # st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  

        
        # ======= Filtered User Table =======
        st.markdown("---")
        st.subheader("👥Edit User")

        # Fetch all users
        users = query_db("SELECT id, username, role, email, phone, first_name, last_name, company, job_title, department FROM users")

        if not users:
            st.info("No users found in the database.")
        else:
            # Convert to DataFrame
            users_df = pd.DataFrame(users, columns=["ID", "Username", "Role", "Email", "Phone", "First Name", "Last Name", "Company", "Job Title", "Department"])
            
            # Create filter widgets - matching project analytics style
            with st.expander("🔍 Filter Users", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    username_options = ['All Usernames'] + sorted(users_df['Username'].unique().tolist())
                    selected_username = st.selectbox(
                        "Filter by Username", 
                        username_options,
                        key="user_username_filter"
                    )
                
                with col2:
                    role_options = ['All Roles'] + sorted(users_df['Role'].unique().tolist())
                    selected_role = st.selectbox(
                        "Filter by Role",
                        role_options,
                        key="user_role_filter"
                    )
                    
                with col3:
                    first_name_options = ['All First Names'] + sorted(users_df['First Name'].dropna().unique().tolist())
                    selected_first_name = st.selectbox(
                        "Filter by First Name",
                        first_name_options,
                        key="user_first_name_filter"
                    )
                    
                with col4:
                    last_name_options = ['All Last Names'] + sorted(users_df['Last Name'].dropna().unique().tolist())
                    selected_last_name = st.selectbox(
                        "Filter by Last Name",
                        last_name_options,
                        key="user_last_name_filter"
                    )

            # Apply filters
            filtered_df = users_df.copy()
            
            if selected_username != 'All Usernames':
                filtered_df = filtered_df[filtered_df['Username'] == selected_username]
            
            if selected_role != 'All Roles':
                filtered_df = filtered_df[filtered_df['Role'] == selected_role]
                
            if selected_first_name != 'All First Names':
                filtered_df = filtered_df[filtered_df['First Name'] == selected_first_name]
                
            if selected_last_name != 'All Last Names':
                filtered_df = filtered_df[filtered_df['Last Name'] == selected_last_name]

            # Add selection column to filtered DataFrame
            filtered_df.insert(0, "Select", False)
            
            # Display editable dataframe with checkboxes
            edited_df = st.data_editor(
                filtered_df,
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select"),
                    "ID": None,  # Hide ID column
                    "Role": st.column_config.SelectboxColumn(
                        "Role",
                        options=["Admin", "User"],
                        required=True
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="user_editor"
            )
            
            # Get selected rows from the filtered DataFrame
            selected_users = edited_df[edited_df["Select"]]
            
            # Action buttons for selected users
            if not selected_users.empty:
                st.markdown("---")
                st.subheader("Selected User Actions")
                
                col1, col2, col3 = st.columns([1,1,3])
                
                with col1:
                    if st.button("✏️ Edit Selected", key="edit_selected"):
                        st.session_state.editing_users = selected_users["ID"].tolist()
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete Selected", type="primary", key="delete_selected"):
                        st.session_state.deleting_users = selected_users["ID"].tolist()
                        st.rerun()
            
            # Delete confirmation
            if 'deleting_users' in st.session_state and st.session_state.deleting_users:
                st.markdown("---")
                st.subheader("Confirm Deletion")
                
                users_to_delete = []
                for user_id in st.session_state.deleting_users:
                    user = query_db("SELECT username FROM users WHERE id=?", (user_id,), one=True)
                    if user:
                        users_to_delete.append(user[0])
                
                st.warning(f"⚠️ You are about to delete {len(users_to_delete)} user(s):")
                st.write(", ".join(users_to_delete))
                st.error("This action cannot be undone! All associated data will be permanently deleted.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm Deletion", type="primary"):
                        for user_id in st.session_state.deleting_users:
                            try:
                                query_db("DELETE FROM users WHERE id=?", (user_id,))
                            except Exception as e:
                                st.error(f"Error deleting user ID {user_id}: {str(e)}")
                        st.success(f"Successfully deleted {len(users_to_delete)} user(s)")
                        del st.session_state.deleting_users
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel"):
                        del st.session_state.deleting_users
                        st.rerun()
           

            # Add this section to handle editing selected users
            if 'editing_users' in st.session_state and st.session_state.editing_users:
                st.markdown("---")
                st.subheader("✏️ Edit Selected Users")
                
                # Get the selected users' data
                selected_users_data = []
                for user_id in st.session_state.editing_users:
                    user = query_db(
                        "SELECT id, username, role, email, phone, first_name, last_name, company, job_title, department FROM users WHERE id=?",
                        (user_id,), one=True
                    )
                    if user:
                        selected_users_data.append(user)
                
                if selected_users_data:
                    # Create a form for editing
                    with st.form("edit_users_form"):
                        edited_users = []
                        
                        for user in selected_users_data:
                            user_id, username, role, email, phone, first_name, last_name, company, job_title, department = user
                            
                            st.markdown(f"### Editing User: {username}")
                            
                            cols = st.columns(2)
                            with cols[0]:
                                new_first_name = st.text_input("First Name", value=first_name, key=f"first_name_{user_id}")
                                new_last_name = st.text_input("Last Name", value=last_name, key=f"last_name_{user_id}")
                                new_company = st.text_input("Company", value=company, key=f"company_{user_id}")
                            with cols[1]:
                                new_role = st.selectbox(
                                    "Role", 
                                    ["User", "Admin"],
                                    index=0 if role == "User" else 1,
                                    key=f"role_{user_id}"
                                )
                                new_job_title = st.text_input("Job Title", value=job_title, key=f"job_title_{user_id}")
                                new_department = st.text_input("Department", value=department, key=f"department_{user_id}")
                            
                            new_email = st.text_input("Email", value=email, key=f"email_{user_id}")
                            new_phone = st.text_input("Phone", value=phone, key=f"phone_{user_id}")
                            
                            edited_users.append({
                                "id": user_id,
                                "first_name": new_first_name,
                                "last_name": new_last_name,
                                "company": new_company,
                                "role": new_role,
                                "job_title": new_job_title,
                                "department": new_department,
                                "email": new_email,
                                "phone": new_phone
                            })
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save Changes"):
                                try:
                                    for user in edited_users:
                                        query_db("""
                                            UPDATE users SET
                                                first_name=?, last_name=?, company=?,
                                                role=?, job_title=?, department=?,
                                                email=?, phone=?
                                            WHERE id=?
                                        """, (
                                            user["first_name"], user["last_name"], user["company"],
                                            user["role"], user["job_title"], user["department"],
                                            user["email"], user["phone"],
                                            user["id"]
                                        ))
                                    st.success("User updates saved successfully!")
                                    del st.session_state.editing_users
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating users: {str(e)}")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state.editing_users
                                st.rerun()
       

       # Add export functionality for the user data:
        with st.expander("📤 Export User Data"):
            csv = users_df.to_csv(index=False)
            st.download_button(
            label="Download CSV",
            data=csv,
            file_name="user_data.csv",
            mime="text/csv"
        )



        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # ======= Project Management Section =======
        st.subheader("📂 Project Management")

        # ======= Summary Statistics ======= 
        st.markdown("---")
        st.subheader("📊 Project Overview")
        

        # Calculate metrics
        total_users = len(query_db("SELECT * FROM users"))
        total_projects = len(query_db("SELECT * FROM projects"))
        active_projects = len(query_db("SELECT * FROM projects WHERE end_date >= ?", (datetime.today().date(),)))
        overdue_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE p.end_date < ? 
            AND EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """, (datetime.today().date(),)))
        completed_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE NOT EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """))
        
        # Create metric cards with the same style as Dashboard
        metric_cards = [
            {"title": "Completed Projects", "value": completed_projects, "color": "#07f7f7", "icon": "✅"},
            {"title": "Total Projects", "value": total_projects, "color": "#6BB9F0", "icon": "📂"},
            {"title": "Active Projects", "value": active_projects, "color": "#32CD32", "icon": "🟢"},
            {"title": "Overdue Projects", "value": overdue_projects, "color": "#FF4500", "icon": "⚠️"}
        ]

        # Display metrics in columns with consistent styling
        cols = st.columns(4)
        for i, card in enumerate(metric_cards):
            with cols[i]:
                st.markdown(f"""
                <div style='
                    background-color: #FFFFFF;
                    border-radius: 10px;
                    padding: 1.2rem;
                    border-left: 4px solid {card['color']};
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    height: 100%;
                '>
                    <div style='display: flex; align-items: center; margin-bottom: 8px;'>
                        <span style='font-size: 1.5rem; margin-right: 8px;'>{card['icon']}</span>
                        <span style='font-size: 0.9rem; color: #666;'>{card['title']}</span>
                    </div>
                    <p style='font-size: 1.8rem; font-weight: 700; color: #2c3e50; margin: 0;'>{card['value']}</p>
                </div>
                """, unsafe_allow_html=True)

        
        # Divider with spacing
        # st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)



        # ======= Summary Statistics ======= 
        st.markdown("---")
        st.subheader("🔍 Filter Projects")

        # First, fetch all project data with proper status calculations
        projects_data = query_db("""
            SELECT 
                p.id, 
                p.user_id as owner_id, 
                p.name, 
                p.description, 
                p.start_date as planned_start_date,
                p.end_date as planned_deadline,
                p.budget,
                ROUND(COALESCE(SUM(t.actual_cost), 0)) as actual_cost,
                ROUND(p.budget - COALESCE(SUM(t.actual_cost), 0)) as budget_variance,
                COUNT(t.id) as task_count,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                u.username as owner_name,
                (ROUND(SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(t.id), 0), 2)) as completion_pct,
                julianday(p.end_date) - julianday(p.start_date) as planned_duration,
                CASE
                    WHEN MIN(t.actual_start_date) IS NULL OR MAX(t.actual_deadline) IS NULL THEN NULL
                    ELSE julianday(MAX(t.actual_deadline)) - julianday(MIN(t.actual_start_date))
                END as actual_duration,
                MIN(t.actual_start_date) as actual_start_date,  
                MAX(t.actual_deadline) as actual_deadline,      
                CASE 
                    WHEN COUNT(t.id) = 0 THEN 0
                    WHEN SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) = COUNT(t.id) THEN 1
                    ELSE 0
                END as is_completed
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            LEFT JOIN users u ON p.user_id = u.id
            GROUP BY p.id
        """)

        # Convert to DataFrame
        project_df = pd.DataFrame(projects_data, columns=[
            "ID", "Owner ID", "Project", "Description", "Planned Start Date", "Planned Deadline",
            "Budget", "Actual Cost", "Budget Variance", "Total Tasks",
            "Completed Tasks", "Owner", "Completion %",
            "Planned Duration (days)", "Actual Duration (days)",
            "Actual Start Date", "Actual Deadline", "is_completed"
        ])

        # Ensure date columns are proper datetime objects
        date_cols = ["Planned Start Date", "Planned Deadline", "Actual Start Date", "Actual Deadline"]
        for col in date_cols:
            project_df[col] = pd.to_datetime(project_df[col])

        # Create filter widgets in an expandable section
        with st.expander("🔍 Filter Projects", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Project name filter (multi-select)
                project_names = ["All Projects"] + sorted(project_df["Project"].unique().tolist())
                selected_projects = st.multiselect(
                    "Filter by Project",
                    options=project_names,
                    default=["All Projects"],
                    key="project_filter"
                )
                
            with col2:
                # Owner filter
                owner_options = ["All Owners"] + sorted(project_df["Owner"].dropna().unique().tolist())
                selected_owner = st.selectbox(
                    "Filter by Owner",
                    options=owner_options,
                    key="owner_filter"
                )
                
            with col3:
                # Status filter (based on completion)
                status_options = ["All", "Completed", "In Progress", "Not Started"]
                selected_status = st.selectbox(
                    "Filter by Status",
                    options=status_options,
                    key="status_filter"
                )

            col4, col5 = st.columns(2)
            with col4:
                # Date range filter
                min_date = project_df["Planned Start Date"].min().date()
                max_date = project_df["Planned Deadline"].max().date()
                date_range = st.date_input(
                    "Date Range",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    key="date_filter"
                )
                
            with col5:
                # Budget variance filter
                budget_filter = st.slider(
                    "Minimum Budget Variance ($)",
                    min_value=int(project_df["Budget Variance"].min()),
                    max_value=int(project_df["Budget Variance"].max()),
                    value=int(project_df["Budget Variance"].min()),
                    key="budget_filter"
                )

        # Apply filters
        filtered_df = project_df.copy()

        # Project name filter
        if "All Projects" not in selected_projects and selected_projects:
            filtered_df = filtered_df[filtered_df["Project"].isin(selected_projects)]

        # Owner filter
        if selected_owner != "All Owners":
            filtered_df = filtered_df[filtered_df["Owner"] == selected_owner]

        # Status filter
        if selected_status == "Completed":
            filtered_df = filtered_df[filtered_df["is_completed"] == 1]
        elif selected_status == "In Progress":
            filtered_df = filtered_df[(filtered_df["is_completed"] == 0) & (filtered_df["Total Tasks"] > 0)]
        elif selected_status == "Not Started":
            filtered_df = filtered_df[filtered_df["Total Tasks"] == 0]

        # Date range filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df["Planned Start Date"].dt.date >= start_date) &
                (filtered_df["Planned Deadline"].dt.date <= end_date)
            ]

        # Budget variance filter
        filtered_df = filtered_df[filtered_df["Budget Variance"] >= budget_filter]

        # Display the filtered table
        st.subheader("📊 Project Analytics")

        # Format the display DataFrame (without affecting filtering)
        display_df = filtered_df.copy()
        display_df["Planned Start Date"] = display_df["Planned Start Date"].dt.strftime('%Y-%m-%d')
        display_df["Planned Deadline"] = display_df["Planned Deadline"].dt.strftime('%Y-%m-%d')
        display_df["Actual Start Date"] = display_df["Actual Start Date"].dt.strftime('%Y-%m-%d')
        display_df["Actual Deadline"] = display_df["Actual Deadline"].dt.strftime('%Y-%m-%d')

        # Show metrics summary
        st.metric("Projects Shown", len(filtered_df), delta=f"{len(filtered_df)}/{len(project_df)}")

        # Display the table
        st.dataframe(
            display_df[[
                "Project", "Owner", "Planned Start Date", "Planned Deadline",
                "Actual Start Date", "Actual Deadline", "Total Tasks",
                "Completed Tasks", "Completion %", "Budget", "Actual Cost",
                "Budget Variance"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Completion %": st.column_config.ProgressColumn(
                    "Completion %",
                    help="Project completion percentage",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Budget": st.column_config.NumberColumn(
                    "Budget ($)",
                    format="$%.2f",
                ),
                "Actual Cost": st.column_config.NumberColumn(
                    "Actual Cost ($)",
                    format="$%.2f",
                ),
                "Budget Variance": st.column_config.NumberColumn(
                    "Budget Variance ($)",
                    format="$%.2f",
                )
            }
        )



        # Add export functionality for project analytics data:
        with st.expander("📤 Export Project Analytics Data"):
            csv = project_df.to_csv(index=False)
            st.download_button(
            label="Download CSV",
            data=csv,
            file_name="project_analytics_data.csv",
            mime="text/csv"
        )

        # Divider with spacing
        # st.markdown("---")
        # st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

                 
        
        # Edit and Delete Projects
        st.markdown("---")
        st.subheader("📂 Edit or Delete Projects")
       
        
        # Create dropdown for project selection
        project_options = ["Select a project..."] + [f"{project[2]} (ID: {project[0]})" for project in projects_data]
        selected_project = st.selectbox("Select Project to Edit/Delete", project_options, key="project_select")
        
        if selected_project != "Select a project...":
            selected_project_id = int(selected_project.split("ID: ")[1].rstrip(")"))
            project_to_edit = next((project for project in projects_data if project[0] == selected_project_id), None)
            
            if project_to_edit:
                # Initialize session state variables
                if 'confirm_delete_project' not in st.session_state:
                    st.session_state.confirm_delete_project = False
                if 'editing_project' not in st.session_state:
                    st.session_state.editing_project = True
                
                # Display edit form unless in delete confirmation or edit mode is False
                if not st.session_state.confirm_delete_project and st.session_state.editing_project:
                    st.write(f"### Editing: {project_to_edit[2]}")
                    
                    with st.form(f"edit_project_{project_to_edit[0]}"):
                        # Define all form variables at the start
                        new_name = st.text_input("Project Name*", 
                                            value=project_to_edit[2],
                                            help="Project name must be unique (case-insensitive)")
                        
                        new_description = st.text_area("Description", 
                                                    value=project_to_edit[3] if len(project_to_edit) > 3 else "")
                        
                        # Get user options as a dictionary {id: username}
                        users = query_db("SELECT id, username FROM users")
                        user_options = {user[0]: user[1] for user in users}
                        
                        # Project Owner Dropdown (only for admins)
                        if st.session_state.user_role == "Admin":
                            current_owner_result = query_db(
                                "SELECT username FROM users WHERE id=?", 
                                (project_to_edit[1],), 
                                one=True
                            )
                            current_owner = current_owner_result[0] if current_owner_result else "Unknown"
                            
                            # Create list of usernames for the selectbox
                            usernames = list(user_options.values())
                            new_owner = st.selectbox(
                                "Project Owner*",
                                options=usernames,
                                index=usernames.index(current_owner) if current_owner in usernames else 0
                            )
                            new_owner_id = [uid for uid, uname in user_options.items() if uname == new_owner][0]
                        else:
                            new_owner_id = project_to_edit[1]
                            owner_name_result = query_db(
                                "SELECT username FROM users WHERE id=?", 
                                (project_to_edit[1],), 
                                one=True
                            )
                            owner_name = owner_name_result[0] if owner_name_result else "Unknown"
                            st.write(f"**Project Owner:** {owner_name}")
                        
                        # Project Dates
                        col1, col2 = st.columns(2)
                        with col1:
                            new_start_date = st.date_input(
                                "Start Date*",
                                value=datetime.strptime(project_to_edit[4], "%Y-%m-%d").date() if len(project_to_edit) > 4 else datetime.now().date()
                            )
                        with col2:
                            new_end_date = st.date_input(
                                "Due Date*",
                                value=datetime.strptime(project_to_edit[5], "%Y-%m-%d").date() if len(project_to_edit) > 5 else datetime.now().date()
                            )
                        
                        # Project Budget
                        budget_value = float(project_to_edit[6]) if len(project_to_edit) > 6 and project_to_edit[6] is not None else 0.0
                        new_budget = st.number_input(
                            "Project Budget", 
                            min_value=0.0, 
                            value=budget_value
                        )
                        
                        # Form buttons column layout
                        col1, col2 = st.columns(2)
                        with col1:
                            submit_button = st.form_submit_button("💾 Save Changes")
                        with col2:
                            cancel_button = st.form_submit_button("❌ Cancel")
                        
                        # Handle form submission
                        if submit_button:
                            # Validate inputs
                            if not new_name.strip():
                                st.error("Project name is required")
                            elif new_end_date < new_start_date:
                                st.error("Due date must be on or after the start date")
                            else:
                                # Check for duplicate name (excluding current project)
                                existing_project = query_db(
                                    "SELECT 1 FROM projects WHERE LOWER(name) = LOWER(?) AND id != ?", 
                                    (new_name.strip(), project_to_edit[0]), 
                                    one=True
                                )
                                
                                if existing_project:
                                    st.error(f"A project with name '{new_name.strip()}' already exists")
                                else:
                                    query_db("""
                                        UPDATE projects 
                                        SET name=?, description=?, user_id=?, 
                                            start_date=?, end_date=?, budget=?
                                        WHERE id=?
                                    """, (
                                        new_name.strip(), 
                                        new_description, 
                                        new_owner_id,
                                        new_start_date, 
                                        new_end_date, 
                                        new_budget, 
                                        project_to_edit[0]
                                    ))
                                    st.toast("✅ Changes updated successfully!", icon="✅")
                                    st.session_state.editing_project = False
                                    st.rerun()
                        
                        if cancel_button:
                            st.session_state.editing_project = False
                            st.rerun()
                
                # Delete confirmation section (outside the form)
                if st.session_state.confirm_delete_project:
                    st.warning(f"⚠️ Are you sure you want to delete project '{project_to_edit[2]}'?")
                    st.error("This will delete ALL associated tasks and cannot be undone!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm Delete", key=f"confirm_del_proj_{project_to_edit[0]}"):
                            delete_project(project_to_edit[0])
                            st.toast("🗑️ Project deleted successfully!", icon="🗑️")
                            st.session_state.confirm_delete_project = False
                            st.session_state.editing_project = False
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_del_proj_{project_to_edit[0]}"):
                            st.session_state.confirm_delete_project = False
                            st.rerun()
                else:
                    # Show edit button if not currently editing
                    if not st.session_state.editing_project:
                        if st.button("✏️ Edit Project", key=f"edit_{project_to_edit[0]}"):
                            st.session_state.editing_project = True
                            st.rerun()
                    
                    # Delete button (only show when not editing)
                    if not st.session_state.editing_project:
                        if st.button("🗑️ Delete Project", key=f"init_del_proj_{project_to_edit[0]}", type="primary"):
                            st.session_state.confirm_delete_project = True
                            st.rerun()

        # # Divider with spacing
        # st.markdown("---")
        # st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
       

        # ======= System Settings Section =======
        st.markdown("---")
        st.subheader("⚙️ System Settings")

        with st.expander("Customize System Settings", expanded=False):
            with st.form("system_settings_form"):
                default_reminder_period = st.number_input("Default Reminder Period (days)", min_value=1, value=7)
                enable_email_notifications = st.checkbox("Enable Email Notifications", value=True)

                submitted = st.form_submit_button("Save Settings")
                if submitted:
                    st.session_state.reminder_period = default_reminder_period
                    st.success("System settings updated successfully!")
                    st.rerun()

        # Add another divider at the bottom for clean separation
        st.markdown("---")



    # Profile Page
    elif page == "Profile":
        st.markdown("---")
        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">👤 User Profile</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)
        
        
        st.markdown("---")
        
        
        # Display user profile information
        display_user_profile(st.session_state.user_id)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  
        
        # Success notification state
        if 'profile_update_success' not in st.session_state:
            st.session_state.profile_update_success = False
        if 'password_change_success' not in st.session_state:
            st.session_state.password_change_success = False
        
        # Display success notifications
        if st.session_state.profile_update_success:
            st.success("✅ Profile updated successfully!")
            st.session_state.profile_update_success = False
        
        if st.session_state.password_change_success:
            st.success("✅ Password changed successfully!")
            st.session_state.password_change_success = False
        
        # Main profile layout
        col1, col2 = st.columns([1, 2], gap="large")
        
        with col1:
            # Profile Picture Section
            st.subheader("Profile Picture")
            user = query_db("SELECT profile_picture FROM users WHERE id=?", (st.session_state.user_id,), one=True)
            
            if user and user[0]:
                st.image(user[0], width=150)
            else:
                st.image("https://via.placeholder.com/150", width=150)
            
            uploaded_file = st.file_uploader("Upload new photo", type=["jpg", "jpeg", "png"])
            
        with col2:
            # Profile Information Section
            st.subheader("Personal Information")
            user = query_db("""
                SELECT username, first_name, last_name, email, phone, 
                    company, job_title, department, profile_picture
                FROM users WHERE id=?
            """, (st.session_state.user_id,), one=True)
            
            with st.form("profile_form"):
                cols = st.columns(2)
                with cols[0]:
                    first_name = st.text_input("First Name", value=user[1] if user[1] else "")
                    email = st.text_input("Email", value=user[3] if user[3] else "")
                    company = st.text_input("Company", value=user[5] if user[5] else "")
                with cols[1]:
                    last_name = st.text_input("Last Name", value=user[2] if user[2] else "")
                    phone = st.text_input("Phone", value=user[4] if user[4] else "")
                    job_title = st.text_input("Job Title", value=user[6] if user[6] else "")
                
                department = st.text_input("Department", value=user[7] if user[7] else "")
                
                if st.form_submit_button("Update Profile"):
                    # Handle profile picture upload
                    profile_pic = user[8]  # Keep existing if no new upload
                    if uploaded_file is not None:
                        profile_pic = uploaded_file.read()
                    
                    query_db("""
                        UPDATE users SET
                            first_name=?, last_name=?, email=?,
                            phone=?, company=?, job_title=?,
                            department=?, profile_picture=?
                        WHERE id=?
                    """, (
                        first_name, last_name, email,
                        phone, company, job_title,
                        department, profile_pic,
                        st.session_state.user_id
                    ))
                    st.session_state.profile_update_success = True
                    st.rerun()
        
        # Change Password Section
        st.divider()
        st.subheader("Change Password")
        
        with st.form("password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                # Verify current password
                user = query_db("SELECT password FROM users WHERE id=?", (st.session_state.user_id,), one=True)
                if not verify_password(user[0], current_password):
                    st.error("Current password is incorrect")
                elif new_password != confirm_password:
                    st.error("New passwords don't match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    query_db("UPDATE users SET password=? WHERE id=?", 
                            (hash_password(new_password), st.session_state.user_id))
                    st.session_state.password_change_success = True
                    st.rerun()

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
        

        # ======= Activity Summary Section =======
        st.subheader("📊 Activity Summary")

        # Custom CSS for the cards (similar to Notifications page)
        st.markdown("""
        <style>
            .metric-card {
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .metric-title {
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 8px;
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #2c3e50;
                margin: 0;
            }
        </style>
        """, unsafe_allow_html=True)

        # Get activity data
        tasks_assigned = len(get_tasks())
        tasks_completed = len([task for task in get_tasks() if task[4] == "Completed"])
        projects_involved = len(get_projects())

        # Create cards in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #4E8BF5;">
                <div class="metric-title">Tasks Assigned</div>
                <div class="metric-value">{tasks_assigned}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #32CD32;">
                <div class="metric-title">Tasks Completed</div>
                <div class="metric-value">{tasks_completed}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #FFA500;">
                <div class="metric-title">Projects Involved</div>
                <div class="metric-value">{projects_involved}</div>
            </div>
            """, unsafe_allow_html=True)

        # Completion rate visualization
        if tasks_assigned > 0:
            completion_rate = (tasks_completed / tasks_assigned) * 100
            remaining_rate = 100 - completion_rate
            
            st.markdown("---")
            st.write("### Task Completion Progress")
            
            # Create a completion card similar to notification cards
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #6BB9F0; margin-top: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span class="metric-title">Overall Completion Rate</span>
                    <span style="font-weight: 600; color: #2c3e50;">{completion_rate:.1f}%</span>
                </div>
                <div style="height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden;">
                    <div style="width: {completion_rate}%; height: 100%; background: #4CAF50;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                    <span style="font-size: 0.8rem; color: #666;">Completed: {tasks_completed}</span>
                    <span style="font-size: 0.8rem; color: #666;">Pending: {tasks_assigned - tasks_completed}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


            
            # Divider
            st.markdown("---")
            st.header("📊 Your Task Analytics")

            
            # Fetch the user's tasks with proper error handling
            try:
                # Get tasks assigned to the current user
                tasks = query_db("""
                    SELECT 
                        t.id, t.title, t.status, t.priority, t.deadline, 
                        t.time_spent, p.name as project_name,
                        t.start_date, t.actual_start_date,
                        t.deadline as planned_deadline, t.actual_deadline,
                        t.budget, t.actual_cost
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.id
                    WHERE t.assigned_to = ?
                """, (st.session_state.user_id,))
                
                if not tasks:
                    st.info("No tasks found for your account.")
                else:
                    # Create DataFrame with proper column names
                    tasks_df = pd.DataFrame(tasks, columns=[
                        "ID", "Title", "Status", "Priority", "Deadline", 
                        "Time Spent", "Project",
                        "Planned Start", "Actual Start",
                        "Planned Deadline", "Actual Deadline",
                        "Budget", "Actual Cost"
                    ])
                    
                    # Convert date columns
                    date_cols = ["Deadline", "Planned Start", "Actual Start", "Planned Deadline", "Actual Deadline"]
                    for col in date_cols:
                        tasks_df[col] = pd.to_datetime(tasks_df[col])
                    
                    # Calculate additional metrics
                    today = pd.Timestamp.today()
                    tasks_df["Days Until Deadline"] = (tasks_df["Deadline"] - today).dt.days
                    tasks_df["Duration Variance"] = (tasks_df["Actual Deadline"] - tasks_df["Planned Deadline"]).dt.days
                    tasks_df["Budget Variance"] = tasks_df["Budget"] - tasks_df["Actual Cost"]
                    
                    # Create tabs for different visualizations
                    tab1, tab2, tab3 = st.tabs(["Productivity", "Time Management", "Performance"])
                    
                    with tab1:

                        # --- NEW: Project Task Status Bar Chart ---
                        st.subheader("📋 Tasks by Project and Status")
                        
                        # Group by Project and Status
                        project_status_counts = tasks_df.groupby(['Project', 'Status']).size().unstack(fill_value=0)
                        
                        # Create stacked bar chart
                        fig = px.bar(
                            project_status_counts,
                            x=project_status_counts.index,
                            y=project_status_counts.columns,
                            title="Your Tasks by Project and Status",
                            labels={'value': 'Number of Tasks', 'index': 'Project'},
                            color_discrete_map={
                                'Pending': '#FFA500',  # Orange
                                'In Progress': '#1E90FF',  # DodgerBlue
                                'Completed': '#32CD32',  # LimeGreen
                                'Overdue': '#FF4500'  # OrangeRed
                            }
                        )
                        
                        # Improve layout
                        fig.update_layout(
                            barmode='stack',
                            xaxis_title="Project",
                            yaxis_title="Number of Tasks",
                            legend_title="Task Status",
                            hovermode="x unified"
                        )
                        
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)


                        st.subheader("🔄 Task Completion Rate")
                        
                        # Weekly completion rate
                        completed_tasks = tasks_df[tasks_df["Status"] == "Completed"]
                        if not completed_tasks.empty:
                            weekly_completion = completed_tasks.groupby(
                                pd.Grouper(key="Actual Deadline", freq="W-MON")
                            ).size().reset_index(name="Tasks Completed")
                            
                            fig = px.line(
                                weekly_completion,
                                x="Actual Deadline",
                                y="Tasks Completed",
                                title="Your Weekly Task Completion",
                                markers=True
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No completed tasks to show completion rate.")
                        
                        # Status distribution
                        st.subheader("📊 Current Task Status")
                        status_counts = tasks_df["Status"].value_counts().reset_index()
                        fig = px.pie(
                            status_counts,
                            names="Status",
                            values="count",
                            title="Your Task Status Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        st.subheader("⏱️ Time Management")

                        # Risk metric
                        st.subheader("⚡ Risk Matrix - Priority vs Days Overdue")
                        tasks_df['Days_Overdue'] = (pd.to_datetime('today') - 
                                                    pd.to_datetime(tasks_df['Deadline'])).dt.days
                        fig = px.scatter(
                            tasks_df,
                            x='Days_Overdue',
                            y='Priority',
                            color='Project',
                            size='Budget',
                            title='Task Risk Assessment',
                            labels={'Days_Overdue': 'Days Overdue'}
                        )
                        st.plotly_chart(fig, use_container_width=True)   
                        
                        # Duration variance
                        if "Actual Deadline" in tasks_df.columns and "Planned Deadline" in tasks_df.columns:
                            fig = px.scatter(
                                tasks_df,
                                x="Planned Deadline",
                                y="Duration Variance",
                                color="Project",
                                title="Planned vs Actual Duration Variance",
                                hover_data=["Title", "Project"]
                            )
                            fig.add_hline(y=0, line_dash="dash", line_color="red")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Time spent distribution
                        st.subheader("⏳ Time Spent Analysis")
                        fig = px.box(
                            tasks_df,
                            x="Project",
                            y="Time Spent",
                            color="Priority",
                            title="Time Spent by Project and Priority"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab3:
                        st.subheader("📈 Budget Performance")
                        
                        # Budget variance
                        if "Budget Variance" in tasks_df.columns:
                            fig = px.bar(
                                tasks_df,
                                x="Project",
                                y="Budget Variance",
                                color="Priority",
                                title="Your Budget Variance by Project",
                                labels={"Budget Variance": "Budget Variance ($)"}
                            )
                            fig.add_hline(y=0, line_dash="dash", line_color="green")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Efficiency metric
                        st.subheader("⚡ Your Efficiency")
                        efficiency_df = tasks_df.groupby("Project").agg({
                            "Time Spent": "sum",
                            "Budget Variance": "mean"
                        }).reset_index()
                        
                        fig = px.scatter(
                            efficiency_df,
                            x="Time Spent",
                            y="Budget Variance",
                            size="Time Spent",
                            color="Project",
                            title="Time Investment vs Budget Performance",
                            labels={
                                "Time Spent": "Total Hours Spent",
                                "Budget Variance": "Average Budget Variance ($)"
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)


            except Exception as e:
                st.error(f"Error loading task data: {str(e)}")
                st.info("Please try refreshing the page or contact support if the problem persists.")


        # Final divider at bottom
        st.markdown("---")    

 

    # Documentation Page
    elif page == "Documentation":
        st.markdown("---")

        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
 
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">📚 Knowledge Center</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;">Comprehensive guides and resources for all app features</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Introduction
        st.markdown("""
        <div style="background-color: #f9f7ff; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
            <h3 style="color: #6e48aa; margin-top: 0;">Welcome To The Project Management App Documentation</h3>
            <p>This documentation provides detailed information about all features and functionality. 
            Expand the sections below to access guides tailored to your needs.</p>
        </div>
        """, unsafe_allow_html=True)         

        st.markdown("---")
        # st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
        

        # Collapsible Sections
        with st.expander("🚀 Getting Started", expanded=True):
            st.markdown("""
            ### 1. **Account Creation**
            - **New Users**: Register via the login page with your email and password
            - **First-Time Setup**: Complete your profile after registration
            
            ### 2. **Initial Navigation**
            - **Dashboard**: Your central hub for project overviews
            - **Projects**: Create and manage your projects
            - **Tasks**: View and update individual tasks
            
            ### 3. **Quick Tips**
            - Use the sidebar to navigate between features
            - Hover over buttons for tooltips
            - Click on any card to see detailed information
            """)
            
            st.image("https://via.placeholder.com/800x300?text=Getting+Started+Screenshot", 
                    caption="Getting Started Overview", use_container_width=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        with st.expander("📂 Projects Guide"):
            st.markdown("""
            ### Project Management
            
            #### Creating Projects
            1. Navigate to the Projects page
            2. Click "Add New Project"
            3. Fill in project details:
            - Name (required)
            - Description
            - Start/End Dates
            - Budget (optional)
            
            #### Managing Projects
            - **View Projects**: See all projects in card view or list format
            - **Edit Projects**: Click the edit button on any project card
            - **Delete Projects**: Remove projects (admin-only feature)
            
            #### Best Practices
            - Set clear project names and descriptions
            - Establish realistic timelines
            - Assign team members early
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image("https://via.placeholder.com/400x250?text=Project+Creation", 
                        caption="Creating a New Project", use_container_width=True)
            with col2:
                st.image("https://via.placeholder.com/400x250?text=Project+View", 
                        caption="Project Management View", use_container_width=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        with st.expander("✅ Tasks Guide"):
            st.markdown("""
            ### Task Management
            
            #### Creating Tasks
            1. Select a project from the dropdown
            2. Click "Add New Task"
            3. Provide task details:
            - Title (required)
            - Detailed description
            - Priority level
            - Deadline
            - Assignee
            
            #### Task Features
            - **Status Tracking**: Update task progress (Pending/In Progress/Completed)
            - **Priority Levels**: Visual indicators for task urgency
            - **Overdue Alerts**: Automatic highlighting of late tasks
            
            #### Productivity Tips
            - Break large tasks into subtasks
            - Use priorities effectively
            - Regularly update task statuses
            """)


            st.markdown("""
            ### Subtask Management
            
            #### Creating Subtasks
            1. Select a task from the task list
            2. Click "Add Subtask"
            3. Provide subtask details:
            - Title (required)
            - Detailed description (optional)
            - Deadline (optional, inherited from parent task if not set)
            - Assignee
            
            #### Subtask Features
            - **Hierarchical View**: Subtasks appear nested under their parent task
            - **Status Tracking**: Track subtask progress independently
            - **Progress Roll-up**:  Parent task progress reflects subtask completion
            
            #### Productivity Tips
            - Use subtasks to break complex tasks into smaller, manageable steps
            - Assign subtasks to different team members for parallel progress
            - Keep subtask deadlines aligned with the parent task timeline
            """)

            
            st.image("https://via.placeholder.com/800x300?text=Task+Management+Screenshot", 
                    caption="Task Management Interface", use_container_width=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)




        # Workspace Guide
        with st.expander("🖥️ Workspace Guide"):
            st.markdown("""
            ### Workspace Overview
            
            #### Key Features
            - **Task Management**: Manage tasks in List, Kanban, or Gantt views
            - **Task Progress**: Monitor completion rates with metrics and pie charts
            - **Team Management**: TView and manage project members
            
            #### Sections Explained
            1. **Select Workspace**
            - Choose a project from the dropdown to access its workspace
            - The list includes all projects you have access to, with project owners highlighted
            - Only admins and owners can modify project settings           
            
            2. **Tabs Overview**
                        
            a. 📋 Tasks
            - Manage tasks in List, Kanban, or Gantt views
            - Create, edit, and track progress with deadlines, priorities, and assignments
            - Owners and assignees can update task statuses

            b. 📋 Subtasks
            - Break tasks into smaller actionable items
            - Set individual deadlines and assignees for each subtask
            - Track subtask status independently from the main task
            - View subtasks nested under their parent task for clarity                                                
         
            c. 📂 Files
            - Upload, share, and organize project files (PDF, DOCX, etc.)
            - Files can be linked to specific tasks or the overall project
            - Download or delete files with appropriate permissions
                        
            d. 💬 Discussions
            - Start topic-based conversations with threaded replies
            - Archive resolved discussions to keep the workspace clutter-free
            - Search by keywords to find past messages

            e. 📅 Timeline
            - Visualize task deadlines and dependencies in an interactive Gantt chart
            - The "Today" marker helps track progress against schedules

            f. 📊 Progress
            - Monitor completion rates with metrics and pie charts
            - Automatically updates based on task status (e.g., "Completed" vs. "Pending")
                              
            g. 👥 Team
            - View and manage project members
            - Owners/admins can add or remove users                           
            - Roles and contact details are displayed for coordination
                        
            #### Export Options
            - Download any chart as PNG
            - Export all data as CSV
            - Print reports directly from the dashboard
            """)
            
            st.image("https://via.placeholder.com/800x400?text=Dashboard+Screenshot", 
                    caption="Dashboard Overview", use_container_width=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        with st.expander("🔔 Notifications Guide"):
            st.markdown("""
            ### Notification System
            
            #### Alert Types
            - **Overdue Tasks**: Highlighted in red with warning icons
            - **Upcoming Deadlines**: Shown with amber indicators
            - **Status Changes**: Notifications when tasks are updated
            
            #### Management Features
            - **Custom Reminders**: Set notification preferences
            - **Filter Options**: View by project or priority
            - **Quick Actions**: Mark as complete directly from alerts
            
            #### Best Practices
            - Review notifications daily
            - Set up email reminders for critical tasks
            - Use the snooze feature for temporary delays
            """)
            
            st.image("https://via.placeholder.com/600x300?text=Notifications+Screenshot", 
                    caption="Notifications Interface", use_container_width=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        with st.expander("👤 Profile Guide"):
            st.markdown("""
            ### Profile Management
            
            #### Personal Information
            - Update your contact details
            - Upload a profile picture
            - Change password
            
            #### Preferences
            - Set notification preferences
            - Choose default views
            - Configure display settings
            
            #### Security
            - Two-factor authentication
            - Login history
            - Connected devices
            """)
            
            st.image("https://via.placeholder.com/600x300?text=Profile+Settings+Screenshot", 
                    caption="Profile Management", use_container_width=True)

        # Divider with extra spacing before admin section
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

        if st.session_state.user_role == "Admin":
            with st.expander("👑 Admin Guide", expanded=False):
                st.markdown("""
                ### Administrator Tools
                
                #### User Management
                - Create/edit user accounts
                - Assign roles and permissions
                - Reset passwords
                
                #### System Configuration
                - Configure application settings
                - Set up organization defaults
                - Manage integrations
                
                #### Data Administration
                - Backup and restore data
                - Audit logs
                - System health monitoring
                """)
                
                st.image("https://via.placeholder.com/600x300?text=Admin+Panel+Screenshot", 
                        caption="Admin Dashboard", use_container_width=True)

            # Divider with spacing
            st.markdown("---")
            st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        # Footer with contact information
        st.markdown("""
        <div style="text-align:center;color:#666;font-size:14px;margin-top:50px;">
            <p>Need additional help? Contact our support team at support@projectapp.com</p>
            <p>© 2023 Project Management App. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)

        # Final divider
        st.markdown("---")








    # Workspace Page
    elif page == "Workspace":
            st.markdown("---")

            # Custom CSS for enhanced styling
            st.markdown("""
            <style>
                .doc-header {
                    background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                    color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    margin-bottom: 2rem;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
            </style>
            """, unsafe_allow_html=True)


            # Header Section with Gradient
            st.markdown("""
            <div class="doc-header">
                <h1 style="color: white; margin-bottom: 0.5rem;">🖥️ Project Workspace</h1>
                <p style="font-size: 1.1rem; opacity: 0.9;"></p>
            </div>
            """, unsafe_allow_html=True)
    

            
            workspace_page() 
    