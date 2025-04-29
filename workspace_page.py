from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st 
import sqlite3
import time
 
# Database connection function 
def get_db_connection():
    conn = sqlite3.connect('project_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database query function
def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args) 
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def sort_tasks(tasks):
    """Sort tasks by planned start date (ascending) then by task title (ascending)"""
    def get_sort_key(task):
        # Handle different task tuple structures from different queries
        if len(task) >= 5:  # For Timeline tab query
            start_date = task[1]  # start_date is at index 1
            title = task[0]       # title is at index 0
        elif len(task) >= 9:  # For Gantt Chart query
            start_date = task[2]  # start_date is at index 2
            title = task[1]       # title is at index 1
        else:
            start_date = None
            title = task[1] if len(task) > 1 else ""
            
        try:
            date_key = pd.to_datetime(start_date) if start_date else pd.to_datetime('today')
        except:
            date_key = pd.to_datetime('today')
            
        return (date_key, title)
    
    return sorted(tasks, key=get_sort_key)

 
#
def edit_task_in_workspace(task_id, project_id=None):
    """Reusable edit task form for workspace page with fully functional subtask integration"""
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
        st.error("Task not found in workspace")
        return False

    # Initialize session state variables
    if 'subtask_actions' not in st.session_state:
        st.session_state.subtask_actions = {
            'confirm_delete': None,
            'show_subtask_form': False,
            'editing_subtask': None
        }

    with st.form(key=f"workspace_edit_task_{task_id}_form"):
        st.subheader(f"✏️ Edit Task: {task[2]}")
        
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
                value=float(task[17]) if len(task) > 17 and task[17] is not None and str(task[17]).replace('.', '', 1).isdigit() else 0.0,
                step=0.5
            )

        # Dates Section
        st.subheader("Dates", divider="gray")
        date_col1, date_col2 = st.columns(2)
        
        with date_col1:
            try:
                start_date_value = datetime.strptime(str(task[11]), "%Y-%m-%d").date() if task[11] else datetime.now().date()
            except:
                start_date_value = datetime.now().date()
            start_date = st.date_input("Planned Start Date*", value=start_date_value)
            
            try:
                actual_start_value = datetime.strptime(str(task[12]), "%Y-%m-%d").date() if task[12] else None
            except:
                actual_start_value = None
            actual_start = st.date_input("Actual Start Date", value=actual_start_value)
            
        with date_col2:
            try:
                deadline_value = datetime.strptime(str(task[6]), "%Y-%m-%d").date() if task[6] else datetime.now().date() + timedelta(days=7)
            except:
                deadline_value = datetime.now().date() + timedelta(days=7)
            deadline = st.date_input("Planned Deadline*", value=deadline_value)
            
            try:
                actual_deadline_value = datetime.strptime(str(task[13]), "%Y-%m-%d").date() if task[13] else None
            except:
                actual_deadline_value = None
            actual_deadline = st.date_input("Actual Deadline", value=actual_deadline_value)

        # Budget Section
        st.subheader("Budget", divider="gray")
        budget_col1, budget_col2 = st.columns(2)
        
        original_budget = task[14]
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
                key=f"workspace_budget_{task_id}"
            )
            
        with budget_col2:
            st.write(f"**Current Actual Cost:** ${actual_cost_value:,.2f}" if actual_cost_value else "**Current Actual Cost:** Not set")
            actual_cost = st.number_input(
                "Update Actual Cost ($)",
                min_value=0.0,
                value=actual_cost_value,
                step=0.01,
                key=f"workspace_actual_cost_{task_id}"
            )

        # Form actions
        # Form actions
        st.divider()
        col1, col2, _ = st.columns([1,1,2])

        submitted = st.form_submit_button("💾 Save Changes")
        cancel_pressed = st.form_submit_button("❌ Cancel")

        if cancel_pressed:
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            st.rerun()

        if submitted:
            # Get assignee ID from username
            assignee_id = None
            if assignee != "Unassigned":
                assignee_user = query_db("SELECT id FROM users WHERE username=?", (assignee,), one=True)
                assignee_id = assignee_user[0] if assignee_user else None
            
            # Convert dates to strings for database
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            deadline_str = deadline.strftime("%Y-%m-%d") if deadline else None
            actual_start_str = actual_start.strftime("%Y-%m-%d") if actual_start else None
            actual_deadline_str = actual_deadline.strftime("%Y-%m-%d") if actual_deadline else None
            
            # Calculate budget variance
            budget_variance = float(budget) - float(actual_cost) if budget and actual_cost else None
            
            # Update the task in database - including ALL fields
            query_db("""
                UPDATE tasks SET
                    title=?, description=?, status=?, 
                    priority=?, assigned_to=?, time_spent=?,
                    start_date=?, deadline=?, actual_start_date=?,
                    actual_deadline=?, budget=?, actual_cost=?,
                    budget_variance=?, actual_time_spent=?
                WHERE id=?
            """, (
                title, description, status,
                priority, assignee_id, planned_time,
                start_date_str, deadline_str, actual_start_str,
                actual_deadline_str, budget, actual_cost,
                budget_variance, actual_time, task_id
            ))
            
            st.success("Task updated successfully in workspace!")
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            st.rerun()
    
    # Subtask Section (outside the main form)
    # Subtask Section
    st.markdown("---")
    st.subheader("Subtasks Management")
    
    # Get all subtasks
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
        
        # Display subtasks table
        subtasks_df = pd.DataFrame(subtasks, columns=[
            "ID", "Title", "Description", "Status", "Start Date", "Deadline",
            "Priority", "Assigned To ID", "Budget", "Time Spent", "Assigned To"
        ])
        
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
        
        # Subtask management
        # Subtask management
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
                    with st.form(key=f"edit_subtask_{subtask_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            subtask_title = st.text_input("Title", value=subtask[1], key=f"title_{subtask_id}")
                            subtask_description = st.text_area(
                                "Description", 
                                value=subtask[2] or "",
                                placeholder="Enter detailed description...",
                                key=f"desc_{subtask_id}"
                            )
                            
                            status_col, priority_col = st.columns(2)
                            with status_col:
                                subtask_status = st.selectbox(
                                    "Status", 
                                    ["Pending", "In Progress", "Completed"], 
                                    index=["Pending", "In Progress", "Completed"].index(subtask[3]),
                                    key=f"status_{subtask_id}"
                                )
                            with priority_col:
                                subtask_priority = st.selectbox(
                                    "Priority", 
                                    ["High", "Medium", "Low"], 
                                    index=["High", "Medium", "Low"].index(subtask[6]),
                                    key=f"priority_{subtask_id}"
                                )
                        
                        with col2:
                            date_col1, date_col2 = st.columns(2)
                            with date_col1:
                                subtask_start_date = st.date_input(
                                    "Start Date", 
                                    value=datetime.strptime(subtask[4], "%Y-%m-%d").date() if subtask[4] else start_date,
                                    key=f"start_{subtask_id}"
                                )
                            with date_col2:
                                subtask_deadline = st.date_input(
                                    "Deadline", 
                                    value=datetime.strptime(subtask[5], "%Y-%m-%d").date() if subtask[5] else deadline,
                                    key=f"deadline_{subtask_id}"
                                )
                            
                            subtask_budget = st.number_input(
                                "Budget ($)", 
                                min_value=0.0, 
                                value=float(subtask[8] or 0), 
                                step=0.01,
                                placeholder="Enter budget amount...",
                                key=f"budget_{subtask_id}"
                            )
                            
                            subtask_time_spent = st.number_input(
                                "Time Spent (hours)", 
                                min_value=0.0, 
                                value=float(subtask[9] or 0),
                                step=0.5,
                                placeholder="Enter hours worked...",
                                key=f"time_{subtask_id}"
                            )
                            
                            team_members = query_db("SELECT id, username FROM users ORDER BY username")
                            assignee_options = ["Unassigned"] + [member[1] for member in team_members]
                            
                            current_assignee = "Unassigned"
                            if subtask[7]:  # If there's an assigned_to value
                                current_assignee = subtask[10] if subtask[10] else "Unassigned"
                            
                            subtask_assigned_to = st.selectbox(
                                "Assign To", 
                                assignee_options,
                                index=assignee_options.index(current_assignee) if current_assignee in assignee_options else 0,
                                key=f"assignee_{subtask_id}"
                            )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update Subtask"):
                                try:
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
                                        priority=?, assigned_to=?, budget=?, time_spent=?
                                        WHERE id=?
                                    """, (
                                        subtask_title, subtask_description, subtask_status, 
                                        subtask_start_date, subtask_deadline, subtask_priority, 
                                        assigned_to_id, subtask_budget, subtask_time_spent, subtask_id
                                    ))
                                    st.success("Subtask updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating subtask: {str(e)}")
                        
                        with col2:
                            if st.form_submit_button("Delete Subtask"):
                                st.session_state.subtask_actions['confirm_delete'] = subtask_id


    
    # Delete confirmation (outside any form)
    if st.session_state.subtask_actions['confirm_delete']:
        st.warning("⚠️ Are you sure you want to delete this subtask? This action cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete", key="confirm_delete_subtask"):
                query_db("DELETE FROM subtasks WHERE id=?", (st.session_state.subtask_actions['confirm_delete'],))
                st.success("Subtask deleted successfully!")
                st.session_state.subtask_actions['confirm_delete'] = None
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="cancel_delete_subtask"):
                st.session_state.subtask_actions['confirm_delete'] = None
                st.rerun()
    
    # Create New Subtask Section
    # Add new subtask section
    st.markdown("---")
    st.subheader("Create New Subtask")
    
    if st.button("➕ Create New Subtask", key="toggle_subtask_form"):
        st.session_state.subtask_actions['show_subtask_form'] = not st.session_state.subtask_actions['show_subtask_form']
    
    if st.session_state.subtask_actions['show_subtask_form']:
        with st.form(key="new_subtask_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_subtask_title = st.text_input("Title*", placeholder="Enter subtask name", key="new_subtask_title")
                new_subtask_description = st.text_area("Description", placeholder="Enter detailed description...", key="new_subtask_desc")
                
                status_col, priority_col = st.columns(2)
                with status_col:
                    new_subtask_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], key="new_subtask_status")
                with priority_col:
                    new_subtask_priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="new_subtask_priority")
            
            with col2:
                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    new_subtask_start_date = st.date_input("Start Date", value=start_date, key="new_subtask_start")
                with date_col2:
                    new_subtask_deadline = st.date_input("Deadline", value=deadline, key="new_subtask_deadline")
                
                new_subtask_budget = st.number_input("Budget ($)", 
                                                   min_value=0.0, 
                                                   value=0.0, 
                                                   step=0.01, 
                                                   key="new_subtask_budget",
                                                   placeholder="Enter budget amount...")
                
                new_subtask_time_spent = st.number_input("Time Spent (hours)", 
                                                       min_value=0.0, 
                                                       value=0.0, 
                                                       step=0.5,
                                                       key="new_subtask_time",
                                                       placeholder="Enter hours worked...")
                
                team_members = query_db("SELECT id, username FROM users ORDER BY username")
                new_subtask_assigned_to = st.selectbox(
                    "Assign To", 
                    ["Unassigned"] + [member[1] for member in team_members],
                    key="new_subtask_assignee"
                )
            
            col1, col2 = st.columns(2)
            with col1:
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
                             priority, assigned_to, budget, time_spent)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            task_id, new_subtask_title.strip(), new_subtask_description, 
                            new_subtask_status, new_subtask_start_date, new_subtask_deadline,
                            new_subtask_priority, assigned_to_id, new_subtask_budget, new_subtask_time_spent
                        ))
                        st.success("Subtask created successfully!")
                        st.session_state.subtask_actions['show_subtask_form'] = False
                        st.rerun()
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.subtask_actions['show_subtask_form'] = False
                    st.rerun()
        
#
def render_task_form(edit_mode=False, project_id=None):
    """Task form for creation (updated to accept project_id)"""
    form_key = f"task_form_{'edit' if edit_mode else 'create'}"
    
    with st.form(key=form_key):
        if edit_mode:
            st.subheader("✏️ Edit Task")
            task_data = query_db("""
                SELECT title, description, priority, start_date, deadline, status,
                    budget, actual_cost, time_spent, assigned_to,
                    actual_start_date, actual_deadline
                FROM tasks WHERE id=?
            """, (st.session_state.editing_task_id,), one=True)
        else:
            st.subheader("🆕 Create New Task")
            task_data = [None] * 11

        def parse_date(date_val):
            if not date_val or isinstance(date_val, int):
                return None
            try:
                return datetime.strptime(str(date_val), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        new_title = st.text_input("Task Title *", value=task_data[0] if edit_mode else "")
        new_desc = st.text_area("Description", value=task_data[1] if edit_mode else "")

        st.markdown("### 📅 Planning")
        col1, col2 = st.columns(2)
        with col1:
            new_priority = st.selectbox(
                "Priority *",
                ["Low", "Medium", "High"],
                index=["Low", "Medium", "High"].index(task_data[2]) if edit_mode and task_data[2] else 1
            )
            start_date = st.date_input(
                "Start Date",
                value=parse_date(task_data[3]) if edit_mode else None
            )
            # Changed from planned_cost to budget for consistency
            budget = st.number_input(
                "Planned Budget ($)",
                min_value=0.0,
                value=float(task_data[6]) if edit_mode and task_data[6] else 0.0,
                
            )
            
        with col2:
            new_status = st.selectbox(
                "Status *",
                ["Pending", "In Progress", "Completed", "On Hold"],
                index=["Pending", "In Progress", "Completed", "On Hold"].index(task_data[5]) if edit_mode and task_data[5] else 0
            )
            deadline = st.date_input(
                "Deadline",
                value=parse_date(task_data[4]) if edit_mode else None
            )
            planned_time = st.number_input(
                "Planned Time (hours)",
                min_value=0.0,
                value=float(task_data[8]) if edit_mode and task_data[8] else 0.0
            )

        if edit_mode:
            st.markdown("### 📊 Tracking")
            track_col1, track_col2 = st.columns(2)
            with track_col1:
                actual_start_date = st.date_input(
                    "Actual Start Date",
                    value=parse_date(task_data[10]) if edit_mode else None
                )
                actual_cost = st.number_input(
                    "Actual Cost ($)",
                    min_value=0.0,
                    value=float(task_data[7]) if edit_mode and task_data[7] else 0.0
                )
                
            with track_col2:
                actual_deadline = st.date_input(
                    "Actual Deadline",
                    value=parse_date(task_data[11]) if edit_mode else None
                )
                actual_time_spent = st.number_input(
                    "Actual Time Spent (hours)",
                    min_value=0.0,
                    value=float(task_data[8]) if edit_mode and task_data[8] else 0.0
                )
                

        st.markdown("### 👥 Assignment")
        team_members = query_db("""
            SELECT u.id, u.username FROM project_team pt
            JOIN users u ON pt.user_id = u.id WHERE pt.project_id = ?
            UNION
            SELECT u.id, u.username FROM projects p
            JOIN users u ON p.user_id = u.id WHERE p.id = ?
        """, (project_id, project_id)) if project_id else []
        
        member_options = {m[0]: m[1] for m in (team_members or [])}
        member_options[None] = "Unassigned"
        
        assigned_to = st.selectbox(
            "Assigned To",
            options=list(member_options.keys()),
            format_func=lambda x: member_options[x],
            index=list(member_options.keys()).index(task_data[8]) if edit_mode and task_data[8] in member_options else 0
        )

        st.markdown("---")
        btn_col1, btn_col2, _ = st.columns([1,1,3])
        with btn_col1:
            submit_label = "💾 Save" if edit_mode else "➕ Create"
            submitted = st.form_submit_button(submit_label, type="primary")
        with btn_col2:
            cancelled = st.form_submit_button("❌ Cancel", type="secondary")

        if submitted:
            if not new_title:
                st.error("Task title is required!")
            else:
                start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
                deadline_str = deadline.strftime("%Y-%m-%d") if deadline else None
                
                if edit_mode:
                    actual_start_str = actual_start_date.strftime("%Y-%m-%d") if actual_start_date else None
                    actual_deadline_str = actual_deadline.strftime("%Y-%m-%d") if actual_deadline else None
                    
                    query_db("""
                        UPDATE tasks SET
                            title=?, description=?, priority=?,
                            start_date=?, deadline=?, status=?,
                            budget=?,actual_cost=?, time_spent=?, assigned_to=?,
                            actual_start_date=?, actual_deadline=?
                        WHERE id=?
                    """, (
                        new_title, new_desc, new_priority,
                        start_date_str, deadline_str, new_status,
                        budget, actual_cost, actual_time_spent, assigned_to,
                        actual_start_str, actual_deadline_str,
                        st.session_state.editing_task_id
                    ))
                    st.success("Task updated!")
                else:
                    query_db("""
                        INSERT INTO tasks (
                            project_id, title, description, priority,
                            start_date, deadline, status,
                            budget, time_spent, assigned_to
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project_id, new_title, new_desc, new_priority,
                        start_date_str, deadline_str, new_status,
                        budget, planned_time, assigned_to
                    ))
                    st.success("Task created!")
                
                st.session_state.show_task_form = False
                st.session_state.editing_task_id = None
                st.rerun()
        
        if cancelled:
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            st.rerun()

def workspace_page():
    st.markdown("---")
    st.subheader("🔍 Select Workspace")
    
    projects = query_db("SELECT id, name, user_id FROM projects")
    
    if not projects:
        st.warning("No projects available. Create a project first.")
        st.stop()
    
    project_options = {p[0]: (p[1], p[2]) for p in projects}
    selected_project_id = st.selectbox(
        "Choose Project",
        options=list(project_options.keys()),
        format_func=lambda x: project_options[x][0],
        key="workspace_project"
    )
    
    is_project_owner = (project_options[selected_project_id][1] == st.session_state.user_id or 
                       st.session_state.user_role == "Admin")
    
    st.markdown("---")
    st.subheader(f"🚀 {project_options[selected_project_id][0]} Workspace")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Tasks", 
        "📂 Files", 
        "💬 Discussions", 
        "📅 Timeline", 
        "📊 Progress", 
        "👥 Team"
    ])

    #
    with tab1:  # Task Management
        st.subheader("Task Management")
        
        if 'show_task_form' not in st.session_state:
            st.session_state.show_task_form = False
        if 'editing_task_id' not in st.session_state:
            st.session_state.editing_task_id = None
        
        view_option = st.radio(
            "View Mode:",
            ["List", "Kanban Board", "Gantt Chart"],
            horizontal=True,
            key="task_view"
        )
        
        # Fetch tasks from database
        tasks = query_db("""
            SELECT id, title, description, status, priority, start_date, deadline, assigned_to 
            FROM tasks 
            WHERE project_id = ?
        """, (selected_project_id,)) or []
        
        if st.session_state.show_task_form:
            if st.session_state.editing_task_id:
                edit_task_in_workspace(st.session_state.editing_task_id, selected_project_id)
            else:
                render_task_form(edit_mode=False, project_id=selected_project_id)
        else:
            if view_option == "List":
                st.write("### Task List")

                # Status color configuration
                status_config = {
                    "Pending": {"color": "#FFA07A", "bg_color": "#FFF5F0", "icon": "⏳"},
                    "In Progress": {"color": "#1E90FF", "bg_color": "#F0F8FF", "icon": "🚧"},
                    "Completed": {"color": "#3CB371", "bg_color": "#F0FFF0", "icon": "✅"},
                    "On Hold": {"color": "#FFD700", "bg_color": "#FFF9E6", "icon": "⏸️"}
                }

                # Add New Task button for project owners
                if is_project_owner and st.button("➕ Add New Task", key="add_new_task_btn"):
                    st.session_state.show_task_form = True
                    st.session_state.editing_task_id = None
                    st.rerun()

                if not tasks:
                    st.info("No tasks found for this project")
                else:
                    # Create rows of 3 tasks each
                    for i in range(0, len(tasks), 3):
                        row_tasks = tasks[i:i+3]
                        cols = st.columns(3, gap="large")  # Increased gap between cards
                        
                        for j, task in enumerate(row_tasks):
                            task_id, title, description, status, priority, start_date, deadline, assigned_to = task
                            status_style = status_config.get(status, {})
                            
                            with cols[j]:
                                # Card container
                                st.markdown(
                                    f"""
                                    <div style="
                                        border-left: 4px solid {status_style.get('color', '#CCCCCC')};
                                        padding: 16px;
                                        margin-bottom: 20px;
                                        border-radius: 6px;
                                        background-color: {status_style.get('bg_color', '#FFFFFF')};
                                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                                        height: 100%;
                                    ">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.1rem;">{status_style.get('icon', '')} {title}</h3>
                                            <span style="
                                                padding: 4px 8px;
                                                border-radius: 12px;
                                                font-size: 0.75em;
                                                background-color: {'#ffcccc' if priority == 'High' else '#fff3cd' if priority == 'Medium' else '#e6ffe6'};
                                            ">{priority}</span>
                                        </div>
                                        <p style="margin: 0 0 12px 0; color: #555; font-size: 0.9rem; min-height: 40px;">
                                            {description or 'No description'}
                                        </p>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 8px;">
                                            <div style="margin-bottom: 4px;">📅 <strong>Start:</strong> {start_date if start_date else 'Not set'}</div>
                                            <div style="margin-bottom: 4px;">⏱️ <strong>Deadline:</strong> {deadline if deadline else 'Not set'}</div>
                                            <div>👤 <strong>Assigned:</strong> {query_db('SELECT username FROM users WHERE id=?', (assigned_to,), one=True)[0] if assigned_to else 'Unassigned'}</div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                # Action buttons container
                                with st.container():
                                    col1, col2 = st.columns(2)
                                    
                                    # Check if user can edit this task
                                    can_edit_task = (is_project_owner or 
                                                    (assigned_to and assigned_to == st.session_state.user_id))
                                    
                                    with col1:
                                        if can_edit_task and st.button("Edit", key=f"edit_{task_id}", use_container_width=True):
                                            st.session_state.editing_task_id = task_id
                                            st.session_state.show_task_form = True
                                            st.rerun()
                                    
                                    with col2:
                                        # Only project owners can delete
                                        if is_project_owner and st.button("Delete", key=f"delete_{task_id}", type="secondary", use_container_width=True):
                                            st.session_state.task_to_delete = task_id
                                    
                                    # Delete confirmation (only shown if project owner)
                                    if is_project_owner and 'task_to_delete' in st.session_state and st.session_state.task_to_delete == task_id:
                                        st.warning("Delete this task?")
                                        confirm_col1, confirm_col2 = st.columns(2)
                                        with confirm_col1:
                                            if st.button("Yes", key=f"confirm_{task_id}", use_container_width=True):
                                                query_db("DELETE FROM tasks WHERE id=?", (task_id,))
                                                st.success("Task deleted!")
                                                del st.session_state.task_to_delete
                                                st.rerun()
                                        with confirm_col2:
                                            if st.button("No", key=f"cancel_{task_id}", use_container_width=True):
                                                del st.session_state.task_to_delete
                                                st.rerun()






            elif view_option == "Kanban Board":
                st.write("### Kanban Board")
                
                status_config = {
                    "Pending": {"color": "#FFA07A", "bg_color": "#FFF5F0", "icon": "⏳"},
                    "In Progress": {"color": "#1E90FF", "bg_color": "#F0F8FF", "icon": "🚧"},
                    "Completed": {"color": "#3CB371", "bg_color": "#F0FFF0", "icon": "✅"}
                }
                
                cols = st.columns(3, gap="small")
                
                for idx, (status, config) in enumerate(status_config.items()):
                    with cols[idx]:
                        st.markdown(
                            f"<h3 style='color:{config['color']}; text-align:center; margin-bottom:10px;'>"
                            f"{config['icon']} {status}</h3>",
                            unsafe_allow_html=True
                        )
                        
                        status_tasks = [t for t in tasks if t[3] == status]
                        
                        for task in status_tasks:
                            deadline_info = ""
                            if task[6]:
                                deadline_date = datetime.strptime(task[6], "%Y-%m-%d").date()
                                days_left = (deadline_date - datetime.now().date()).days
                                deadline_info = f"<br><small>📅 {days_left}d left</small>"
                            
                            priority_color = {
                                "High": "red",
                                "Medium": "orange",
                                "Low": "green"
                            }.get(task[4], "gray")
                            
                            st.markdown(
                                f"<div style='background-color:{config['bg_color']}; border-left:4px solid {config['color']}; padding:8px; margin-bottom:8px; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.1);'>"
                                f"<div style='display:flex; justify-content:space-between;'>"
                                f"<strong>{task[1]}</strong>"
                                f"<span style='color:{priority_color}; font-size:0.8em;'>⬤</span>"
                                f"</div>"
                                f"<div style='font-size:0.8em; color:#555;'>{task[2][:50]}{'...' if len(task[2])>50 else ''}</div>"
                                f"{deadline_info}"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                            
                            if is_project_owner or (task[7] and task[7] == st.session_state.user_id):
                                new_status = st.selectbox(
                                    "Change Status",
                                    list(status_config.keys()),
                                    index=list(status_config.keys()).index(status),
                                    key=f"kanban_status_{task[0]}",
                                    label_visibility="collapsed"
                                )
                                
                                if new_status != status:
                                    query_db("UPDATE tasks SET status=? WHERE id=?", (new_status, task[0]))
                                    st.rerun()
                            else:
                                st.caption(f"Status: {status}")

            # Gantt Chart
            elif view_option == "Gantt Chart":
                st.write("### Task Timeline")
                
                # Get and sort tasks
                tasks = query_db("""
                    SELECT t.id, t.title, t.start_date, t.deadline, t.status, 
                        t.priority, t.assigned_to, t.actual_start_date, t.actual_deadline
                    FROM tasks t
                    WHERE t.project_id = ?
                """, (selected_project_id,)) or []
                
                tasks = sort_tasks(tasks)  # Apply consistent sorting
                
                gantt_data = []
                for task in tasks:
                    # Planned timeline
                    planned_start = pd.to_datetime(task[2]) if task[2] else None
                    planned_end = pd.to_datetime(task[3]) if task[3] else None
                    
                    # Actual timeline
                    actual_start = pd.to_datetime(task[7]) if task[7] else None
                    actual_end = pd.to_datetime(task[8]) if task[8] else None
                    
                    # Get assignee name if available
                    assigned_to = query_db("SELECT username FROM users WHERE id=?", (task[6],), one=True) if task[6] else None
                    
                    if planned_start and planned_end:
                        gantt_data.append({
                            "Task": task[1],
                            "Start": planned_start,
                            "Finish": planned_end,
                            "Timeline": "Planned",
                            "Status": task[4],
                            "Priority": task[5],
                            "Assignee": assigned_to[0] if assigned_to else "Unassigned"
                        })
                    
                    if actual_start and actual_end:
                        gantt_data.append({
                            "Task": task[1],
                            "Start": actual_start,
                            "Finish": actual_end,
                            "Timeline": "Actual",
                            "Status": task[4],
                            "Priority": task[5],
                            "Assignee": assigned_to[0] if assigned_to else "Unassigned"
                        })

                if gantt_data:
                    gantt_df = pd.DataFrame(gantt_data)
                    
                    # Ensure all hover_data columns exist
                    hover_columns = ["Status", "Priority", "Assignee"]
                    existing_hover_columns = [col for col in hover_columns if col in gantt_df.columns]
                    
                    fig = px.timeline(
                        gantt_df,
                        x_start="Start",
                        x_end="Finish",
                        y="Task",
                        color="Timeline",
                        color_discrete_map={
                            "Planned": "lightgray",
                            "Actual": "blue"
                        },
                        hover_data=existing_hover_columns,
                        title="Task Timeline (Planned vs Actual)"
                    )
                    
                    today = pd.to_datetime('today')
                    fig.add_shape(
                        type="line",
                        x0=today,
                        x1=today,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dot")
                    )
                    
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(
                        height=600,
                        xaxis_title="Timeline",
                        yaxis_title="Tasks"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No tasks with dates to display")




    with tab2:
        st.subheader("Project Files")
        st.markdown("---")
        
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = set()
        if 'file_uploaded' not in st.session_state:
            st.session_state.file_uploaded = False

        with st.expander("📤 Upload New File", expanded=False):
            with st.form("file_upload_form", clear_on_submit=True):
                file_type = st.radio(
                    "File belongs to:",
                    ["Project", "Task"],
                    horizontal=True
                )
                
                task_id = None
                if file_type == "Task":
                    tasks = query_db("""
                        SELECT id, title FROM tasks 
                        WHERE project_id = ?
                        ORDER BY title
                    """, (selected_project_id,)) or []
                    if tasks:
                        task_options = {t[0]: t[1] for t in tasks}
                        task_id = st.selectbox(
                            "Select Task",
                            options=list(task_options.keys()),
                            format_func=lambda x: task_options[x]
                        )
                    else:
                        st.warning("No tasks available for this project")
                
                uploaded_file = st.file_uploader(
                    "Choose file",
                    type=["pdf", "docx", "xlsx", "pptx", "jpg", "png", "txt"],
                    key="file_uploader"
                )
                
                if st.form_submit_button("Upload", type="primary"):
                    if uploaded_file:
                        try:
                            uploader = query_db("""
                                SELECT username FROM users 
                                WHERE id = ?
                            """, (st.session_state.user_id,), one=True)
                            
                            username = uploader[0] if uploader else "Unknown"
                            
                            query_db("""
                                INSERT INTO attachments (
                                    file_name, 
                                    file_data, 
                                    task_id, 
                                    project_id,
                                    uploaded_by,
                                    uploaded_at
                                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                            """, (
                                uploaded_file.name,
                                uploaded_file.read(),
                                task_id if file_type == "Task" else None,
                                selected_project_id,
                                st.session_state.user_id
                            ))
                            
                            st.success("File uploaded successfully!")
                            st.session_state.file_uploaded = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Upload error: {str(e)}")
                    else:
                        st.error("Please select a file to upload")

        st.markdown("### Project Files")
        project_files = query_db("""
            SELECT a.id, a.file_name, a.uploaded_at, u.username
            FROM attachments a
            JOIN users u ON a.uploaded_by = u.id
            WHERE a.project_id = ? AND a.task_id IS NULL
            ORDER BY a.uploaded_at DESC
        """, (selected_project_id,)) or []
        
        if project_files:
            for file in project_files:
                file_id, file_name, uploaded_at, username = file
                with st.container():
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        st.markdown(f"""
                            <div class="file-card">
                                <div class="file-name">{file_name}</div>
                                <div class="file-meta">
                                    Uploaded by {username} • {uploaded_at}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        file_data = query_db("SELECT file_data FROM attachments WHERE id=?", (file_id,), one=True)
                        st.download_button(
                            "↓",
                            data=file_data[0] if file_data else b'',
                            file_name=file_name,
                            key=f"dl_{file_id}",
                            help="Download file"
                        )
                    with col3:
                        if st.button("🗑️", key=f"del_{file_id}", help="Delete file"):
                            query_db("DELETE FROM attachments WHERE id=?", (file_id,))
                            st.success("File deleted!")
                            st.rerun()
        else:
            st.info("No project files uploaded yet")

        st.markdown("---")
        st.markdown("### Task Files")
        task_files = query_db("""
            SELECT a.id, a.file_name, a.uploaded_at, u.username, t.title
            FROM attachments a
            JOIN users u ON a.uploaded_by = u.id
            JOIN tasks t ON a.task_id = t.id
            WHERE a.project_id = ? AND a.task_id IS NOT NULL
            ORDER BY t.title, a.uploaded_at DESC
        """, (selected_project_id,)) or []
        
        if task_files:
            current_task = None
            for file in task_files:
                file_id, file_name, uploaded_at, username, task_title = file
                
                if task_title != current_task:
                    st.markdown(f"**Task:** {task_title}")
                    current_task = task_title
                
                with st.container():
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        st.markdown(f"""
                            <div class="file-card">
                                <div class="file-name">{file_name}</div>
                                <div class="file-meta">
                                    Uploaded by {username} • {uploaded_at}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        file_data = query_db("SELECT file_data FROM attachments WHERE id=?", (file_id,), one=True)
                        st.download_button(
                            "↓",
                            data=file_data[0] if file_data else b'',
                            file_name=file_name,
                            key=f"t_dl_{file_id}",
                            help="Download file"
                        )
                    with col3:
                        if st.button("🗑️", key=f"t_del_{file_id}", help="Delete file"):
                            query_db("DELETE FROM attachments WHERE id=?", (file_id,))
                            st.success("File deleted!")
                            st.rerun()
        else:
            st.info("No task files uploaded yet")

        st.markdown("""
        <script>
        function downloadFile(fileId) {
            window.location.href = `/download_file?file_id=${fileId}`;
        }
        function confirmDelete(fileId) {
            if (confirm('Are you sure you want to delete this file?')) {
                fetch(`/delete_file?file_id=${fileId}`, {method: 'POST'})
                    .then(response => location.reload());
            }
        }
        </script>
        """, unsafe_allow_html=True)

    with tab3:
        st.subheader("Team Discussions")
        
        if 'show_new_topic' not in st.session_state:
            st.session_state.show_new_topic = False
        if 'editing_topic_id' not in st.session_state:
            st.session_state.editing_topic_id = None
        if 'topic_to_delete' not in st.session_state:
            st.session_state.topic_to_delete = None
        if 'editing_msg_id' not in st.session_state:
            st.session_state.editing_msg_id = None
        if 'msg_to_delete' not in st.session_state:
            st.session_state.msg_to_delete = None
        if 'expanded_topics' not in st.session_state:
            st.session_state.expanded_topics = {}

        st.markdown("""
        <style>
        .discussion-topic {
            background-color: #4e73df;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: 600;
            margin-bottom: 8px;
            display: inline-block;
        }
        .discussion-container {
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            background-color: #f8f9fa;
            border-left: 4px solid #4e73df;
        }
        .discussion-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .discussion-user {
            font-weight: 600;
            color: #2c3e50;
            font-size: 0.95rem;
        }
        .discussion-time {
            font-size: 0.8em;
            color: #7f8c8d;
        }
        .discussion-message {
            padding: 12px 0;
            line-height: 1.5;
            color: #495057;
            font-size: 0.9rem;
        }
        .search-highlight {
            background-color: #fff3cd;
            padding: 0 2px;
            border-radius: 3px;
        }
        .archived-topic {
            opacity: 0.7;
            border-left-color: #6c757d !important;
        }
        </style>
        """, unsafe_allow_html=True)

        def highlight_search_terms(text, query):
            if not query or not text:
                return text
            text_lower = text.lower()
            query_lower = query.lower()
            result = []
            start_idx = 0
            
            while True:
                idx = text_lower.find(query_lower, start_idx)
                if idx == -1:
                    break
                result.append(text[start_idx:idx])
                result.append(f'<span class="search-highlight">{text[idx:idx+len(query)]}</span>')
                start_idx = idx + len(query)
            
            result.append(text[start_idx:])
            return ''.join(result)

        def toggle_topic_expansion(topic_id):
            st.session_state.expanded_topics[topic_id] = not st.session_state.expanded_topics.get(topic_id, False)

        def render_topic(topic, is_topic_match, search_query, is_last_topic=False):
            topic_id, topic_title, creator, created_at, is_archived, message_count = topic
            
            try:
                timestamp = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
            except:
                timestamp = created_at
            
            current_user = query_db("SELECT username FROM users WHERE id = ?", (st.session_state.user_id,), one=True)
            current_username = current_user[0] if current_user else "Unknown"
            is_creator_or_admin = (creator == current_username) or (st.session_state.user_role == "Admin")
            
            display_topic = highlight_search_terms(topic_title, search_query) if search_query and is_topic_match else topic_title
            
            if not is_last_topic:
                st.markdown("---")

            toggle_key = f"toggle_{topic_id}_{message_count}_{int(is_archived)}"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                with st.container():
                    st.markdown(
                        f'<span class="discussion-topic" style="background-color: {"#6c757d" if is_archived else "#4e73df"}">'
                        f'{display_topic}'
                        '</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"Started by {creator} on {timestamp} • {message_count} messages{' • 📁 Archived' if is_archived else ''}")
            
            with col2:
                if st.button("📖" if not st.session_state.expanded_topics.get(topic_id, False) else "📕", 
                            key=toggle_key,
                            help="Show/Hide messages"):
                    toggle_topic_expansion(topic_id)
                    st.rerun()
          
            if is_creator_or_admin:
                action_cols = st.columns(3 if not is_archived else 2)
                with action_cols[0]:
                    if st.button("✏️ Edit", key=f"edit_{topic_id}"):
                        st.session_state.editing_topic_id = topic_id
                        st.session_state.editing_topic_title = topic_title
                        st.rerun()
                if not is_archived:
                    with action_cols[1]:
                        if st.button("📁 Archive", key=f"archive_{topic_id}"):
                            query_db("UPDATE discussion_topics SET is_archived=1 WHERE id=?", (topic_id,))
                            st.success("Topic archived!")
                            st.rerun()
                with action_cols[-1]:
                    if st.button("🗑️ Delete", key=f"delete_{topic_id}"):
                        st.session_state.topic_to_delete = topic_id
                
                if st.session_state.get('topic_to_delete') == topic_id:
                    st.warning("Delete this topic and all its messages?")
                    confirm_cols = st.columns(2)
                    with confirm_cols[0]:
                        if st.button("✅ Yes", key=f"confirm_del_{topic_id}"):
                            query_db("DELETE FROM discussion_messages WHERE topic_id=?", (topic_id,))
                            query_db("DELETE FROM discussion_topics WHERE id=?", (topic_id,))
                            st.success("Topic deleted!")
                            del st.session_state.topic_to_delete
                            st.rerun()
                    with confirm_cols[1]:
                        if st.button("❌ No", key=f"cancel_del_{topic_id}"):
                            del st.session_state.topic_to_delete
                            st.rerun()
            
            if st.session_state.get('editing_topic_id') == topic_id:
                with st.form(f"edit_topic_form_{topic_id}"):
                    new_title = st.text_input("Topic Title", value=st.session_state.editing_topic_title)
                    cols = st.columns(2)
                    with cols[0]:
                        if st.form_submit_button("💾 Save"):
                            if new_title.strip():
                                query_db("UPDATE discussion_topics SET topic=? WHERE id=?", (new_title, topic_id))
                                st.success("Topic updated!")
                                del st.session_state.editing_topic_id
                                del st.session_state.editing_topic_title
                                st.rerun()
                    with cols[1]:
                        if st.form_submit_button("❌ Cancel"):
                            del st.session_state.editing_topic_id
                            del st.session_state.editing_topic_title
                            st.rerun()
            
            if st.session_state.expanded_topics.get(topic_id, False):
                messages = query_db("""
                    SELECT m.id, m.message, u.username, m.created_at
                    FROM discussion_messages m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.topic_id = ?
                    ORDER BY m.created_at ASC
                """, (topic_id,))
                
                for msg in messages:
                    msg_id, msg_content, author, msg_time = msg
                    try:
                        msg_time = datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y at %I:%M %p")
                    except:
                        pass
                    
                    display_msg = highlight_search_terms(msg_content, search_query) if search_query and not is_topic_match else msg_content
                    
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="discussion-container {'archived-topic' if is_archived else ''}">
                                <div class="discussion-header">
                                    <div class="discussion-user">
                                        <span style="font-size:1.1em;">👤</span> {author}
                                    </div>
                                    <div class="discussion-time">{msg_time}</div>
                                </div>
                                <div class="discussion-message">{display_msg}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        if (author == current_username or st.session_state.user_role == "Admin") and not is_archived:
                            action_cols = st.columns([0.5, 0.5, 3])
                            
                            with action_cols[0]:
                                if st.button("✏️", 
                                            key=f"edit_msg_{msg_id}",
                                            help="Edit message"):
                                    st.session_state.editing_msg_id = msg_id
                                    st.session_state.editing_msg_content = msg_content
                            
                            with action_cols[1]:
                                if st.button("🗑️", 
                                            key=f"delete_msg_{msg_id}",
                                            help="Delete message"):
                                    st.session_state.msg_to_delete = msg_id
                            
                            st.markdown("""
                            <style>
                                div[data-testid="column"] {
                                    gap: 0.5rem;
                                }
                                button[kind="secondary"] {
                                    padding: 0.25rem 0.5rem;
                                    min-width: unset;
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            if st.session_state.get('msg_to_delete') == msg_id:
                                st.warning("Delete this message?")
                                confirm_cols = st.columns(2)
                                with confirm_cols[0]:
                                    if st.button("✅ Yes", key=f"confirm_del_msg_{msg_id}"):
                                        query_db("DELETE FROM discussion_messages WHERE id=?", (msg_id,))
                                        st.success("Message deleted!")
                                        del st.session_state.msg_to_delete
                                        st.rerun()
                                with confirm_cols[1]:
                                    if st.button("❌ No", key=f"cancel_del_msg_{msg_id}"):
                                        del st.session_state.msg_to_delete
                                        st.rerun()
                            
                            if st.session_state.get('editing_msg_id') == msg_id:
                                with st.form(f"edit_msg_form_{msg_id}"):
                                    new_content = st.text_area("Edit message", value=st.session_state.editing_msg_content, height=100)
                                    cols = st.columns(2)
                                    with cols[0]:
                                        if st.form_submit_button("💾 Save"):
                                            if new_content.strip():
                                                query_db("UPDATE discussion_messages SET message=? WHERE id=?", (new_content, msg_id))
                                                st.success("Message updated!")
                                                del st.session_state.editing_msg_id
                                                del st.session_state.editing_msg_content
                                                st.rerun()
                                    with cols[1]:
                                        if st.form_submit_button("❌ Cancel"):
                                            del st.session_state.editing_msg_id
                                            del st.session_state.editing_msg_content
                                            st.rerun() 
                
                if not is_archived:
                    with st.form(f"reply_form_{topic_id}", clear_on_submit=True):
                        reply = st.text_area("Add your message", key=f"reply_{topic_id}", height=80)
                        if st.form_submit_button("Post Reply", type="secondary"):
                            if reply.strip():
                                query_db("""
                                    INSERT INTO discussion_messages (topic_id, user_id, message, created_at)
                                    VALUES (?, ?, ?, datetime('now'))
                                """, (topic_id, st.session_state.user_id, reply))
                                st.success("Message added!")
                                st.rerun()

        search_col, new_topic_col = st.columns([3, 1])
        with search_col:
            search_query = st.text_input("Search discussions", placeholder="Enter topic or message keywords...")
        with new_topic_col:
            if st.button("➕ New Topic", use_container_width=True):
                st.session_state.show_new_topic = True

        if st.session_state.show_new_topic:
            with st.form("new_topic_form", clear_on_submit=True):
                st.markdown("### Start New Discussion")
                topic = st.text_input("Topic Title*", placeholder="Enter discussion topic title")
                message = st.text_area("Initial Message*", placeholder="Write your first message...", height=100)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.form_submit_button("Create Discussion", type="primary"):
                        if topic.strip() and message.strip():
                            topic_id = query_db("""
                                INSERT INTO discussion_topics (project_id, user_id, topic, created_at, is_archived)
                                VALUES (?, ?, ?, datetime('now'), 0)
                                RETURNING id
                            """, (selected_project_id, st.session_state.user_id, topic), one=True)[0]
                            
                            query_db("""
                                INSERT INTO discussion_messages (topic_id, user_id, message, created_at)
                                VALUES (?, ?, ?, datetime('now'))
                            """, (topic_id, st.session_state.user_id, message))
                            
                            st.success("Discussion topic created!")
                            st.session_state.show_new_topic = False
                            st.rerun()
                        else:
                            st.error("Please provide both a topic title and initial message")
                with col2:
                    if st.form_submit_button("Cancel", type="secondary"):
                        st.session_state.show_new_topic = False
                        st.rerun()

        topics = query_db("""
            SELECT t.id, t.topic, u.username, t.created_at, t.is_archived,
                (SELECT COUNT(*) FROM discussion_messages WHERE topic_id = t.id) as message_count
            FROM discussion_topics t
            JOIN users u ON t.user_id = u.id
            WHERE t.project_id = ?
            ORDER BY t.is_archived ASC, t.created_at DESC
        """, (selected_project_id,))
        
        if topics:
            filtered_topics = []
            if search_query:
                search_lower = search_query.lower()
                for topic in topics:
                    if topic[4]:
                        continue
                    
                    if search_lower in topic[1].lower():
                        filtered_topics.append((topic, True))
                        continue
                    
                    messages = query_db("""
                        SELECT message FROM discussion_messages
                        WHERE topic_id = ? AND LOWER(message) LIKE ?
                        LIMIT 1
                    """, (topic[0], f"%{search_lower}%"))
                    if messages:
                        filtered_topics.append((topic, False))
            else:
                filtered_topics = [(topic, False) for topic in topics if not topic[4]]
            
            if not filtered_topics and search_query:
                st.info("No discussions found matching your search")
            else:
                active_topics = [t for t in filtered_topics if not t[0][4]]
                archived_topics = [t for t in topics if t[4]] if not search_query else []
                
                if active_topics:
                    st.markdown("### Active Discussions")
                    for i, (topic, is_topic_match) in enumerate(active_topics):
                        render_topic(topic, is_topic_match, search_query, i == len(active_topics)-1)

                if archived_topics and not search_query:
                    with st.expander(f"📁 Archived Discussions ({len(archived_topics)})", expanded=False):
                        for i, topic in enumerate(archived_topics):
                            render_topic(topic, False, None, i == len(archived_topics)-1)
        else:
            st.info("No discussion topics yet. Start one by clicking 'New Topic'")

    with tab4:
        st.subheader("Project Timeline")
        
        tasks = query_db("""
            SELECT 
                t.id, t.title, t.description, t.status, 
                t.start_date, t.deadline, 
                t.actual_start_date, t.actual_deadline,
                t.priority, u.username
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.project_id = ?
        """, (selected_project_id,)) or []
        
        #
        if tasks:
            gantt_data = []
            for task in tasks:
                # Planned timeline
                planned_start = pd.to_datetime(task[4]) if task[4] else None
                planned_end = pd.to_datetime(task[5]) if task[5] else None
                
                # Actual timeline
                actual_start = pd.to_datetime(task[6]) if task[6] else None
                actual_end = pd.to_datetime(task[7]) if task[7] else None
                
                if planned_start and planned_end:
                    gantt_data.append({
                        "Task": task[1],
                        "Start": planned_start,
                        "Finish": planned_end,
                        "Timeline": "Planned",
                        "Status": task[3],
                        "Priority": task[8],
                        "Assignee": task[9] or "Unassigned"
                    })
                
                if actual_start and actual_end:
                    gantt_data.append({
                        "Task": task[1],
                        "Start": actual_start,
                        "Finish": actual_end,
                        "Timeline": "Actual",
                        "Status": task[3],
                        "Priority": task[8],
                        "Assignee": task[9] or "Unassigned"
                    })

            #
            if gantt_data:
                gantt_df = pd.DataFrame(gantt_data)
                
                # Create figure using plotly express timeline
                fig = px.timeline(
                    gantt_df,
                    x_start="Start",
                    x_end="Finish",
                    y="Task",
                    color="Timeline",
                    color_discrete_map={
                        "Planned": "lightgray",
                        "Actual": "blue"
                    },
                    hover_data=["Status", "Priority", "Assignee"],
                    title="Project Timeline (Planned vs Actual)"
                )
                
                # Add today's line - FIXED VERSION
                today = pd.Timestamp.now().normalize()  # Get today's date at midnight
                fig.add_shape(
                    type="line",
                    x0=today,
                    x1=today,
                    y0=-0.5,
                    y1=len(gantt_df['Task'].unique()) - 0.5,
                    line=dict(color="red", width=2, dash="dot")
                )
                
                # Add today's annotation
                fig.add_annotation(
                    x=today,
                    y=len(gantt_df['Task'].unique()) - 0.5,
                    text="Today",
                    showarrow=False,
                    yshift=10,
                    font=dict(color="red")
                )
                
                # Update layout
                fig.update_yaxes(
                    categoryorder="total ascending",
                    autorange="reversed"
                )
                fig.update_layout(
                    height=600,
                    xaxis_title="Timeline",
                    yaxis_title="Tasks",
                    hovermode="closest",
                    showlegend=True,
                    legend_title="Timeline Type"
                )
                
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("No tasks found for timeline visualization")


    with tab5:
        st.subheader("Project Progress")
        
        tasks = query_db("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE project_id = ?
        """, (selected_project_id,), one=True)
        
        if tasks and tasks[0] > 0:
            completion_rate = (tasks[1] / tasks[0]) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
            
            fig = go.Figure(go.Pie(
                labels=["Completed", "Remaining"],
                values=[tasks[1], tasks[0] - tasks[1]],
                hole=0.4
            ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks found for progress tracking")
    
    with tab6:
        st.subheader("Project Team")
        
        is_admin_or_owner = False
        if st.session_state.user_role == "Admin":
            is_admin_or_owner = True
        else:
            project_owner = query_db("SELECT user_id FROM projects WHERE id=?", (selected_project_id,), one=True)
            if project_owner and project_owner[0] == st.session_state.user_id:
                is_admin_or_owner = True
        
        members = query_db("""
            SELECT u.id, u.username, u.role, u.email 
            FROM project_team pt
            JOIN users u ON pt.user_id = u.id
            WHERE pt.project_id = ?
            UNION
            SELECT u.id, u.username, u.role, u.email
            FROM projects p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (selected_project_id, selected_project_id))
        
        if members:
            st.markdown("### Team Members")
            
            cols = st.columns(3)
            col_index = 0
            
            for idx, member in enumerate(members):
                with cols[col_index]:
                    role_colors = {
                        "Admin": "#FFEBEE",
                        "Manager": "#E8F5E9",
                        "Developer": "#E3F2FD",
                        "Designer": "#F3E5F5",
                        "default": "#FAFAFA"
                    }
                    card_color = role_colors.get(member[2], role_colors["default"])
                    
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div style="background-color: {card_color}; padding: 10px; border-radius: 4px; margin: -10px -10px 10px -10px;">
                                <div style="display: flex; align-items: center;">
                                    <div style="font-size: 24px; margin-right: 10px;">👤</div>
                                    <div>
                                        <h3 style="margin: 0; padding: 0; color: #333;">{member[1]}</h3>
                                        <p style="margin: 0; padding: 0; color: #666; font-weight: 500;">{member[2]}</p>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown(
                            f"""
                            <div style="margin-top: 5px;">
                                <p style="margin: 8px 0; font-size: 14px; display: flex; align-items: center;">
                                    <span style="margin-right: 8px; color: #555;">✉️</span> 
                                    <span>{member[3]}</span>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        is_owner = query_db("SELECT user_id FROM projects WHERE id=?", (selected_project_id,), one=True)[0] == member[0]
                        if is_admin_or_owner and not is_owner:
                            if st.button("Remove Member", key=f"remove_{member[0]}", 
                                    type="secondary", use_container_width=True):
                                st.session_state.member_to_remove = member[0]
                            
                            if 'member_to_remove' in st.session_state and st.session_state.member_to_remove == member[0]:
                                st.warning("Are you sure you want to remove this team member?")
                                confirm_cols = st.columns(2)
                                with confirm_cols[0]:
                                    if st.button("✅ Confirm", key=f"confirm_remove_{member[0]}",
                                            type="primary", use_container_width=True):
                                        query_db("DELETE FROM project_team WHERE project_id=? AND user_id=?", 
                                                (selected_project_id, member[0]))
                                        st.success("Member removed!")
                                        del st.session_state.member_to_remove
                                        st.rerun()
                                with confirm_cols[1]:
                                    if st.button("❌ Cancel", key=f"cancel_remove_{member[0]}",
                                            type="secondary", use_container_width=True):
                                        del st.session_state.member_to_remove
                                        st.rerun()
                
                col_index = (col_index + 1) % 3
                if col_index == 0 and idx < len(members) - 1:
                    st.write("")
                    cols = st.columns(3)
            
            if is_admin_or_owner:
                st.markdown("---")
                st.subheader("Add Team Member")
                
                available_users = query_db("""
                    SELECT u.id, u.username, u.role 
                    FROM users u
                    WHERE u.id NOT IN (
                        SELECT user_id FROM project_team WHERE project_id = ?
                        UNION
                        SELECT user_id FROM projects WHERE id = ?
                    )
                """, (selected_project_id, selected_project_id))
                
                if available_users:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        user_options = {u[0]: f"{u[1]} ({u[2]})" for u in available_users}
                        selected_user = st.selectbox(
                            "Select User to Add",
                            options=list(user_options.keys()),
                            format_func=lambda x: user_options[x]
                        )
                    
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("➕ Add to Team", use_container_width=True):
                            try:
                                query_db("""
                                    INSERT INTO project_team (project_id, user_id)
                                    VALUES (?, ?)
                                """, (selected_project_id, selected_user))
                                st.success("User added to team!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("User is already in the team")
                else:
                    st.info("No available users to add")
        else:
            st.info("No team members found")

if __name__ == "__main__":
    workspace_page() 