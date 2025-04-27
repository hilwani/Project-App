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
                                f'<p><strong>Description:</strong></p>'
                                f'<div style="background:#f8f9fa; padding:10px; border-radius:4px; margin:5px 0;">'
                                f'{task[3] or "No description provided"}'
                                f'</div>'
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Timeline", "Progress", "Priority Breakdown", "Budget Tracking", "Budget Variance", "Workload"])

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


