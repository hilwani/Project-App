import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
from main_page import query_db, priority_colors, status_colors

def show_task_page():
    # Page Header
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
    <div class="doc-header">
        <h1 style="color: white; margin-bottom: 0.5rem;">✅ Task Management</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Task Creation Section
    st.markdown("---")
    st.header("📂 Create New Tasks")
    
    with st.expander("➕ Create New Task", expanded=False):
        with st.form(key="create_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Task Title*", placeholder="Enter task name")
                start_date = st.date_input("Start Date*")
            with col2:
                priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
                deadline = st.date_input("Deadline*")
            
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title.strip():
                    st.error("Task title is required")
                elif deadline < start_date:
                    st.error("Deadline must be after start date")
                else:
                    # Save to database
                    query_db("""
                        INSERT INTO tasks (title, description, start_date, deadline, priority)
                        VALUES (?, ?, ?, ?, ?)
                    """, (title, description, start_date, deadline, priority))
                    st.success("Task created successfully!")
                    st.rerun()

    # Task List Section
    st.markdown("---")
    st.header("📋 Your Tasks")
    
    tasks = query_db("SELECT * FROM tasks")
    if tasks:
        df = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Status", 
                                         "Created", "Deadline", "Time Spent", 
                                         "Priority", "Project ID", "Assignee"])
        st.dataframe(df)
    else:
        st.warning("No tasks found")

    # Task Analytics
    st.markdown("---")
    st.header("📊 Task Analytics")
    
    if tasks:
        tab1, tab2 = st.tabs(["Status Distribution", "Priority Breakdown"])
        
        with tab1:
            status_counts = pd.DataFrame(tasks)[3].value_counts()
            fig = px.pie(status_counts, names=status_counts.index, 
                         title="Task Status Distribution")
            st.plotly_chart(fig)
            
        with tab2:
            priority_counts = pd.DataFrame(tasks)[7].value_counts()
            fig = px.bar(priority_counts, 
                         color=priority_counts.index,
                         color_discrete_map=priority_colors,
                         title="Task Priority Distribution")
            st.plotly_chart(fig)
    else:
        st.warning("No data available for analytics")

# Helper functions for task page
def edit_task_form(task_id):
    """Reusable form for editing tasks"""
    task = query_db("SELECT * FROM tasks WHERE id=?", (task_id,), one=True)
    
    with st.form(key=f"edit_task_{task_id}"):
        st.subheader(f"Edit Task: {task[1]}")
        
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Title", value=task[1])
            new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], 
                                    index=["Pending", "In Progress", "Completed"].index(task[3]))
        with col2:
            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], 
                                      index=["High", "Medium", "Low"].index(task[7]))
            new_deadline = st.date_input("Deadline", 
                                       value=datetime.strptime(task[5], "%Y-%m-%d").date())
        
        new_desc = st.text_area("Description", value=task[2])
        
        if st.form_submit_button("Save Changes"):
            query_db("""
                UPDATE tasks 
                SET title=?, description=?, status=?, priority=?, deadline=?
                WHERE id=?
            """, (new_title, new_desc, new_status, new_priority, new_deadline, task_id))
            st.success("Task updated!")
            return True
        if st.form_submit_button("Cancel"):
            return False
    return False