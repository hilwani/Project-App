import streamlit as st 
import sqlite3 
import datetime 
import time
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import hashlib
from components.drag_and_drop import drag_and_drop
from streamlit_calendar import calendar
from calendar_page import show_calendar_page
from workspace_page import workspace_page
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

# Page Config (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(page_title="Project Management App", layout="wide")


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
   
   
    # Check if the is_archived column exists, and if not, add it
    # c.execute("PRAGMA table_info(discussion_topics)")
    # columns = c.fetchall()
    # column_names = [column[1] for column in columns]
    
    # if 'is_archieved' not in column_names:
    #     c.execute('ALTER TABLE discussion_topics ADD COLUMN is_archived INTEGER DEFAULT 0') 



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
# if 'page_navigation' not in st.session_state:
#     st.session_state.page_navigation = None

# if 'username' not in st.session_state:
#     st.session_state.username = None

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
def edit_task_form(task_id, project_id=None):
    """Reusable edit task form with all sections (time tracking, dates, budget)"""
    # Get task details with all budget-related fields
    task = query_db("""
        SELECT 
            t.id, t.project_id, t.title, t.description, t.status, 
            t.created_at, t.deadline, t.time_spent, t.priority, 
            t.recurrence, t.assigned_to, t.start_date, 
            t.actual_start_date, t.actual_deadline, 
            t.budget as original_budget,
            t.actual_cost, t.budget_variance,
            p.name as project_name, 
            u.username as assignee_name 
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        LEFT JOIN users u ON t.assigned_to = u.id
        WHERE t.id = ?
    """, (task_id,), one=True)
    
    if not task:
        st.error("Task not found")
        return False

    with st.form(key=f"edit_task_{task_id}_form"):
        st.subheader(f"✏️ Edit Task: {task[2]}")
        
        # Main columns layout
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Task Title*", value=task[2])
            description = st.text_area("Description", value=task[3] or "")
            status = st.selectbox(
                "Status*",
                options=["Pending", "In Progress", "Completed", "On Hold"],
                index=["Pending", "In Progress", "Completed", "On Hold"].index(task[4]) 
                if task[4] in ["Pending", "In Progress", "Completed", "On Hold"] else 0
            )
            
        with col2:
            priority = st.selectbox(
                "Priority*",
                options=["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(task[8]) 
                if task[8] in ["High", "Medium", "Low"] else 1
            )
            
            users = query_db("SELECT id, username FROM users ORDER BY username")
            current_assignee = task[-1] if task[-1] else "Unassigned"
            assignee_options = ["Unassigned"] + [user[1] for user in users]
            assignee = st.selectbox(
                "Assignee",
                options=assignee_options,
                index=assignee_options.index(current_assignee) 
                if current_assignee in assignee_options else 0
            )

        # Time Tracking Section
        st.subheader("Time Tracking", divider="gray")
        time_col1, time_col2 = st.columns(2)
        
        with time_col1:
            planned_time = st.number_input(
                "Planned Time Spent (Hours)*",
                min_value=0.0,
                value=float(task[7]) if task[7] is not None and str(task[7]).replace('.', '', 1).isdigit() else 0.0,
                step=0.5
            )
            
        with time_col2:
            actual_time = st.number_input(
                "Actual Time Spent (Hours)",
                min_value=0.0,
                value=float(task[16]) if len(task) > 16 and task[16] is not None and str(task[16]).replace('.', '', 1).isdigit() else 0.0,
                step=0.5
            )

        # Dates Section - Restored Actual Dates placeholders
        st.subheader("Dates", divider="gray")
        date_col1, date_col2 = st.columns(2)
        
        with date_col1:
            # Planned Start Date
            try:
                start_date_value = datetime.strptime(str(task[11]), "%Y-%m-%d").date() if task[11] else datetime.now().date()
            except:
                start_date_value = datetime.now().date()
            start_date = st.date_input("Planned Start Date*", value=start_date_value)
            
            # Actual Start Date (always shown)
            try:
                actual_start_value = datetime.strptime(str(task[12]), "%Y-%m-%d").date() if task[12] else None
            except:
                actual_start_value = None
            actual_start = st.date_input("Actual Start Date", value=actual_start_value)
            
        with date_col2:
            # Planned Deadline
            try:
                deadline_value = datetime.strptime(str(task[6]), "%Y-%m-%d").date() if task[6] else datetime.now().date() + timedelta(days=7)
            except:
                deadline_value = datetime.now().date() + timedelta(days=7)
            deadline = st.date_input("Planned Deadline*", value=deadline_value)
            
            # Actual Deadline (always shown)
            try:
                actual_deadline_value = datetime.strptime(str(task[13]), "%Y-%m-%d").date() if task[13] else None
            except:
                actual_deadline_value = None
            actual_deadline = st.date_input("Actual Deadline", value=actual_deadline_value)

        # Budget Section
        st.subheader("Budget", divider="gray")
        budget_col1, budget_col2 = st.columns(2)
        
        original_budget = task[14]  # From our modified query
        try:
            original_budget_value = float(original_budget) if original_budget is not None else None
            formatted_original_budget = f"${original_budget_value:,.2f}" if original_budget_value is not None else "Not set"
        except ValueError:
            formatted_original_budget = "Invalid value"
            original_budget_value = 0.0

        try:
            actual_cost_value = float(task[15]) if task[15] is not None and str(task[15]).replace('.', '', 1).isdigit() else 0.0
        except:
            actual_cost_value = 0.0

        with budget_col1:
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <strong>Original Planned Budget:</strong> {formatted_original_budget}
            </div>
            """, unsafe_allow_html=True)
            
            budget = st.number_input(
                "Update Planned Budget ($)",
                min_value=0.0,
                value=original_budget_value if original_budget_value is not None else 0.0,
                step=0.01,
                key=f"budget_{task_id}"
            )
            
        with budget_col2:
            st.write(f"**Current Actual Cost:** ${actual_cost_value:,.2f}" if actual_cost_value else "**Current Actual Cost:** Not set")
            actual_cost = st.number_input(
                "Update Actual Cost ($)",
                min_value=0.0,
                value=actual_cost_value,
                step=0.01,
                key=f"actual_cost_{task_id}"
            )

        # Form actions
        st.divider()
        col1, col2, _ = st.columns([1,1,2])
        
        submitted = st.form_submit_button("💾 Save Changes")
        if submitted:
            assignee_id = None
            if assignee != "Unassigned":
                assignee_result = query_db(
                    "SELECT id FROM users WHERE username = ?", 
                    (assignee,), one=True
                )
                assignee_id = assignee_result[0] if assignee_result else None
            
            query_db("""
                UPDATE tasks SET
                    title = ?, description = ?, status = ?,
                    priority = ?, assigned_to = ?, time_spent = ?,
                    actual_time_spent = ?,
                    start_date = ?, deadline = ?,
                    actual_start_date = ?, actual_deadline = ?,
                    budget = ?, actual_cost = ?
                WHERE id = ?
            """, (
                title, description, status,
                priority, assignee_id, planned_time,
                actual_time,
                start_date, deadline,
                actual_start, actual_deadline,
                budget, actual_cost,
                task_id 
            ))
            
            st.success("Task updated successfully!")
            return True
        
        if st.form_submit_button("❌ Cancel"):
            return False
    
    return False




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
        
        # Create a nice welcome container
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: #E1F0FF;
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 5px solid #4E8BF5;
                margin-bottom: 1.5rem;
            ">
                <h3 style="color: #2c3e50; margin-top: 0;">🎉 Welcome back, {welcome_name}!</h3>
                <p style="margin-bottom: 0.5rem;">You're logged in as <strong>{st.session_state.user_role}</strong>.</p>
                <p style="margin-bottom: 0;">Let's get productive! 🚀</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to dismiss the message
            if st.button("Got it!", key="dismiss_welcome"):
                st.session_state.show_welcome = False
                st.rerun()

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
        """
        Create a bar chart showing the distribution of tasks by priority.
        """
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Count tasks by priority
        priority_counts = tasks_df["Priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]
        
        # Create bar chart
        fig = px.bar(
            priority_counts,
            x="Priority",
            y="Count",
            title="Task Priority Distribution",
            labels={"Priority": "Task Priority", "Count": "Number of Tasks"},
            color="Priority",
            color_discrete_map={
                "High": "#FF0000",  # Red
                "Medium": "#FFA500",  # Orange
                "Low": "#32CD32",  # Green
            },
        )
        st.plotly_chart(fig)


    # Helper function for task progress over time (Line Chart)
    def plot_task_progress_over_time(tasks_df):
        """Create a line chart showing the number of tasks completed over time."""
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Filter completed tasks
        completed_tasks = tasks_df[tasks_df["Status"] == "Completed"]
        
        if completed_tasks.empty:
            st.warning("No completed tasks found.")
            return
        
        # Convert "Planned Start Date" to datetime (using new column name)
        completed_tasks["Planned Start Date"] = pd.to_datetime(completed_tasks["Planned Start Date"]).dt.date
        
        # Group by date and count completed tasks (using new column name)
        progress_data = completed_tasks.groupby("Planned Start Date").size().reset_index(name="Completed Tasks")
        
        # Create line chart
        fig = px.line(
            progress_data,
            x="Planned Start Date",
            y="Completed Tasks",
            title="Task Progress Over Time",
            labels={"Planned Start Date": "Date", "Completed Tasks": "Number of Tasks Completed"},
            markers=True,
        )
        
        st.plotly_chart(fig)


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
        """
        Create a bar chart showing budget, actual cost, and budget variance for tasks.
        """
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Prepare data for the chart
        budget_data = tasks_df[["Task", "Budget", "Actual Cost", "Budget Variance"]].melt(id_vars="Task", var_name="Category", value_name="Amount")
        
        # Create bar chart
        fig = px.bar(
            budget_data,
            x="Task",
            y="Amount",
            color="Category",
            title="Budget Tracking",
            labels={"Task": "Task", "Amount": "Amount ($)", "Category": "Category"},
            barmode="group",
        )
        st.plotly_chart(fig)


    # Helper function to visualize task timeline (Gantt chart)
    def plot_task_timeline(tasks_df):
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Prepare data for Gantt chart - use the new column names
        timeline_df = tasks_df.copy()
        timeline_df['Start'] = pd.to_datetime(tasks_df['Planned Start Date'])
        timeline_df['End'] = pd.to_datetime(tasks_df['Planned Deadline'])
        timeline_df['Completion'] = (timeline_df['Status'] == 'Completed').astype(int)
        
        # Add actual dates if they exist
        if 'Actual Start Date' in tasks_df.columns:
            timeline_df['Actual Start'] = pd.to_datetime(tasks_df['Actual Start Date'])
        if 'Actual Deadline' in tasks_df.columns:
            timeline_df['Actual End'] = pd.to_datetime(tasks_df['Actual Deadline'])
        
        fig = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Status",
            color_discrete_map=status_colors,
            title="Task Timeline with Completion Status",
            hover_data=["Priority", "Assignee", "Project Owner"]
        )
        
        # Add actual dates to hover data if they exist
        if 'Actual Start' in timeline_df.columns and 'Actual End' in timeline_df.columns:
            fig.update_traces(
                customdata=timeline_df[['Actual Start', 'Actual End']],
                hovertemplate=(
                    "<b>%{y}</b><br>" +
                    "Planned: %{x|%b %d, %Y} - %{x_end|%b %d, %Y}<br>" +
                    "Actual: %{customdata[0]|%b %d, %Y} - %{customdata[1]|%b %d, %Y}<br>" +
                    "Status: %{marker.color}<br>" +
                    "Priority: %{customdata[2]}<br>" +
                    "Project: %{customdata[3]}<extra></extra>"
                )
            )
        
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)


    #helper function to visualize assignee workload (Sunburst chart)
    def plot_assignee_workload(tasks_df):
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Prepare hierarchical data
        workload_df = tasks_df.groupby(['Assignee', 'Status']).size().reset_index(name='Count')
        
        fig = px.sunburst(
            workload_df,
            path=['Assignee', 'Status'],
            values='Count',
            color='Status',
            color_discrete_map=status_colors,
            title="Assignee Workload by Task Status"
        )
        st.plotly_chart(fig, use_container_width=True)


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

        # Display task details if a task is selected
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



    

