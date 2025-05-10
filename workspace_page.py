from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st 
import sqlite3 
import time
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
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




def render_project_form():
    """Form for creating/editing projects"""
    is_edit_mode = st.session_state.get('editing_project_id') is not None
    
    with st.form(key="project_form", clear_on_submit=not is_edit_mode):
        if is_edit_mode:
            st.subheader("✏️ Edit Project")
            project = query_db("""
                SELECT id, name, description, status, start_date, end_date, user_id, budget
                FROM projects WHERE id=?    
            """, (st.session_state.editing_project_id,), one=True)
            
            if not project:
                st.error("Project not found")
                st.session_state.show_project_form = False
                st.session_state.editing_project_id = None
                st.rerun()
            
            default_values = {
                'name': project[1],
                'description': project[2] or "",
                'status': project[3] if project[3] else "Planning",
                'start_date': datetime.strptime(project[4], "%Y-%m-%d").date() if project[4] else None,
                'end_date': datetime.strptime(project[5], "%Y-%m-%d").date() if project[5] else None,
                'manager_id': project[6],
                'budget': float(project[7]) if project[7] is not None else None
            }
        else:
            st.subheader("🆕 Create New Project")
            default_values = {
                'name': "",
                'description': "",
                'status': "Planning",
                'start_date': None,
                'end_date': None,
                'manager_id': None,
                'budget': None
            }
        
        # Form fields
        name = st.text_input("Project Name*", value=default_values['name'],
                            placeholder="Enter unique project name (required)")
        
        # Check for duplicate name as user types
        if name and name != default_values.get('name', ""):
            if not is_project_name_unique(name, st.session_state.editing_project_id if is_edit_mode else None):
                st.error("Project name already exists. Please choose a different name.")
        
        description = st.text_area("Description", value=default_values['description'], height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Status*",
                options=["Planning", "Active", "On Hold", "Completed", "Cancelled"],
                index=["Planning", "Active", "On Hold", "Completed", "Cancelled"].index(
                    default_values['status'] if default_values['status'] in ["Planning", "Active", "On Hold", "Completed", "Cancelled"] 
                    else "Planning"
                )
            )
            
            start_date = st.date_input(
                "Start Date*",
                value=default_values['start_date'] or datetime.now().date()
            )
        
        with col2:
            end_date = st.date_input(
                "End Date*",
                value=default_values['end_date'] or (datetime.now().date() + timedelta(days=30))
            )
            
            budget = st.number_input(
                "Budget ($)",
                min_value=0.0,
                value=default_values['budget'] if default_values['budget'] is not None else 0.0,
                step=100.0,
                format="%.2f"
            )
        
        # Manager selection - FIXED ISSUE WITH FORM CLOSING
        # Manager selection section - UPDATED TO USE DROPDOWN IN BOTH CREATE AND EDIT MODES
        if st.session_state.user_role == "Admin":
            # Admin can see all users
            users = query_db("SELECT id, username FROM users ORDER BY username")
            user_options = {u[0]: u[1] for u in users} if users else {}
        else:
            # Non-admins can only see managers/admins
            users = query_db("SELECT id, username FROM users WHERE role='Manager' OR role='Admin' ORDER BY username")
            user_options = {u[0]: u[1] for u in users} if users else {}
        
        if not is_edit_mode:
            # Create project form - show dropdown for manager selection
            manager_id = st.selectbox(
                "Project Manager*",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                index=0,
                help="Select the project manager" + (" (Admin can assign any user)" if st.session_state.user_role == "Admin" else "")
            )
        else:
            # Edit project form - show dropdown for manager selection (consistent with create form)
            if st.session_state.user_role == "Admin":
                # Admin can change to any user
                manager_id = st.selectbox(
                    "Project Manager*",
                    options=list(user_options.keys()),
                    format_func=lambda x: user_options[x],
                    index=list(user_options.keys()).index(default_values['manager_id']) 
                    if default_values['manager_id'] in user_options 
                    else 0,
                    help="Admin can assign any user as manager"
                )
            else:
                # Non-admin can see but not change the manager
                current_manager = query_db(
                    "SELECT username FROM users WHERE id=?",
                    (default_values['manager_id'],),
                    one=True
                )
                current_manager_name = current_manager[0] if current_manager else "Unknown"
                
                # Display disabled dropdown showing current manager
                manager_id = st.selectbox(
                    "Project Manager",
                    options=[default_values['manager_id']],
                    format_func=lambda x: current_manager_name,
                    index=0,
                    disabled=True,
                    help="Only administrators can change the project manager"
                )
        
        # Form actions
        # Form actions
        st.divider()
        col1, col2, _ = st.columns([1,1,2])
        with col1:
            submitted = st.form_submit_button(
                "💾 Save Project" if is_edit_mode else "➕ Create Project", 
                type="primary",
                use_container_width=True
            )
        with col2:
            if st.form_submit_button("❌ Cancel", 
                                  type="secondary",
                                  use_container_width=True):
                st.session_state.show_project_form = False
                st.session_state.editing_project_id = None
                st.rerun()
        
        if submitted:
            errors = []
            if not name.strip():
                errors.append("Project name is required")
            elif not is_project_name_unique(name.strip(), st.session_state.editing_project_id if is_edit_mode else None):
                errors.append("Project name already exists")
            if end_date < start_date:
                errors.append("End date must be after start date")
            if budget < 0:
                errors.append("Budget cannot be negative")

            #
            if not errors:
                try:
                    if is_edit_mode:
                        # Get previous owner before update
                        previous_owner = query_db(
                            "SELECT user_id FROM projects WHERE id=?",
                            (st.session_state.editing_project_id,),
                            one=True
                        )
                        previous_owner_id = previous_owner[0] if previous_owner else None
                        
                        query_db("""
                            UPDATE projects SET
                                name=?, description=?, status=?,
                                start_date=?, end_date=?, user_id=?, budget=?
                            WHERE id=?
                        """, (
                            name.strip(), description, status,
                            start_date, end_date, manager_id, budget,
                            st.session_state.editing_project_id
                        ))
                        
                        # Check if owner changed
                        owner_changed = (previous_owner_id != manager_id) if previous_owner_id else False
                        
                        # Get new owner details for toast
                        new_owner = query_db(
                            "SELECT username FROM users WHERE id=?",
                            (manager_id,),
                            one=True
                        )
                        new_owner_name = new_owner[0] if new_owner else "Unknown"
                        
                        # Show toast notifications
                        if owner_changed:
                            st.toast(f"✉️ Ownership transferred to {new_owner_name}", icon="👤")
                            # Get previous owner name for toast
                            prev_owner = query_db(
                                "SELECT username FROM users WHERE id=?",
                                (previous_owner_id,),
                                one=True
                            )
                            prev_owner_name = prev_owner[0] if prev_owner else "Unknown"
                            st.toast(f"📬 CC notification sent to previous owner: {prev_owner_name}", icon="ℹ️")
                        else:
                            st.toast(f"✉️ Project update notification sent to owner: {new_owner_name}", icon="ℹ️")
                        
                        # Send email notification
                        if owner_changed or manager_id != st.session_state.user_id:
                            send_project_notification(
                                st.session_state.editing_project_id,
                                "update",
                                previous_owner_id if owner_changed else None
                            )
                        
                        st.success("Project updated successfully!")
                    else:
                        query_db("""
                            INSERT INTO projects (
                                name, description, status,
                                start_date, end_date, user_id, budget
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name.strip(), description, status,
                            start_date, end_date, manager_id, budget
                        ))
                        
                        # Get the newly created project ID
                        new_project = query_db(
                            "SELECT id FROM projects WHERE name=? ORDER BY id DESC LIMIT 1",
                            (name.strip(),),
                            one=True
                        )
                        
                        if new_project:
                            # Send notification to owner if different from creator
                            if manager_id != st.session_state.user_id:
                                send_project_notification(new_project[0], "create")
                            else:
                                # Show toast even if creator is owner
                                st.toast("✅ Project created successfully! You are the project owner.", icon="👑")
                        
                        st.success("Project created successfully!")
                    
                    st.session_state.show_project_form = False
                    st.session_state.editing_project_id = None
                    time.sleep(0.5)
                    st.rerun()
                
                except Exception as e:  # Proper exception handling
                    st.error(f"Database error: {str(e)}")
                    print(f"Error in project form submission: {str(e)}")


def is_project_name_unique(name, exclude_id=None):
    """Check if project name is unique (excluding current project if editing)"""
    if exclude_id:
        existing = query_db(
            "SELECT id FROM projects WHERE name = ? AND id != ?",
            (name.strip(), exclude_id),
            one=True
        )
    else:
        existing = query_db(
            "SELECT id FROM projects WHERE name = ?",
            (name.strip(),),
            one=True
        )
    return existing is None


# Email notification function
def send_task_assignment_email(assignee_email, task_title, project_name, deadline, assigner_name, parent_task=None):
    """
    Send email notification to assignee when a new task is assigned.
    """
    try:
        # Debug print (remove after testing)
        print(f"Attempting to send email to: {assignee_email}")
        


        # Email Configuration (using Streamlit secrets)
        SMTP_SERVER = st.secrets.get("email", {}).get("server", "smtp.gmail.com")
        SMTP_PORT = st.secrets.get("email", {}).get("port", 587)
        SENDER_EMAIL = st.secrets.get("email", {}).get("user", "your.email@gmail.com")
        SENDER_PASSWORD = st.secrets.get("email", {}).get("password", "your-app-password")

        
        # Validate email
        # Validate email
        if not assignee_email or "@" not in assignee_email:
            print("Invalid recipient email address")
            return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = assignee_email
        msg['Subject'] = f"New Assignment: {task_title}"
        
        # Email body with conditional parent task info
        parent_info = f"<p><strong>Parent Task:</strong> {parent_task}</p>" if parent_task else ""
        
        body = f"""
        <html>
            <body>
                <h2>You have been assigned a new task</h2>
                <p><strong>Task:</strong> {task_title}</p>
                {parent_info}
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Deadline:</strong> {deadline}</p>
                <p><strong>Assigned by:</strong> {assigner_name}</p>
                <br>
                <p>Please log in to the system to view and update this assignment.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("TLS started")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Logged in to SMTP server")
            server.send_message(msg)
            print("Email sent successfully")
            st.toast(f"Notification sent to {assignee_email}")
            
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        st.error(f"Failed to send email notification: {str(e)}")
        return False


def send_subtask_assignment_email(assignee_email, subtask_title, project_name, 
                                deadline, assigner_name, parent_task, subtask_url):
    """Send email notification for new subtask assignment"""
    try:
        # # Email configuration - REPLACE WITH YOUR ACTUAL CREDENTIALS
        # SMTP_SERVER = "smtp.gmail.com"
        # SMTP_PORT = 587
        # SMTP_USERNAME = "your_email@gmail.com"
        # SMTP_PASSWORD = "your_app_password"
        # SENDER_EMAIL = "your_email@gmail.com"

        # Email Configuration (using Streamlit secrets)
        SMTP_SERVER = st.secrets.get("email", {}).get("server", "smtp.gmail.com")
        SMTP_PORT = st.secrets.get("email", {}).get("port", 587)
        SENDER_EMAIL = st.secrets.get("email", {}).get("user", "your.email@gmail.com")
        SENDER_PASSWORD = st.secrets.get("email", {}).get("password", "your-app-password")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = assignee_email
        msg['Subject'] = f"New Subtask Assigned: {subtask_title}"
        
        # Email body with direct link
        body = f"""
        <html>
            <body>
                <h2>You have been assigned a new subtask</h2>
                <p><strong>Subtask:</strong> {subtask_title}</p>
                <p><strong>Parent Task:</strong> {parent_task}</p>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Deadline:</strong> {deadline}</p>
                <p><strong>Assigned by:</strong> {assigner_name}</p>
                <br>
                <p><a href="{subtask_url}" style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    border-radius: 5px;
                    font-weight: bold;
                ">View Subtask</a></p>
                <br>
                <p>Or copy this link: {subtask_url}</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # # Send email
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USERNAME, SMTP_PASSWORD)
        #     server.send_message(msg)


        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("TLS started")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Logged in to SMTP server")
            server.send_message(msg)
            print("Email sent successfully")
            st.toast(f"Notification sent to {assignee_email}")


            
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        st.error(f"Failed to send subtask assignment notification: {str(e)}")
        return False


# New email function for reassignments
def send_subtask_reassignment_email(new_assignee_email, previous_assignee_email, subtask_title, 
                                  project_name, deadline, assigner_name, parent_task, subtask_url):
    """
    Send email notification about subtask reassignment.
    """
    try:
        # # Email configuration - REPLACE WITH YOUR ACTUAL CREDENTIALS
        # SMTP_SERVER = "smtp.gmail.com"
        # SMTP_PORT = 587
        # SMTP_USERNAME = "your_email@gmail.com"
        # SMTP_PASSWORD = "your_app_password"
        # SENDER_EMAIL = "your_email@gmail.com"


        # Email Configuration (using Streamlit secrets)
        SMTP_SERVER = st.secrets.get("email", {}).get("server", "smtp.gmail.com")
        SMTP_PORT = st.secrets.get("email", {}).get("port", 587)
        SENDER_EMAIL = st.secrets.get("email", {}).get("user", "your.email@gmail.com")
        SENDER_PASSWORD = st.secrets.get("email", {}).get("password", "your-app-password")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = new_assignee_email
        if previous_assignee_email:
            msg['Cc'] = previous_assignee_email
        msg['Subject'] = f"Subtask Assigned to You: {subtask_title}"
        
        # Email body
        body = f"""
        <html>
            <body>
                <h2>You have been assigned a subtask</h2>
                <p><strong>Subtask:</strong> {subtask_title}</p>
                <p><strong>Parent Task:</strong> {parent_task}</p>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Deadline:</strong> {deadline}</p>
                <p><strong>Assigned by:</strong> {assigner_name}</p>
                <br>
                <p><a href="{subtask_url}" style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    border-radius: 5px;
                    font-weight: bold;
                ">View Subtask</a></p>
                <br>
                <p>Or copy this link: {subtask_url}</p>
                {'<p>Note: This subtask was previously assigned to someone else.</p>' if previous_assignee_email else ''}
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # # Send email
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USERNAME, SMTP_PASSWORD)
        #     server.send_message(msg)



        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("TLS started")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Logged in to SMTP server")
            server.send_message(msg)
            print("Email sent successfully")
            st.toast(f"Notification sent to {new_assignee_email}")
            
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        st.error(f"Failed to send reassignment notification: {str(e)}")
        return False


def send_task_reassignment_email(new_assignee_email, previous_assignee_email, task_title, 
                               project_name, deadline, assigner_name, task_url):
    """
    Send email notification about task reassignment.
    """
    try:
        # # Email configuration - REPLACE WITH YOUR ACTUAL CREDENTIALS
        # SMTP_SERVER = "smtp.gmail.com"
        # SMTP_PORT = 587
        # SMTP_USERNAME = "your_email@gmail.com"
        # SMTP_PASSWORD = "your_app_password"
        # SENDER_EMAIL = "your_email@gmail.com"

        # Email Configuration (using Streamlit secrets)
        SMTP_SERVER = st.secrets.get("email", {}).get("server", "smtp.gmail.com")
        SMTP_PORT = st.secrets.get("email", {}).get("port", 587)
        SENDER_EMAIL = st.secrets.get("email", {}).get("user", "your.email@gmail.com")
        SENDER_PASSWORD = st.secrets.get("email", {}).get("password", "your-app-password")


        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = new_assignee_email
        if previous_assignee_email:
            msg['Cc'] = previous_assignee_email
        msg['Subject'] = f"Task Assigned to You: {task_title}"
        
        # Email body
        # Email body with direct link
        body = f"""
        <html>
            <body>
                <h2>You have been assigned a task</h2>
                <p><strong>Task:</strong> {task_title}</p>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Deadline:</strong> {deadline}</p>
                <p><strong>Assigned by:</strong> {assigner_name}</p>
                <br>
                <p><a href="{task_url}" style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    border-radius: 5px;
                    font-weight: bold;
                ">View Task</a></p>
                <br>
                <p>Or copy this link: {task_url}</p>
                {'<p>Note: This task was previously assigned to someone else.</p>' if previous_assignee_email else ''}
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # # Send email
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USERNAME, SMTP_PASSWORD)
        #     server.send_message(msg)


        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("TLS started")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Logged in to SMTP server")
            server.send_message(msg)
            print("Email sent successfully")
            st.toast(f"Notification sent to {new_assignee_email}")

            
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        st.error(f"Failed to send reassignment notification: {str(e)}")
        return False


#send project email notification
def send_project_notification(project_id, action, previous_owner_id=None):
    """Send email notification about project changes and show toast"""
    try:
        # Get project details
        project = query_db("""
            SELECT p.name, p.description, p.start_date, p.end_date, p.budget,
                   u.email as owner_email, u.username as owner_name
            FROM projects p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (project_id,), one=True)
        
        if not project:
            print("Project not found")
            return False

        # Get previous owner details if changed
        previous_owner_email = None
        previous_owner_name = None
        if previous_owner_id:
            previous_owner = query_db("""
                SELECT email, username FROM users WHERE id = ?
            """, (previous_owner_id,), one=True)
            if previous_owner:
                previous_owner_email = previous_owner[0]
                previous_owner_name = previous_owner[1]

        # Get current user (who made the change)
        current_user = query_db("""
            SELECT username FROM users WHERE id = ?
        """, (st.session_state.user_id,), one=True)
        modifier_name = current_user[0] if current_user else "System"

        # Show toast notification for new projects
        # Show toast notifications
        if action == "create":
            st.toast(f"📬 Notification sent to project owner: {project[6]}", icon="✉️")
        elif action == "update":
            if previous_owner_id:
                # Get previous owner name for toast
                prev_owner = query_db(
                    "SELECT username FROM users WHERE id=?",
                    (previous_owner_id,),
                    one=True
                )
                prev_owner_name = prev_owner[0] if prev_owner else "Unknown"
                st.toast(f"📬 CC notification sent to previous owner: {prev_owner_name}", icon="ℹ️")
        
        
        # Email configuration
        SMTP_SERVER = st.secrets.get("email", {}).get("server", "smtp.gmail.com")
        SMTP_PORT = st.secrets.get("email", {}).get("port", 587)
        SENDER_EMAIL = st.secrets.get("email", {}).get("user", "your.email@gmail.com")
        SENDER_PASSWORD = st.secrets.get("email", {}).get("password", "your-app-password")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = project[5]  # owner_email
        
        if previous_owner_email:
            msg['Cc'] = previous_owner_email
        
        if action == "create":
            msg['Subject'] = f"New Project Created: {project[0]}"
        else:
            msg['Subject'] = f"Project Updated: {project[0]}"

        # Format dates
        start_date = datetime.strptime(project[2], "%Y-%m-%d").strftime("%b %d, %Y") if project[2] else "Not specified"
        end_date = datetime.strptime(project[3], "%Y-%m-%d").strftime("%b %d, %Y") if project[3] else "Not specified"
        budget = f"${float(project[4]):,.2f}" if project[4] is not None else "Not specified"

        # Email body
        body = f"""
        <html>
            <body>
                <h2>{'New Project Created' if action == 'create' else 'Project Updated'}</h2>
                <p><strong>Project:</strong> {project[0]}</p>
                <p><strong>Description:</strong> {project[1] or 'No description'}</p>
                <p><strong>Start Date:</strong> {start_date}</p>
                <p><strong>End Date:</strong> {end_date}</p>
                <p><strong>Budget:</strong> {budget}</p>
                <p><strong>Current Owner:</strong> {project[6]} ({project[5]})</p>
                {'<p><strong>Previous Owner:</strong> ' + previous_owner_name + ' (' + previous_owner_email + ')</p>' if previous_owner_email else ''}
                <p><strong>Created by:</strong> {modifier_name}</p>
                <br>
                <p>Please log in to the system to view this project.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print("Project notification email sent successfully")
            
        return True
        
    except Exception as e:
        print(f"Failed to send project notification: {str(e)}")
        st.error(f"Failed to send notification email: {str(e)}")
        return False





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



def update_parent_task_status(task_id):
    """Update parent task status based on subtasks' statuses"""
    subtasks = query_db("""
        SELECT status FROM subtasks 
        WHERE task_id = ?
    """, (task_id,))
    
    if not subtasks:
        return False  # No subtasks to check
        
    # Get current parent task status
    parent_task = query_db("SELECT status FROM tasks WHERE id = ?", (task_id,), one=True)
    current_status = parent_task[0] if parent_task else None
    
    # Check if all subtasks are completed
    all_completed = all(st[0] == "Completed" for st in subtasks)
    
    if all_completed:
        new_status = "Completed"
    else:
        # Get the most relevant incomplete status
        incomplete_statuses = [st[0] for st in subtasks if st[0] != "Completed"]
        # Priority: In Progress > Pending
        new_status = "In Progress" if "In Progress" in incomplete_statuses else "Pending"
    
    # Only update if status actually changed
    if new_status != current_status:
        query_db("""
            UPDATE tasks 
            SET status = ?
            WHERE id = ?
        """, (new_status, task_id))
        return True
        
    return False



#
def update_task_dates_based_on_subtasks(task_id):
    """Update task dates, time, and budget based on subtask data"""
    # Get all subtasks for this task
    subtasks = query_db("""
        SELECT start_date, deadline, actual_start_date, actual_deadline,
               time_spent, actual_time_spent, budget, actual_cost 
        FROM subtasks 
        WHERE task_id = ?
    """, (task_id,))
    
    if not subtasks:
        return None
    
    # Get current task data
    task = query_db("""
        SELECT start_date, deadline, actual_start_date, actual_deadline,
               time_spent, actual_time_spent, budget, actual_cost 
        FROM tasks 
        WHERE id = ?
    """, (task_id,), one=True)
    
    if not task:
        return None
    
    # Parse dates, times, and budgets
    task_start = pd.to_datetime(task[0]) if task[0] else None
    task_end = pd.to_datetime(task[1]) if task[1] else None
    task_actual_start = pd.to_datetime(task[2]) if task[2] else None
    task_actual_end = pd.to_datetime(task[3]) if task[3] else None
    task_time_spent = float(task[4]) if task[4] is not None else 0.0
    task_actual_time = float(task[5]) if task[5] is not None else 0.0
    task_budget = float(task[6]) if task[6] is not None else 0.0
    task_actual_cost = float(task[7]) if task[7] is not None else 0.0
    
    # Find min/max dates and sum times/budgets from subtasks
    subtask_starts = [pd.to_datetime(s[0]) for s in subtasks if s[0]]
    subtask_ends = [pd.to_datetime(s[1]) for s in subtasks if s[1]]
    subtask_actual_starts = [pd.to_datetime(s[2]) for s in subtasks if s[2]]
    subtask_actual_ends = [pd.to_datetime(s[3]) for s in subtasks if s[3]]
    subtask_times = [float(s[4]) for s in subtasks if s[4] is not None]
    subtask_actual_times = [float(s[5]) for s in subtasks if s[5] is not None]
    subtask_budgets = [float(s[6]) for s in subtasks if s[6] is not None]
    subtask_actual_costs = [float(s[7]) for s in subtasks if s[7] is not None]
    
    # Determine new dates
    new_start = min(subtask_starts) if subtask_starts and (task_start is None or min(subtask_starts) < task_start) else task_start
    new_end = max(subtask_ends) if subtask_ends and (task_end is None or max(subtask_ends) > task_end) else task_end
    new_actual_start = min(subtask_actual_starts) if subtask_actual_starts and (task_actual_start is None or min(subtask_actual_starts) < task_actual_start) else task_actual_start
    new_actual_end = max(subtask_actual_ends) if subtask_actual_ends and (task_actual_end is None or max(subtask_actual_ends) > task_actual_end) else task_actual_end
    
    # Calculate totals from subtasks
    total_subtask_time = sum(subtask_times) if subtask_times else 0.0
    total_subtask_actual_time = sum(subtask_actual_times) if subtask_actual_times else 0.0
    total_subtask_budget = sum(subtask_budgets) if subtask_budgets else 0.0
    total_subtask_actual_cost = sum(subtask_actual_costs) if subtask_actual_costs else 0.0
    
    # Calculate budget variance
    budget_variance = total_subtask_budget - total_subtask_actual_cost
    
    # Update task in database if any values changed
    if (new_start != task_start or new_end != task_end or 
        new_actual_start != task_actual_start or new_actual_end != task_actual_end or
        total_subtask_time != task_time_spent or total_subtask_actual_time != task_actual_time or
        total_subtask_budget != task_budget or total_subtask_actual_cost != task_actual_cost):
        
        query_db("""
            UPDATE tasks 
            SET start_date = ?, deadline = ?,
                actual_start_date = ?, actual_deadline = ?,
                time_spent = ?, actual_time_spent = ?,
                budget = ?, actual_cost = ?,
                budget_variance = ?
            WHERE id = ?
        """, (
            new_start.strftime('%Y-%m-%d') if new_start else None,
            new_end.strftime('%Y-%m-%d') if new_end else None,
            new_actual_start.strftime('%Y-%m-%d') if new_actual_start else None,
            new_actual_end.strftime('%Y-%m-%d') if new_actual_end else None,
            total_subtask_time,
            total_subtask_actual_time,
            total_subtask_budget,
            total_subtask_actual_cost,
            budget_variance,
            task_id
        ))
        
        return (new_start, new_end, new_actual_start, new_actual_end, 
                total_subtask_time, total_subtask_actual_time,
                total_subtask_budget, total_subtask_actual_cost, budget_variance)
    return None
 



#
def edit_task_in_workspace(task_id, project_id=None):
    """Professional edit task form with improved layout"""
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

    # Get previous assignee info before changes
    previous_assignee_id = task[10]  # assigned_to is at index 10
    previous_assignee_info = None
    if previous_assignee_id:
        previous_assignee_info = query_db(
            "SELECT email, username FROM users WHERE id = ?", 
            (previous_assignee_id,), 
            one=True
        )

    with st.container(border=True):
        st.subheader(f"✏️ Editing: {task[2]}", divider="blue")
        
        # Main form columns
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("**Basic Information**")
                title = st.text_input("Task Title*", value=task[2], key="task_title")
                description = st.text_area("Description", value=task[3] or "", height=100)
                
                status = st.selectbox(
                    "Status*",
                    options=["Pending", "In Progress", "Completed", "On Hold"],
                    index=["Pending", "In Progress", "Completed", "On Hold"].index(task[4]) 
                    if task[4] in ["Pending", "In Progress", "Completed", "On Hold"] else 0,
                    key="task_status"
                )
                
                priority = st.selectbox(
                    "Priority*",
                    options=["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(task[8]) 
                    if task[8] in ["High", "Medium", "Low"] else 1,
                    key="task_priority"
                )
                
                users = query_db("SELECT id, username FROM users ORDER BY username")
                current_assignee = task[-1] if task[-1] else "Unassigned"
                assignee_options = ["Unassigned"] + [user[1] for user in users]
                assignee = st.selectbox(
                    "Assignee",
                    options=assignee_options,
                    index=assignee_options.index(current_assignee) 
                    if current_assignee in assignee_options else 0,
                    key="task_assignee"
                )

        with col2:
            with st.container(border=True):
                st.markdown("**Time Tracking**")
                time_col1, time_col2 = st.columns(2)
                
                with time_col1:
                    planned_time = st.number_input(
                        "Planned Hours*",
                        min_value=0.0,
                        value=float(task[7]) if task[7] is not None and str(task[7]).replace('.', '', 1).isdigit() else 0.0,
                        step=0.5,
                        key="planned_time"
                    )
                    
                with time_col2:
                    actual_time = st.number_input(
                        "Actual Hours",
                        min_value=0.0,
                        value=float(task[17]) if len(task) > 17 and task[17] is not None and str(task[17]).replace('.', '', 1).isdigit() else 0.0,
                        step=0.5,
                        key="actual_time"
                    )
                
                st.markdown("**Dates**")
                date_col1, date_col2 = st.columns(2)
                
                with date_col1:
                    try:
                        start_date_value = datetime.strptime(str(task[11]), "%Y-%m-%d").date() if task[11] else datetime.now().date()
                    except:
                        start_date_value = datetime.now().date()
                    start_date = st.date_input("Start Date*", value=start_date_value, key="start_date")
                    
                    try:
                        actual_start_value = datetime.strptime(str(task[12]), "%Y-%m-%d").date() if task[12] else None
                    except:
                        actual_start_value = None
                    actual_start = st.date_input("Actual Start", value=actual_start_value, key="actual_start")
                    
                with date_col2:
                    try:
                        deadline_value = datetime.strptime(str(task[6]), "%Y-%m-%d").date() if task[6] else datetime.now().date() + timedelta(days=7)
                    except:
                        deadline_value = datetime.now().date() + timedelta(days=7)
                    deadline = st.date_input("Deadline*", value=deadline_value, key="deadline")
                    
                    try:
                        actual_deadline_value = datetime.strptime(str(task[13]), "%Y-%m-%d").date() if task[13] else None
                    except:
                        actual_deadline_value = None
                    actual_deadline = st.date_input("Actual Deadline", value=actual_deadline_value, key="actual_deadline")

        # Budget Section
        with st.container(border=True):
            st.markdown("**Budget Information**")
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
                        <strong>Original Budget:</strong> {formatted_original_budget}
                    </div>
                    """, unsafe_allow_html=True)
                
                budget = st.number_input(
                    "Update Budget ($)",
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

        # Notification Settings
        with st.container(border=True):
            st.markdown("**Notification Settings**")
            send_notification = st.checkbox(
                "Send email notifications for assignee changes",
                value=True,
                key=f"task_notify_{task_id}"
            )

        # Form actions
        st.divider()
        col1, col2, _ = st.columns([1,1,2])

        with col1:
            submitted = st.button("💾 Save Changes", type="primary", use_container_width=True)
        with col2:
            cancel_pressed = st.button("❌ Cancel", type="secondary", use_container_width=True)

        if cancel_pressed:
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            st.rerun()

        if submitted:
            # Get assignee ID from username
            new_assigned_to_id = None
            if assignee != "Unassigned":
                assignee_user = query_db("SELECT id FROM users WHERE username=?", (assignee,), one=True)
                new_assigned_to_id = assignee_user[0] if assignee_user else None
            
            # Check if assignee was changed
            assignee_changed = (new_assigned_to_id != previous_assignee_id)
            
            # Convert dates to strings for database
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            deadline_str = deadline.strftime("%Y-%m-%d") if deadline else None
            actual_start_str = actual_start.strftime("%Y-%m-%d") if actual_start else None
            actual_deadline_str = actual_deadline.strftime("%Y-%m-%d") if actual_deadline else None
            
            # Calculate budget variance
            budget_variance = float(budget) - float(actual_cost) if budget and actual_cost else None
            
            # Update the task in database
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
                priority, new_assigned_to_id, planned_time,
                start_date_str, deadline_str, actual_start_str,
                actual_deadline_str, budget, actual_cost,
                budget_variance, actual_time, task_id
            ))
            
            # Send notifications if enabled and assignee changed
            if send_notification and assignee_changed and new_assigned_to_id:
                # Generate task URL
                task_url = f"https://project-app-2025.streamlit.app/{task_id}"
                
                # Get new assignee info
                new_assignee_info = query_db(
                    "SELECT email, username FROM users WHERE id = ?", 
                    (new_assigned_to_id,), 
                    one=True
                )
                
                # Get current user info (assigner)
                assigner_info = query_db(
                    "SELECT username FROM users WHERE id = ?", 
                    (st.session_state.user_id,), 
                    one=True
                )
                
                if new_assignee_info:
                    send_task_reassignment_email(
                        new_assignee_email=new_assignee_info[0],
                        previous_assignee_email=previous_assignee_info[0] if previous_assignee_info else None,
                        task_title=title,
                        project_name=task[17] if task[17] else "Unknown Project",
                        deadline=deadline_str or "Not specified",
                        assigner_name=assigner_info[0] if assigner_info else "System",
                        task_url=task_url
                    )
            
            st.success("Task updated successfully!")
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            time.sleep(0.5)
            st.rerun()
    
    # ... [rest of your existing subtask management code] ...

    
    # Subtask Management Section
    st.divider()
    with st.container():
        st.subheader("📌 Subtask Management", divider="blue")
        
        # Initialize subtask form mode
        if 'subtask_form_mode' not in st.session_state:
            st.session_state.subtask_form_mode = None

        # Get all subtasks with full analytics data
        subtasks = query_db("""
            SELECT 
                s.id, s.title, s.description, s.status, 
                s.start_date, s.deadline, s.priority,
                s.assigned_to, s.budget, s.time_spent,
                u.username as assignee_name,
                s.actual_start_date, s.actual_deadline,
                s.actual_cost, s.actual_time_spent,
                t.title as parent_task
            FROM subtasks s
            LEFT JOIN users u ON s.assigned_to = u.id
            LEFT JOIN tasks t ON s.task_id = t.id
            WHERE s.task_id=?
            ORDER BY s.priority DESC, s.deadline ASC
        """, (task_id,))


        if subtasks:
            # Create comprehensive analytics DataFrame
            subtasks_df = pd.DataFrame(subtasks, columns=[
                "ID", "Subtask Title", "Description", "Status", "Start Date", "Deadline",
                "Priority", "Assigned To ID", "Budget", "Time Spent", "Assignee",
                "Actual Start", "Actual Deadline", "Actual Cost", "Actual Time Spent",
                "Parent Task"
            ])
            
            # Calculate metrics
            subtasks_df["Budget Variance"] = subtasks_df["Budget"] - subtasks_df["Actual Cost"]
            subtasks_df["Time Variance"] = subtasks_df["Time Spent"] - subtasks_df["Actual Time Spent"]
            
            # Format values professionally
            def format_currency(x):
                try:
                    return f"${float(x):,.2f}" if x is not None else "-"
                except:
                    return "-"
                    
            def format_hours(x):
                try:
                    return f"{float(x):.1f} hrs" if x is not None else "-"
                except:
                    return "-"
            
            currency_cols = ["Budget", "Actual Cost", "Budget Variance"]
            time_cols = ["Time Spent", "Actual Time Spent", "Time Variance"]
            
            for col in currency_cols:
                subtasks_df[col] = subtasks_df[col].apply(format_currency)
            
            for col in time_cols:
                subtasks_df[col] = subtasks_df[col].apply(format_hours)

            # Display analytics table with filters
            with st.expander(f"📊 Subtasks Analytics ({len(subtasks_df)})", expanded=True):
                # Add filters - now with dropdown for subtask title
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
                
                with filter_col1:
                    title_options = ["All Subtasks"] + sorted(subtasks_df["Subtask Title"].unique().tolist())
                    title_filter = st.selectbox(
                        "Filter by title",
                        options=title_options,
                        key="subtask_title_filter"
                    )
                
                with filter_col2:
                    status_filter = st.multiselect(
                        "Filter by status",
                        options=subtasks_df["Status"].unique(),
                        default=None,
                        key="subtask_status_filter"
                    )
                
                with filter_col3:
                    priority_filter = st.multiselect(
                        "Filter by priority",
                        options=subtasks_df["Priority"].unique(),
                        default=None,
                        key="subtask_priority_filter"
                    )
                
                with filter_col4:
                    assignee_filter = st.multiselect(
                        "Filter by assignee",
                        options=subtasks_df["Assignee"].unique(),
                        default=None,
                        key="subtask_assignee_filter"
                    )
                
                # Apply filters
                if title_filter and title_filter != "All Subtasks":
                    subtasks_df = subtasks_df[subtasks_df["Subtask Title"] == title_filter]
                if status_filter:
                    subtasks_df = subtasks_df[subtasks_df["Status"].isin(status_filter)]
                if priority_filter:
                    subtasks_df = subtasks_df[subtasks_df["Priority"].isin(priority_filter)]
                if assignee_filter:
                    subtasks_df = subtasks_df[subtasks_df["Assignee"].isin(assignee_filter)]
                
                # Display the table with all required columns
                st.dataframe(
                    subtasks_df[["Subtask Title", "Status", "Priority", "Assignee", 
                                "Start Date", "Deadline", "Actual Start", "Actual Deadline",
                                "Budget", "Actual Cost", "Budget Variance",
                                "Time Spent", "Actual Time Spent", "Time Variance"]],
                    column_config={
                        "Subtask Title": st.column_config.TextColumn("Subtask Title", width="medium"),
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Pending", "In Progress", "Completed"],
                            required=True
                        ),
                        "Priority": st.column_config.TextColumn("Priority"),
                        "Assignee": st.column_config.TextColumn("Assignee"),
                        "Start Date": st.column_config.DateColumn("Planned Start"),
                        "Deadline": st.column_config.DateColumn("Planned End"),
                        "Actual Start": st.column_config.DateColumn("Actual Start"),
                        "Actual Deadline": st.column_config.DateColumn("Actual End"),
                        "Budget": st.column_config.TextColumn("Budget"),
                        "Actual Cost": st.column_config.TextColumn("Actual Cost"),
                        "Budget Variance": st.column_config.TextColumn("Budget Variance"),
                        "Time Spent": st.column_config.TextColumn("Planned Time"),
                        "Actual Time Spent": st.column_config.TextColumn("Actual Time"),
                        "Time Variance": st.column_config.TextColumn("Time Variance")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=min(400, 35 + len(subtasks_df) * 35)
                )
                
                # Add download button
                csv = subtasks_df.to_csv(index=False).encode('utf-8')
                # Inside your subtasks analytics expander, replace the download button section with:
                button_col1, button_col2 = st.columns([1, 3])
                with button_col1:
                    st.download_button(
                        label="📥 Export as CSV",
                        data=csv,
                        file_name=f"subtasks_analytics_{task_id}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary",
                        key="export_subtasks_csv"
                    )
                with button_col2:
                    st.empty()  # Empty space for alignment

     

        # Subtask Actions
        # Subtask Actions
        with st.container(border=True):
            st.markdown("#### 🛠️ Subtask Actions")
            
            if subtasks:
                # Subtask selection
                selected_subtask = st.selectbox(
                    "Select subtask to manage:",
                    options=[f"{s[0]}: {s[1]}" for s in subtasks],
                    index=0,
                    key="subtask_selector",
                    label_visibility="collapsed"
                )
                
                subtask_id = int(selected_subtask.split(":")[0])
                subtask_data = next(s for s in subtasks if s[0] == subtask_id)
                
                # Action buttons
                cols = st.columns(3)
                with cols[0]:
                    if st.button("✏️ Edit Subtask", use_container_width=True):
                        st.session_state.subtask_form_mode = subtask_id
                        st.rerun()
                with cols[1]:
                    if st.button("📊 View Details", use_container_width=True):
                        with st.expander(f"Details for: {subtask_data[1]}", expanded=True):
                            st.write(f"**Description:** {subtask_data[2] or 'No description'}")
                            st.write(f"**Status:** {subtask_data[3]}")
                            st.write(f"**Priority:** {subtask_data[6]}")
                            st.write(f"**Assignee:** {subtask_data[10] or 'Unassigned'}")
                            st.write(f"**Planned Dates:** {subtask_data[4]} to {subtask_data[5]}")
                            if subtask_data[11] and subtask_data[12]:
                                st.write(f"**Actual Dates:** {subtask_data[11]} to {subtask_data[12]}")
                            st.write(f"**Budget:** ${float(subtask_data[8]):,.2f}" if subtask_data[8] else "**Budget:** Not set")
                            st.write(f"**Actual Cost:** ${float(subtask_data[13]):,.2f}" if subtask_data[13] else "**Actual Cost:** Not set")
                with cols[2]:
                    if st.button("🗑️ Delete Subtask", type="secondary", use_container_width=True):
                        st.session_state.subtask_to_delete = subtask_id
                
                # Delete confirmation
                if 'subtask_to_delete' in st.session_state and st.session_state.subtask_to_delete == subtask_id:
                    st.warning("Are you sure you want to delete this subtask?")
                    confirm_cols = st.columns(2)
                    with confirm_cols[0]:
                        if st.button("✅ Confirm Delete", key="confirm_subtask_delete"):
                            query_db("DELETE FROM subtasks WHERE id=?", (subtask_id,))
                            st.success("Subtask deleted successfully!")
                            update_task_dates_based_on_subtasks(task_id)
                            del st.session_state.subtask_to_delete
                            time.sleep(0.5)
                            st.rerun()
                    with confirm_cols[1]:
                        if st.button("❌ Cancel", key="cancel_subtask_delete"):
                            del st.session_state.subtask_to_delete
                            st.rerun()
            
            # Create new subtask button
            if st.button("➕ Create New Subtask", 
                        use_container_width=True,
                        key="create_subtask_btn"):
                st.session_state.subtask_form_mode = 'create'
                st.rerun()

        # Subtask Form (appears when in create/edit mode)
        if st.session_state.subtask_form_mode:
            is_edit_mode = st.session_state.subtask_form_mode != 'create'
            
            if is_edit_mode:
                subtask = next((s for s in subtasks if s[0] == st.session_state.subtask_form_mode), None)
                if not subtask:
                    st.error("Subtask not found")
                    st.session_state.subtask_form_mode = None
                    st.rerun()
                
                # Get previous assignee info
                previous_assignee_id = subtask[7]  # assigned_to is at index 7
                previous_assignee_info = None
                if previous_assignee_id:
                    previous_assignee_info = query_db(
                        "SELECT email, username FROM users WHERE id = ?", 
                        (previous_assignee_id,), 
                        one=True
                    )

            with st.container(border=True):
                if is_edit_mode:
                    form_title = f"✏️ Edit Subtask: {subtask[1]}"
                    default_values = {
                        'title': subtask[1],
                        'description': subtask[2] or "",
                        'status': subtask[3],
                        'priority': subtask[6],
                        'start_date': datetime.strptime(subtask[4], "%Y-%m-%d").date() if subtask[4] else None,
                        'deadline': datetime.strptime(subtask[5], "%Y-%m-%d").date() if subtask[5] else None,
                        'budget': float(subtask[8]) if subtask[8] else 0.0,
                        'time_spent': float(subtask[9]) if subtask[9] else 0.0,
                        'assignee': subtask[10] or "Unassigned",  # Fixed: Use assignee_name from query
                        'actual_start': datetime.strptime(subtask[11], "%Y-%m-%d").date() if subtask[11] else None,
                        'actual_deadline': datetime.strptime(subtask[12], "%Y-%m-%d").date() if subtask[12] else None,
                        'actual_cost': float(subtask[13]) if subtask[13] else 0.0,
                        'actual_time': float(subtask[14]) if subtask[14] else 0.0
                    }
                else:
                    form_title = "🆕 Create New Subtask"
                    default_values = {
                        'title': "",
                        'description': "",
                        'status': "Pending",
                        'priority': "Medium",
                        'start_date': None,
                        'deadline': None,
                        'budget': 0.0,
                        'time_spent': 0.0,
                        'assignee': "Unassigned",
                        'actual_start': None,
                        'actual_deadline': None,
                        'actual_cost': 0.0,
                        'actual_time': 0.0
                    }

                st.subheader(form_title, divider="blue")
                
                with st.form(key="subtask_form", clear_on_submit=not is_edit_mode):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        with st.container(border=True):
                            st.markdown("**Basic Information**")
                            subtask_title = st.text_input("Title*", value=default_values['title'])
                            subtask_description = st.text_area("Description", value=default_values['description'], height=100)
                            
                            status = st.selectbox(
                                "Status*",
                                options=["Pending", "In Progress", "Completed"],
                                index=["Pending", "In Progress", "Completed"].index(default_values['status'])
                            )
                            
                            priority = st.selectbox(
                                "Priority*",
                                options=["High", "Medium", "Low"],
                                index=["High", "Medium", "Low"].index(default_values['priority'])
                            )
                            
                            # Fixed: Proper user selection with correct default
                            team_members = query_db("SELECT id, username FROM users ORDER BY username")
                            assignee_options = ["Unassigned"] + [member[1] for member in team_members]
                            assignee = st.selectbox(
                                "Assignee",
                                options=assignee_options,
                                index=assignee_options.index(default_values['assignee']) if default_values['assignee'] in assignee_options else 0
                            )
                    
                    with col2:
                        with st.container(border=True):
                            st.markdown("**Time Tracking**")
                            time_col1, time_col2 = st.columns(2)
                            with time_col1:
                                time_spent = st.number_input(
                                    "Planned Hours*",
                                    min_value=0.0,
                                    value=default_values['time_spent'],
                                    step=0.5
                                )
                            with time_col2:
                                actual_time = st.number_input(
                                    "Actual Hours",
                                    min_value=0.0,
                                    value=default_values['actual_time'],
                                    step=0.5
                                )
                            
                            st.markdown("**Dates**")
                            date_col1, date_col2 = st.columns(2)
                            with date_col1:
                                start_date = st.date_input(
                                    "Start Date*", 
                                    value=default_values['start_date'] or datetime.now().date()
                                )
                                actual_start = st.date_input(
                                    "Actual Start",
                                    value=default_values['actual_start']
                                )
                            with date_col2:
                                deadline = st.date_input(
                                    "Deadline*", 
                                    value=default_values['deadline'] or (datetime.now().date() + timedelta(days=7))
                                )
                                actual_deadline = st.date_input(
                                    "Actual Deadline",
                                    value=default_values['actual_deadline']
                                )
                    
                    # Budget Section
                    with st.container(border=True):
                        st.markdown("**Budget Information**")
                        budget_col1, budget_col2 = st.columns(2)
                        with budget_col1:
                            budget = st.number_input(
                                "Budget ($)",
                                min_value=0.0,
                                value=default_values['budget'],
                                step=0.01
                            )
                        with budget_col2:
                            actual_cost = st.number_input(
                                "Actual Cost ($)",
                                min_value=0.0,
                                value=default_values['actual_cost'],
                                step=0.01
                            )
                    
                    # Notification Settings
                    with st.container(border=True):
                        st.markdown("**Notification Settings**")
                        send_notification = st.checkbox(
                            "Send email notifications",
                            value=True,
                            key=f"subtask_notify_{st.session_state.subtask_form_mode}"
                        )
                    
                    # Form actions
                    st.divider()
                    col1, col2, _ = st.columns([1,1,2])
                    with col1:
                        submit_label = "💾 Save Changes" if is_edit_mode else "➕ Create Subtask"
                        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)
                    with col2:
                        if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                            st.session_state.subtask_form_mode = None
                            st.rerun()
                    
                    if submitted:
                        if not subtask_title.strip():
                            st.error("Subtask title is required")
                        elif deadline < start_date:
                            st.error("Deadline must be on or after the start date")
                        else:
                            assigned_to_id = None
                            if assignee != "Unassigned":
                                assigned_to = query_db(
                                    "SELECT id FROM users WHERE username = ?", 
                                    (assignee,), 
                                    one=True
                                )
                                if assigned_to:
                                    assigned_to_id = assigned_to[0]
                            
                            # Generate subtask URL
                            subtask_url = f"https://project-app-2025.streamlit.app/{task_id}/subtask/{st.session_state.subtask_form_mode if is_edit_mode else 'new'}"
                            
                            if is_edit_mode:
                                # Check if assignee was changed
                                assignee_changed = (assigned_to_id != previous_assignee_id)
                                
                                query_db("""
                                    UPDATE subtasks SET
                                        title=?, description=?, status=?, 
                                        start_date=?, deadline=?, priority=?,
                                        assigned_to=?, budget=?, time_spent=?,
                                        actual_start_date=?, actual_deadline=?,
                                        actual_cost=?, actual_time_spent=?
                                    WHERE id=?
                                """, (
                                    subtask_title.strip(), subtask_description, status,
                                    start_date, deadline, priority,
                                    assigned_to_id, budget, time_spent,
                                    actual_start, actual_deadline,
                                    actual_cost, actual_time,
                                    st.session_state.subtask_form_mode
                                ))
                                
                                # Send notification if assignee changed
                                if send_notification and assignee_changed and assigned_to_id:
                                    parent_task = query_db("""
                                        SELECT t.title, p.name, u.username 
                                        FROM tasks t
                                        JOIN projects p ON t.project_id = p.id
                                        LEFT JOIN users u ON p.user_id = u.id
                                        WHERE t.id = ?
                                    """, (task_id,), one=True)
                                    
                                    new_assignee_info = query_db(
                                        "SELECT email, username FROM users WHERE id = ?", 
                                        (assigned_to_id,), 
                                        one=True
                                    )
                                    
                                    if new_assignee_info:
                                        send_subtask_reassignment_email(
                                            new_assignee_email=new_assignee_info[0],
                                            previous_assignee_email=previous_assignee_info[0] if previous_assignee_info else None,
                                            subtask_title=subtask_title.strip(),
                                            project_name=parent_task[1] if parent_task else "Unknown Project",
                                            deadline=deadline.strftime('%Y-%m-%d') if deadline else "Not specified",
                                            assigner_name=st.session_state.get('username', 'System'),
                                            parent_task=parent_task[0] if parent_task else "Unknown Task",
                                            subtask_url=subtask_url
                                        )
                                
                                st.success("Subtask updated successfully!")
                            else:
                                # For new subtasks, always send notification if assigned
                                query_db("""
                                    INSERT INTO subtasks (
                                        task_id, title, description, status,
                                        start_date, deadline, priority, assigned_to,
                                        budget, time_spent, actual_start_date,
                                        actual_deadline, actual_cost, actual_time_spent
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    task_id, subtask_title.strip(), subtask_description, status,
                                    start_date, deadline, priority, assigned_to_id,
                                    budget, time_spent, actual_start,
                                    actual_deadline, actual_cost, actual_time
                                ))
                                
                                # Send notification for new subtask if assigned
                                if send_notification and assigned_to_id:
                                    parent_task = query_db("""
                                        SELECT t.title, p.name, u.username 
                                        FROM tasks t
                                        JOIN projects p ON t.project_id = p.id
                                        LEFT JOIN users u ON p.user_id = u.id
                                        WHERE t.id = ?
                                    """, (task_id,), one=True)
                                    
                                    new_assignee_info = query_db(
                                        "SELECT email, username FROM users WHERE id = ?", 
                                        (assigned_to_id,), 
                                        one=True
                                    )
                                    
                                    if new_assignee_info:
                                        send_subtask_assignment_email(
                                            assignee_email=new_assignee_info[0],
                                            subtask_title=subtask_title.strip(),
                                            project_name=parent_task[1] if parent_task else "Unknown Project",
                                            deadline=deadline.strftime('%Y-%m-%d') if deadline else "Not specified",
                                            assigner_name=st.session_state.get('username', 'System'),
                                            parent_task=parent_task[0] if parent_task else "Unknown Task",
                                            subtask_url=subtask_url
                                        )
                                
                                st.success("Subtask created successfully!")
                            
                            update_task_dates_based_on_subtasks(task_id)
                            st.session_state.subtask_form_mode = None
                            time.sleep(0.5)
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
        #
        st.markdown("---")
        btn_col1, btn_col2, _ = st.columns([1,1,3])
        with btn_col1:
            submit_label = "💾 Save" if edit_mode else "➕ Create"
            submitted = st.form_submit_button(submit_label, type="primary")
        with btn_col2:
            # Change this line - use a separate variable for cancelled
            cancelled = st.form_submit_button("❌ Cancel", type="secondary")

        # Handle form submissions
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
                    # Create new task
                    # In the render_task_form function, modify the task creation section:
                    if not edit_mode:
                        # Create new task
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
                        
                        # Debug print
                        print(f"New task created. Assigned to user ID: {assigned_to}")
                        
                        if assigned_to:
                            assignee = query_db("SELECT email, username FROM users WHERE id=?", (assigned_to,), one=True)
                            if assignee:
                                assignee_email, assignee_name = assignee
                                print(f"Assignee found: {assignee_name} ({assignee_email})")
                                
                                # Get assigner name
                                assigner = query_db("SELECT username FROM users WHERE id=?", (st.session_state.user_id,), one=True)
                                assigner_name = assigner[0] if assigner else "System"
                                
                                # Get project name
                                project = query_db("SELECT name FROM projects WHERE id=?", (project_id,), one=True)
                                project_name = project[0] if project else "Unknown Project"
                                
                                print(f"Sending email to {assignee_email} about task '{new_title}'")
                                
                                # Send email notification
                                if send_task_assignment_email(
                                    assignee_email=assignee_email,
                                    task_title=new_title,
                                    project_name=project_name,
                                    deadline=deadline_str or "Not specified",
                                    assigner_name=assigner_name
                                ):
                                    print("Email notification sent successfully")
                                else:
                                    print("Email notification failed")
                            else:
                                print("No assignee information found")
                        else:
                            print("No assignee specified for this task")


                st.session_state.show_task_form = False
                st.session_state.editing_task_id = None
                st.rerun()
                
        # Explicitly handle cancellation
        if cancelled:
            st.session_state.show_task_form = False
            st.session_state.editing_task_id = None
            st.rerun()



def workspace_page():
    
    # Add Project Management section (only visible to admins/managers)
    # ======= Project Management Section =======
    st.markdown("---")
    st.subheader("📋 Project Management")

    # Different layouts for admin vs other users
    if st.session_state.user_role == "Admin":
        # Admin view - full controls
        cols = st.columns([2, 1, 1, 1])
        
        with cols[0]:
            # Project selection dropdown
            projects = query_db("SELECT id, name FROM projects ORDER BY name")
            project_options = {p[0]: p[1] for p in projects} if projects else {}
            selected_project_id = st.selectbox(
                "Select Project",
                options=list(project_options.keys()),
                format_func=lambda x: project_options[x],
                key="project_edit_select"
            )
        
        with cols[1]:
            if st.button("➕ Create New", use_container_width=True):
                st.session_state.show_project_form = True
                st.session_state.editing_project_id = None
                st.rerun()
        
        with cols[2]:
            if st.button("✏️ Edit", use_container_width=True, 
                    disabled=not selected_project_id):
                if selected_project_id:
                    st.session_state.show_project_form = True
                    st.session_state.editing_project_id = selected_project_id
                    st.rerun()
        
        with cols[3]:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True,
                    disabled=not selected_project_id):
                st.session_state.project_to_delete = selected_project_id
        
        # Delete confirmation
        if 'project_to_delete' in st.session_state:
            st.warning("Are you sure you want to delete this project and all its tasks?")
            confirm_cols = st.columns([1,1,2])
            with confirm_cols[0]:
                if st.button("✅ Confirm", type="primary", use_container_width=True):
                    query_db("DELETE FROM tasks WHERE project_id=?", (st.session_state.project_to_delete,))
                    query_db("DELETE FROM project_team WHERE project_id=?", (st.session_state.project_to_delete,))
                    query_db("DELETE FROM projects WHERE id=?", (st.session_state.project_to_delete,))
                    st.success("Project deleted successfully!")
                    del st.session_state.project_to_delete
                    time.sleep(0.5)
                    st.rerun()
            with confirm_cols[1]:
                if st.button("❌ Cancel", type="secondary", use_container_width=True):
                    del st.session_state.project_to_delete
                    st.rerun()

    else:
        # Non-admin view - simplified interface
        cols = st.columns([1,1,2])
        
        with cols[0]:
            st.button("➕ Create New", 
                    use_container_width=True,
                    disabled=True,
                    help="Only administrators can create projects")
        
        with cols[1]:
            st.button("✏️ Edit", 
                    use_container_width=True,
                    disabled=True,
                    help="Only administrators can edit projects")

    # Show project form if in create/edit mode
    if st.session_state.get('show_project_form'):
        # [Keep the existing render_project_form() implementation from previous code]
        render_project_form()

    # ======= Project Analytics Section =======
    # [Previous project analytics code goes here...]



    # Add Project Analytics section (visible to all users)
    st.markdown("---")
    st.subheader("📊 Project Analytics")

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
    st.subheader("Project Analytics Summary")

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
                    # Add Task Selection Dropdown
                    # Create options with title and priority for all tasks
                    task_options = {task[0]: f"{task[1]} ({task[4]})" for task in tasks}
                    
                    # Add default "View all tasks" option
                    task_options = {None: "View all tasks"} | task_options
                    
                    selected_task_id = st.selectbox(
                        "Filter Tasks",
                        options=list(task_options.keys()),
                        format_func=lambda x: task_options[x],
                        key="task_selection_dropdown"
                    )
                    
                    # Filter tasks based on selection
                    display_tasks = tasks if selected_task_id is None else [t for t in tasks if t[0] == selected_task_id]

                    # Create rows of 3 tasks each (will show either all tasks or just the selected one)
                    for i in range(0, len(display_tasks), 3):
                        row_tasks = display_tasks[i:i+3]
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
                                            <div style="margin-bottom: 4px;">⏳ <strong>Status:</strong> {status}</div>
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


                

                # Add Task Analytics Table Section
                # Task Analytics Section
                st.markdown("---")
                st.subheader("📊 Task Analytics")

                # Get all tasks for the selected project with additional details
                tasks_for_analytics = query_db("""
                    SELECT 
                        t.id, 
                        t.title, 
                        t.status, 
                        t.priority,
                        t.start_date,
                        t.deadline,
                        t.actual_start_date,
                        t.actual_deadline,
                        t.budget,
                        t.actual_cost,
                        t.time_spent,
                        t.actual_time_spent,
                        u.username as assignee,
                        p.name as project_name
                    FROM tasks t
                    LEFT JOIN users u ON t.assigned_to = u.id
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.project_id = ?
                    ORDER BY t.priority DESC, t.deadline ASC
                """, (selected_project_id,))

                if tasks_for_analytics:
                    # Convert to DataFrame
                    analytics_df = pd.DataFrame(tasks_for_analytics, columns=[
                        "ID", "Title", "Status", "Priority", 
                        "Start Date", "Deadline", "Actual Start", "Actual Deadline",
                        "Budget", "Actual Cost", "Planned Time", "Actual Time",
                        "Assignee", "Project"
                    ])
                    
                    # Calculate additional metrics
                    analytics_df["Budget Variance"] = analytics_df["Budget"] - analytics_df["Actual Cost"]
                    analytics_df["Time Variance"] = analytics_df["Planned Time"] - analytics_df["Actual Time"]
                    
                    # Format numeric columns
                    analytics_df["Budget"] = analytics_df["Budget"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "-")
                    analytics_df["Actual Cost"] = analytics_df["Actual Cost"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "-")
                    analytics_df["Budget Variance"] = analytics_df["Budget Variance"].apply(
                        lambda x: f"${x:,.2f}" if pd.notnull(x) else "-"
                    )
                    analytics_df["Planned Time"] = analytics_df["Planned Time"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    analytics_df["Actual Time"] = analytics_df["Actual Time"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    analytics_df["Time Variance"] = analytics_df["Time Variance"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    
                    # Add filters
                    with st.expander("🔍 Filter Tasks", expanded=True):
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        # Title filter dropdown
                        with col1:
                            # Get all unique task titles for the dropdown
                            title_options = ["All Tasks"] + sorted(analytics_df["Title"].unique().tolist())
                            
                            title_filter = st.selectbox(
                                "Filter by Title",
                                options=title_options,
                                key="title_filter"
                            )
                        
                        with col2:
                            status_filter = st.multiselect(
                                "Filter by Status",
                                options=analytics_df["Status"].unique(),
                                default=None,
                                key="status_filter"
                            )
                        
                        with col3:
                            priority_filter = st.multiselect(
                                "Filter by Priority",
                                options=analytics_df["Priority"].unique(),
                                default=None,
                                key="priority_filter"
                            )
                        
                        with col4:
                            assignee_filter = st.multiselect(
                                "Filter by Assignee",
                                options=analytics_df["Assignee"].unique(),
                                default=None,
                                key="assignee_filter"
                            )
                        
                        with col5:
                            date_filter = st.selectbox(
                                "Filter by Date Range",
                                options=["All", "Upcoming", "Overdue", "Completed"],
                                key="date_filter"
                            )
                    
                    # Apply filters
                    if title_filter and title_filter != "All Tasks":
                        analytics_df = analytics_df[analytics_df["Title"] == title_filter]
                    
                    if status_filter:
                        analytics_df = analytics_df[analytics_df["Status"].isin(status_filter)]
                    if priority_filter:
                        analytics_df = analytics_df[analytics_df["Priority"].isin(priority_filter)]
                    if assignee_filter:
                        analytics_df = analytics_df[analytics_df["Assignee"].isin(assignee_filter)]

                    if date_filter == "Upcoming":
                        today = pd.Timestamp.now().date()
                        analytics_df = analytics_df[
                            (pd.to_datetime(analytics_df["Deadline"]).dt.date >= today) & 
                            (analytics_df["Status"] != "Completed")
                        ]
                    elif date_filter == "Overdue":
                        today = pd.Timestamp.now().date()
                        analytics_df = analytics_df[
                            (pd.to_datetime(analytics_df["Deadline"]).dt.date < today) & 
                            (analytics_df["Status"] != "Completed")
                        ]
                    elif date_filter == "Completed":
                        analytics_df = analytics_df[analytics_df["Status"] == "Completed"]
                    
                    # Display the table
                    st.dataframe(
                        analytics_df,
                        column_config={
                            "ID": st.column_config.NumberColumn("ID"),
                            "Title": st.column_config.TextColumn("Title"),
                            "Status": st.column_config.TextColumn("Status"),
                            "Priority": st.column_config.TextColumn("Priority"),
                            "Start Date": st.column_config.DateColumn("Start Date"),
                            "Deadline": st.column_config.DateColumn("Deadline"),
                            "Actual Start": st.column_config.DateColumn("Actual Start"),
                            "Actual Deadline": st.column_config.DateColumn("Actual Deadline"),
                            "Budget": st.column_config.TextColumn("Budget"),
                            "Actual Cost": st.column_config.TextColumn("Actual Cost"),
                            "Budget Variance": st.column_config.TextColumn("Budget Variance"),
                            "Planned Time": st.column_config.TextColumn("Planned Time"),
                            "Actual Time": st.column_config.TextColumn("Actual Time"),
                            "Time Variance": st.column_config.TextColumn("Time Variance"),
                            "Assignee": st.column_config.TextColumn("Assignee"),
                            "Project": st.column_config.TextColumn("Project")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Add download button
                    csv = analytics_df.to_csv(index=False).encode('utf-8')
                    
                    # Get current project name for filename
                    current_project = query_db("SELECT name FROM projects WHERE id = ?", (selected_project_id,), one=True)
                    project_name = current_project[0] if current_project else "project_tasks"
                    
                    # Clean project name for filename
                    clean_project_name = "".join(c if c.isalnum() else "_" for c in project_name)
                    
                    st.download_button(
                        label="📥 Download Filtered Data as CSV",
                        data=csv,
                        file_name=f"{clean_project_name}_task_analytics.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No tasks found for analytics")


                # Subtask Analytics Section
                st.markdown("---")
                st.subheader("📊 Subtask Analytics")

                # Get all subtasks for the selected project with additional details
                subtasks_for_analytics = query_db("""
                    SELECT 
                        s.id,
                        s.title,
                        t.title as parent_task,
                        s.status,
                        s.priority,
                        s.start_date,
                        s.deadline,
                        s.actual_start_date,
                        s.actual_deadline,
                        s.budget,
                        s.actual_cost,
                        s.time_spent,
                        s.actual_time_spent,
                        u.username as assignee,
                        p.name as project_name
                    FROM subtasks s
                    JOIN tasks t ON s.task_id = t.id
                    LEFT JOIN users u ON s.assigned_to = u.id
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.project_id = ?
                    ORDER BY s.priority DESC, s.deadline ASC
                """, (selected_project_id,))

                if subtasks_for_analytics:
                    # Convert to DataFrame
                    subtask_df = pd.DataFrame(subtasks_for_analytics, columns=[
                        "ID", "Title", "Parent Task", "Status", "Priority",
                        "Start Date", "Deadline", "Actual Start", "Actual Deadline",
                        "Budget", "Actual Cost", "Planned Time", "Actual Time",
                        "Assignee", "Project"
                    ])
                    
                    # Calculate additional metrics
                    subtask_df["Budget Variance"] = subtask_df["Budget"] - subtask_df["Actual Cost"]
                    subtask_df["Time Variance"] = subtask_df["Planned Time"] - subtask_df["Actual Time"]
                    
                    # Format numeric columns
                    subtask_df["Budget"] = subtask_df["Budget"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "-")
                    subtask_df["Actual Cost"] = subtask_df["Actual Cost"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "-")
                    subtask_df["Budget Variance"] = subtask_df["Budget Variance"].apply(
                        lambda x: f"${x:,.2f}" if pd.notnull(x) else "-"
                    )
                    subtask_df["Planned Time"] = subtask_df["Planned Time"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    subtask_df["Actual Time"] = subtask_df["Actual Time"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    subtask_df["Time Variance"] = subtask_df["Time Variance"].apply(
                        lambda x: f"{x:.1f} hrs" if pd.notnull(x) else "-"
                    )
                    
                    # Add filters
                    with st.expander("🔍 Filter Subtasks", expanded=True):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            subtask_status_filter = st.multiselect(
                                "Filter by Status",
                                options=subtask_df["Status"].unique(),
                                default=None,
                                key="subtask_status_filter"
                            )
                        
                        with col2:
                            subtask_priority_filter = st.multiselect(
                                "Filter by Priority",
                                options=subtask_df["Priority"].unique(),
                                default=None,
                                key="subtask_priority_filter"
                            )
                        
                        with col3:
                            subtask_assignee_filter = st.multiselect(
                                "Filter by Assignee",
                                options=subtask_df["Assignee"].unique(),
                                default=None,
                                key="subtask_assignee_filter"
                            )
                        
                        with col4:
                            subtask_parent_filter = st.multiselect(
                                "Filter by Parent Task",
                                options=subtask_df["Parent Task"].unique(),
                                default=None,
                                key="subtask_parent_filter"
                            )
                    
                    # Apply filters
                    if subtask_status_filter:
                        subtask_df = subtask_df[subtask_df["Status"].isin(subtask_status_filter)]
                    if subtask_priority_filter:
                        subtask_df = subtask_df[subtask_df["Priority"].isin(subtask_priority_filter)]
                    if subtask_assignee_filter:
                        subtask_df = subtask_df[subtask_df["Assignee"].isin(subtask_assignee_filter)]
                    if subtask_parent_filter:
                        subtask_df = subtask_df[subtask_df["Parent Task"].isin(subtask_parent_filter)]
                    
                    # Display the table
                    st.dataframe(
                        subtask_df,
                        column_config={
                            "ID": st.column_config.NumberColumn("Subtask ID"),
                            "Title": st.column_config.TextColumn("Subtask Title"),
                            "Parent Task": st.column_config.TextColumn("Parent Task"),
                            "Status": st.column_config.TextColumn("Status"),
                            "Priority": st.column_config.TextColumn("Priority"),
                            "Start Date": st.column_config.DateColumn("Start Date"),
                            "Deadline": st.column_config.DateColumn("Deadline"),
                            "Actual Start": st.column_config.DateColumn("Actual Start"),
                            "Actual Deadline": st.column_config.DateColumn("Actual Deadline"),
                            "Budget": st.column_config.TextColumn("Budget"),
                            "Actual Cost": st.column_config.TextColumn("Actual Cost"),
                            "Budget Variance": st.column_config.TextColumn("Budget Variance"),
                            "Planned Time": st.column_config.TextColumn("Planned Time"),
                            "Actual Time": st.column_config.TextColumn("Actual Time"),
                            "Time Variance": st.column_config.TextColumn("Time Variance"),
                            "Assignee": st.column_config.TextColumn("Assignee"),
                            "Project": st.column_config.TextColumn("Project")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Add download button
                    csv = subtask_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Subtask Data as CSV",
                        data=csv,
                        file_name=f"{project_options[selected_project_id][0]}_subtask_analytics.csv",
                        mime="text/csv",
                        key="download_subtasks"
                    )
                else:
                    st.info("No subtasks found for analytics")






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
                            # Check if task should be marked completed based on subtasks
                            if task[3] != "Completed":  # Only check if not already completed
                                if update_parent_task_status(task[0]):
                                    st.rerun()

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
                st.write("### Project Timeline (Gantt Chart)")
                
                # Get project name for analytics
                project_name = query_db("SELECT name FROM projects WHERE id = ?", (selected_project_id,), one=True)[0]
                
                # Color scheme definitions
                task_colors = {
                    "High": "#FF6B6B",    # Red for high priority
                    "Medium": "#FFD166",  # Yellow for medium priority
                    "Low": "#06D6A0"      # Green for low priority
                }
                
                subtask_colors = {
                    "High": "#FF9E9E",    # Lighter red
                    "Medium": "#FFE08A",   # Lighter yellow
                    "Low": "#7CE8C9"      # Lighter green
                }

                # Get all tasks with their subtasks
                tasks_data = query_db("""
                    SELECT 
                        t.id as task_id, 
                        t.title as task_title,
                        t.start_date as task_start,
                        t.deadline as task_end,
                        t.status as task_status,
                        t.priority as task_priority,
                        u1.username as task_assignee,
                        t.actual_start_date,
                        t.actual_deadline
                    FROM tasks t
                    LEFT JOIN users u1 ON t.assigned_to = u1.id
                    WHERE t.project_id = ?
                    ORDER BY 
                        CASE WHEN t.start_date IS NULL THEN 1 ELSE 0 END,
                        t.start_date ASC,
                        t.id
                """, (selected_project_id,))
                
                # Get all subtasks for these tasks
                subtasks_data = query_db("""
                    SELECT 
                        s.task_id,
                        t.title as task_title,
                        s.id as subtask_id,
                        s.title as subtask_title,
                        s.start_date as subtask_start,
                        s.deadline as subtask_end,
                        s.status as subtask_status,
                        s.priority as subtask_priority,
                        u2.username as subtask_assignee,
                        s.budget as subtask_budget,
                        s.time_spent as subtask_time_spent,
                        s.actual_start_date,
                        s.actual_deadline
                    FROM subtasks s
                    JOIN tasks t ON s.task_id = t.id
                    LEFT JOIN users u2 ON s.assigned_to = u2.id
                    WHERE s.task_id IN (
                        SELECT id FROM tasks WHERE project_id = ?
                    )
                    ORDER BY 
                        s.task_id,
                        CASE WHEN s.start_date IS NULL THEN 1 ELSE 0 END,
                        s.start_date ASC,
                        s.id
                """, (selected_project_id,))
                
                if tasks_data or subtasks_data:
                    gantt_data = []
                    task_order = {}
                    current_row = 0
                    
                    # Helper function to format dates or return N/A
                    def format_date_or_na(date):
                        if pd.isna(date) or date is None:
                            return "N/A"
                        try:
                            return date.strftime('%b %d, %Y')
                        except:
                            return "N/A"
                    
                    # Helper function to calculate duration or return N/A
                    def calculate_duration(start, end):
                        if pd.isna(start) or pd.isna(end) or start is None or end is None:
                            return "N/A"
                        try:
                            return f"{(end - start).days} days"
                        except:
                            return "N/A"
                    
                  
                    # In the Gantt Chart data preparation
                    # In the Gantt Chart data preparation
                    for task in tasks_data:
                        # Update parent task status based on subtasks
                        if update_parent_task_status(task[0]):
                            # Re-fetch tasks data if status changed
                            tasks_data = query_db("""
                                SELECT 
                                    t.id as task_id, 
                                    t.title as task_title,
                                    t.start_date as task_start,
                                    t.deadline as task_end,
                                    t.status as task_status,
                                    t.priority as task_priority,
                                    u1.username as task_assignee,
                                    t.actual_start_date,
                                    t.actual_deadline
                                FROM tasks t
                                LEFT JOIN users u1 ON t.assigned_to = u1.id
                                WHERE t.project_id = ?
                                ORDER BY 
                                    CASE WHEN t.start_date IS NULL THEN 1 ELSE 0 END,
                                    t.start_date ASC,
                                    t.id
                            """, (selected_project_id,))
                            break  # Break and restart processing with fresh data



                        # Check and update parent task status first
                        if task[4] != "Completed":  # Only check if not already completed
                            update_parent_task_status(task[0])

                        task_id = task[0]
                        task_order[task_id] = current_row
                        current_row += 1
                        
                        # Process dates
                        planned_start = pd.to_datetime(task[2]) if task[2] else None
                        planned_end = pd.to_datetime(task[3]) if task[3] else None
                        actual_start = pd.to_datetime(task[7]) if task[7] else None
                        actual_end = pd.to_datetime(task[8]) if task[8] else None
                        
                        # Format dates for display
                        planned_start_str = format_date_or_na(planned_start)
                        planned_end_str = format_date_or_na(planned_end)
                        actual_start_str = format_date_or_na(actual_start)
                        actual_end_str = format_date_or_na(actual_end)
                        
                        # Calculate durations
                        planned_duration = calculate_duration(planned_start, planned_end)
                        actual_duration = calculate_duration(actual_start, actual_end)
                        
                        # Determine color based on priority
                        priority = task[5] if task[5] in task_colors else "Medium"
                        color = task_colors[priority]
                        
                        # Add task to Gantt data
                        gantt_data.append({
                            "Task": f"📌 {task[1]}",
                            "Start": planned_start if planned_start else pd.to_datetime('today'),
                            "Finish": planned_end if planned_end else pd.to_datetime('today') + pd.Timedelta(days=1),
                            "Type": "Task",
                            "Status": task[4],
                            "Priority": priority,
                            "Assignee": task[6] or "Unassigned",
                            "Row": task_order[task_id],
                            "Color": color,
                            "Planned Start": planned_start_str,
                            "Planned End": planned_end_str,
                            "Actual Start": actual_start_str,
                            "Actual End": actual_end_str,
                            "Planned Duration": planned_duration,
                            "Actual Duration": actual_duration
                        })
                        
                        # Find all subtasks for this task
                        task_subtasks = [st for st in subtasks_data if st[0] == task_id]
                        
                        # Add subtasks under their parent task with indentation
                        for subtask in task_subtasks:
                            planned_start = pd.to_datetime(subtask[4]) if subtask[4] else None
                            planned_end = pd.to_datetime(subtask[5]) if subtask[5] else None
                            actual_start = pd.to_datetime(subtask[11]) if subtask[11] else None
                            actual_end = pd.to_datetime(subtask[12]) if subtask[12] else None
                            
                            # Format dates for display
                            planned_start_str = format_date_or_na(planned_start)
                            planned_end_str = format_date_or_na(planned_end)
                            actual_start_str = format_date_or_na(actual_start)
                            actual_end_str = format_date_or_na(actual_end)
                            
                            # Calculate durations
                            planned_duration = calculate_duration(planned_start, planned_end)
                            actual_duration = calculate_duration(actual_start, actual_end)
                            
                            # Determine subtask color based on priority
                            subtask_priority = subtask[7] if subtask[7] in subtask_colors else "Medium"
                            subtask_color = subtask_colors[subtask_priority]
                            
                            gantt_data.append({
                                "Task": f"    ↳ {subtask[3]}",
                                "Start": planned_start if planned_start else pd.to_datetime('today'),
                                "Finish": planned_end if planned_end else pd.to_datetime('today') + pd.Timedelta(days=1),
                                "Type": "Subtask",
                                "Status": subtask[6],
                                "Priority": subtask_priority,
                                "Assignee": subtask[8] or "Unassigned",
                                "Row": current_row,
                                "Color": subtask_color,
                                "Planned Start": planned_start_str,
                                "Planned End": planned_end_str,
                                "Actual Start": actual_start_str,
                                "Actual End": actual_end_str,
                                "Planned Duration": planned_duration,
                                "Actual Duration": actual_duration
                            })
                            current_row += 1

                    ###
                    # In the Gantt Chart section, modify the figure creation code:

                    if gantt_data:
                        gantt_df = pd.DataFrame(gantt_data)
                        
                        # Calculate row spacing - use fixed spacing between rows (1 unit per row)
                        gantt_df['SpacedRow'] = gantt_df.index * 1  # Simple row numbering
                        
                        # Create figure with improved layout
                        fig = px.timeline(
                            gantt_df,
                            x_start="Start",
                            x_end="Finish",
                            y="SpacedRow",
                            color="Priority",
                            color_discrete_map={
                                "High": task_colors["High"],
                                "Medium": task_colors["Medium"],
                                "Low": task_colors["Low"]
                            },
                            hover_data=[
                                "Task", "Status", "Assignee", "Type",
                                "Planned Start", "Planned End", "Planned Duration",
                                "Actual Start", "Actual End", "Actual Duration"
                            ],
                            title=f"Gantt Chart - {project_name}",
                            template="plotly_white"
                        )
                        
                        # Add today's line
                        today = pd.Timestamp.now().normalize()
                        fig.add_shape(
                            type="line",
                            x0=today,
                            x1=today,
                            y0=-1,
                            y1=gantt_df['SpacedRow'].max() + 1,
                            line=dict(color="red", width=2, dash="dot"),
                            name="Today"
                        )

                        # Customize the layout to fix bar heights and spacing
                        fig.update_layout(
                            yaxis=dict(
                                tickmode='array',
                                tickvals=gantt_df['SpacedRow'],
                                ticktext=gantt_df['Task'],
                                autorange="reversed",
                                showgrid=True,
                                gridcolor="lightgray",
                                range=[-0.5, len(gantt_df) - 0.5]  # Set fixed y-axis range
                            ),
                            height=600 + len(gantt_df) * 25,  # Dynamic height based on number of items
                            xaxis=dict(
                                title="Timeline",
                                showgrid=True,
                                gridcolor="lightgray"
                            ),
                            hovermode="closest",
                            showlegend=True,
                            legend_title="Task Priority",
                            margin=dict(l=250, r=50, t=80, b=50),
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            bargap=0.2  # Add gap between bars
                        )
                        
                        # Set consistent bar height
                        fig.update_traces(
                            width=0.6  # Adjust bar thickness (0-1)
                        )
                        
                        # Customize hover template
                        fig.update_traces(
                            hovertemplate=(
                                "<b>%{customdata[0]}</b><br>"
                                "Type: %{customdata[3]}<br>"
                                "Status: %{customdata[1]}<br>"
                                "Assignee: %{customdata[2]}<br><br>"
                                
                                "<b>Planned Timeline</b><br>"
                                "Start: %{customdata[4]}<br>"
                                "End: %{customdata[5]}<br>"
                                "Duration: %{customdata[6]}<br><br>"
                                
                                "<b>Actual Timeline</b><br>"
                                "Start: %{customdata[7]}<br>"
                                "End: %{customdata[8]}<br>"
                                "Duration: %{customdata[9]}<br><br>"
                                
                                "<extra></extra>"
                            )
                        )
                        
                        # Add annotations for better readability
                        fig.add_annotation(
                            x=today,
                            y=gantt_df['SpacedRow'].max() + 1,
                            text="Today",
                            showarrow=False,
                            yshift=10,
                            font=dict(color="red")
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)


                        
                        # Add legend explanation
                        with st.expander("Chart Legend", expanded=True):
                            st.markdown("""
                            - **📌** - Main task
                            - **↳** - Subtask
                            - **Colors** indicate priority:
                                - <span style='color:#FF6B6B;'>Red</span> - High priority
                                - <span style='color:#FFD166;'>Yellow</span> - Medium priority
                                - <span style='color:#06D6A0;'>Green</span> - Low priority
                            - **Dotted red line** - Today's date
                            """, unsafe_allow_html=True)
            
           
                        
                        
                        # Subtasks Analytics Table with Filters
                        st.markdown("---")
                        st.subheader("Subtasks Analytics")
                        
                        if subtasks_data:
                            # Prepare data for analytics table
                            analytics_data = []
                            for subtask in subtasks_data:
                                analytics_data.append({
                                    "Project": project_name,
                                    "Task": subtask[1],  # task_title
                                    "Subtask": subtask[3],  # subtask_title
                                    "Status": subtask[6],
                                    "Priority": subtask[7],
                                    "Assigned To": subtask[8] or "Unassigned",
                                    "Start Date": pd.to_datetime(subtask[4]).date() if subtask[4] else None,
                                    "Deadline": pd.to_datetime(subtask[5]).date() if subtask[5] else None,
                                    "Budget": float(subtask[9]) if subtask[9] is not None else None,
                                    "Time Spent (Hrs)": float(subtask[10]) if subtask[10] is not None else None
                                })
                            
                            analytics_df = pd.DataFrame(analytics_data)
                            
                            # Add filters
                            with st.expander("🔍 Filter Subtasks", expanded=True):
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    task_filter = st.multiselect(
                                        "Filter by Task",
                                        options=analytics_df['Task'].unique(),
                                        default=None,
                                        key="task_filter"
                                    )
                                
                                with col2:
                                    subtask_filter = st.multiselect(
                                        "Filter by Subtask",
                                        options=analytics_df['Subtask'].unique(),
                                        default=None,
                                        key="subtask_filter"
                                    )
                                
                                with col3:
                                    status_filter = st.multiselect(
                                        "Filter by Status",
                                        options=analytics_df['Status'].unique(),
                                        default=None,
                                        key="status_filter"
                                    )
                                
                                with col4:
                                    assignee_filter = st.multiselect(
                                        "Filter by Assigned To",
                                        options=analytics_df['Assigned To'].unique(),
                                        default=None,
                                        key="assignee_filter"
                                    )
                            
                            # Apply filters
                            if task_filter:
                                analytics_df = analytics_df[analytics_df['Task'].isin(task_filter)]
                            if subtask_filter:
                                analytics_df = analytics_df[analytics_df['Subtask'].isin(subtask_filter)]
                            if status_filter:
                                analytics_df = analytics_df[analytics_df['Status'].isin(status_filter)]
                            if assignee_filter:
                                analytics_df = analytics_df[analytics_df['Assigned To'].isin(assignee_filter)]
                            
                            # Format numeric columns for display
                            display_df = analytics_df.copy()
                            display_df['Budget'] = display_df['Budget'].apply(
                                lambda x: f"${x:,.2f}" if pd.notnull(x) else "-"
                            )
                            display_df['Time Spent (Hrs)'] = display_df['Time Spent (Hrs)'].apply(
                                lambda x: f"{x:.1f}" if pd.notnull(x) else "-"
                            )
                            
                            # Display the table with formatting
                            st.dataframe(
                                display_df,
                                column_config={
                                    "Project": st.column_config.TextColumn("Project"),
                                    "Task": st.column_config.TextColumn("Task"),
                                    "Subtask": st.column_config.TextColumn("Subtask"),
                                    "Status": st.column_config.TextColumn("Status"),
                                    "Priority": st.column_config.TextColumn("Priority"),
                                    "Assigned To": st.column_config.TextColumn("Assigned To"),
                                    "Start Date": st.column_config.DateColumn("Start Date"),
                                    "Deadline": st.column_config.DateColumn("Deadline"),
                                    "Budget": st.column_config.TextColumn("Budget"),
                                    "Time Spent (Hrs)": st.column_config.TextColumn("Time Spent (Hrs)")
                                },
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Download button for filtered data
                            csv = analytics_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Filtered Data as CSV",
                                data=csv,
                                file_name=f"{project_name}_subtasks_analytics.csv",
                                mime="text/csv",
                                key="download_filtered_subtasks"
                            )
                        else:
                            st.info("No subtasks found for analytics")
                    else:
                        st.info("No tasks found for this project")



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

    ####
    with tab4:  # Timeline Tab
        st.subheader("Project Timeline")
        
        # Get all tasks with their planned and actual dates
        tasks_data = query_db("""
            SELECT 
                t.id as task_id, 
                t.title as task_title,
                t.start_date as planned_start,
                t.deadline as planned_end,
                t.actual_start_date as actual_start,
                t.actual_deadline as actual_end,
                t.status as task_status,
                t.priority as task_priority,
                u.username as assignee
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.project_id = ?
            ORDER BY
                CASE WHEN t.start_date IS NULL THEN 1 ELSE 0 END,
                t.start_date ASC,
                t.id
        """, (selected_project_id,)) or []
        
        if tasks_data:
            # Helper functions to handle dates
            def format_date_or_na(date):
                if pd.isna(date) or date is None:
                    return "N/A"
                try:
                    return date.strftime('%b %d, %Y')
                except:
                    return "N/A"
            
            def calculate_duration_or_na(start, end):
                if pd.isna(start) or pd.isna(end) or start is None or end is None:
                    return "N/A"
                try:
                    return f"{(end - start).days} days"
                except:
                    return "N/A"
            
            # Prepare data for Gantt chart
            gantt_data = []
            row_mapping = {}
            current_row = 0
            
           
            # In the Timeline tab data preparation
            # In the Timeline tab data preparation
            for task in tasks_data:
                # Update parent task status based on subtasks
                if update_parent_task_status(task[0]):
                    # Re-fetch tasks data if status changed
                    tasks_data = query_db("""
                        SELECT 
                            t.id as task_id, 
                            t.title as task_title,
                            t.start_date as planned_start,
                            t.deadline as planned_end,
                            t.actual_start_date as actual_start,
                            t.actual_deadline as actual_end,
                            t.status as task_status,
                            t.priority as task_priority,
                            u.username as assignee
                        FROM tasks t
                        LEFT JOIN users u ON t.assigned_to = u.id
                        WHERE t.project_id = ?
                        ORDER BY
                            CASE WHEN t.start_date IS NULL THEN 1 ELSE 0 END,
                            t.start_date ASC,
                            t.id
                    """, (selected_project_id,))
                    break  # Break and restart processing with fresh data



                if task[6] != "Completed":  # task_status is at index 6
                    update_parent_task_status(task[0])
                

                task_id, title, planned_start, planned_end, actual_start, actual_end, status, priority, assignee = task
                
                # Convert dates
                planned_start = pd.to_datetime(planned_start) if planned_start else None
                planned_end = pd.to_datetime(planned_end) if planned_end else None
                actual_start = pd.to_datetime(actual_start) if actual_start else None
                actual_end = pd.to_datetime(actual_end) if actual_end else None
                
                # Format dates for display
                planned_start_str = format_date_or_na(planned_start)
                planned_end_str = format_date_or_na(planned_end)
                actual_start_str = format_date_or_na(actual_start)
                actual_end_str = format_date_or_na(actual_end)
                
                # Calculate durations
                planned_duration = calculate_duration_or_na(planned_start, planned_end)
                actual_duration = calculate_duration_or_na(actual_start, actual_end)
                
                # Maintain same row numbering
                row_mapping[task_id] = current_row
                current_row += 1
                
                # Add planned timeline (always shown)
                gantt_data.append({
                    "Task": title,
                    "Start": planned_start if planned_start else pd.to_datetime('today'),
                    "Finish": planned_end if planned_end else pd.to_datetime('today') + pd.Timedelta(days=1),
                    "Timeline": "Planned",
                    "Status": status,
                    "Priority": priority,
                    "Assignee": assignee or "Unassigned",
                    "Row": row_mapping[task_id],
                    "Color": "lightgray",
                    "Planned Start": planned_start_str,
                    "Planned End": planned_end_str,
                    "Planned Duration": planned_duration,
                    "Actual Start": actual_start_str,
                    "Actual End": actual_end_str,
                    "Actual Duration": actual_duration
                })
                
                # Add actual timeline if available
                if actual_start and actual_end:
                    gantt_data.append({
                        "Task": title,
                        "Start": actual_start,
                        "Finish": actual_end,
                        "Timeline": "Actual",
                        "Status": status,
                        "Priority": priority,
                        "Assignee": assignee or "Unassigned",
                        "Row": row_mapping[task_id],
                        "Color": "blue",
                        "Planned Start": planned_start_str,
                        "Planned End": planned_end_str,
                        "Planned Duration": planned_duration,
                        "Actual Start": actual_start_str,
                        "Actual End": actual_end_str,
                        "Actual Duration": actual_duration
                    })
 
                current_row += 1
            #
            if gantt_data:
                gantt_df = pd.DataFrame(gantt_data)
                
                # Sort maintaining order
                gantt_df = gantt_df.sort_values(by=['Row', 'Start'])
                
                # Create the Gantt chart with both timelines
                fig = px.timeline(
                    gantt_df,
                    x_start="Start",
                    x_end="Finish",
                    y="Row",
                    color="Timeline",
                    color_discrete_map={
                        "Planned": "lightgray",
                        "Actual": "blue"
                    },
                    hover_data=[
                        "Task", "Status", "Priority", "Assignee",
                        "Planned Start", "Planned End", "Planned Duration",
                        "Actual Start", "Actual End", "Actual Duration"
                    ],
                    title="Project Timeline (Planned vs Actual)"
                )
                
                # Add today's line
                today = pd.Timestamp.now().normalize()
                fig.add_shape(
                    type="line",
                    x0=today,
                    x1=today,
                    y0=-0.5,
                    y1=len(row_mapping) - 0.5,
                    line=dict(color="red", width=2, dash="dot")
                )
                
                # Custom y-axis labels to match task names
                y_tick_text = [
                    tasks_data[i][1] for i in range(len(row_mapping))
                ]
                
                fig.update_layout(
                    yaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(row_mapping))),
                        ticktext=y_tick_text,
                        autorange="reversed"
                    ),
                    height=600 + len(row_mapping) * 30,
                    xaxis_title="Timeline",
                    hovermode="closest",
                    showlegend=True,
                    legend_title="Timeline Type",
                    margin=dict(l=200, r=50, t=80, b=50)
                )
                
                # Enhanced tooltip with N/A for unavailable dates
                fig.update_traces(
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Status: %{customdata[1]}<br>"
                        "Priority: %{customdata[2]}<br>"
                        "Assignee: %{customdata[3]}<br><br>"
                        
                        "<b>Planned Timeline</b><br>"
                        "Start: %{customdata[4]}<br>"
                        "End: %{customdata[5]}<br>"
                        "Duration: %{customdata[6]}<br><br>"
                        
                        "<b>Actual Timeline</b><br>"
                        "Start: %{customdata[7]}<br>"
                        "End: %{customdata[8]}<br>"
                        "Duration: %{customdata[9]}<br><br>"
                        
                        "<extra></extra>"
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tasks with valid dates to display")
        else:
            st.info("No tasks found for this project")


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