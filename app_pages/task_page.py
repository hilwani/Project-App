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


