import streamlit as st 
import sqlite3 
import datetime 
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import hashlib
from components.drag_and_drop import drag_and_drop
from streamlit_calendar import calendar
import io  # For handling in-memory file buffers
import logging


# Page Config (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(page_title="Project Management App", layout="wide")


# Define priority colors
priority_colors = {
            "High": "#FF0000",  # Red
            "Medium": "#FFA500",  # Orange
            "Low": "#32CD32"  # Green
        }        


# Initialize session state for color scheme
if "color_scheme" not in st.session_state:
    st.session_state.color_scheme = {
        "primary": "#4CAF50",  # Green
        "secondary": "#2196F3",  # Blue
        "background": "#FFFFFF",  # White
        "text": "#000000",  # Black
    } 

# Custom CSS
custom_css = f"""
<style>
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
    
    # Check if the start_date column exists, and if not, add it
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]

    if 'start_date' not in column_names:
        c.execute('ALTER TABLE tasks ADD COLUMN start_date TEXT')  
        
    
    
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
        )
    ''')
    
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
    """
    Fetch tasks from the database and return them as a Pandas DataFrame.
    If project_id is provided, fetch tasks for that specific project.
    """
    if project_id:
        query = """
            SELECT 
                t.title AS Task, 
                t.status, 
                u.username AS assignee, 
                t.time_spent AS "Spent Time", 
                p.name AS Project, 
                t.start_date AS "Start Date",
                t.deadline AS "Deadline",
                (julianday(t.deadline) - julianday(t.start_date)) AS "Duration (days)",
                t.priority AS Priority,
                t.budget AS Budget,
                t.actual_cost AS "Actual Cost",
                t.budget_variance AS "Budget Variance"
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.project_id = ?
        """
        tasks = query_db(query, (project_id,))
    else:
        if st.session_state.user_role == "Admin":
            # Admin can see all tasks
            query = """
                SELECT 
                    t.title AS Task, 
                    t.status, 
                    u.username AS assignee, 
                    t.time_spent AS "Spent Time", 
                    p.name AS Project, 
                    t.start_date AS "Start Date",
                    t.deadline AS "Deadline",
                    (julianday(t.deadline) - julianday(t.start_date)) AS "Duration (days)",
                    t.priority AS Priority,
                    t.budget AS Budget,
                    t.actual_cost AS "Actual Cost",
                    t.budget_variance AS "Budget Variance"
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.id
                LEFT JOIN projects p ON t.project_id = p.id
            """
            tasks = query_db(query)
        else:
            # Regular users can see tasks assigned to them or tasks in their projects
            query = """
                SELECT 
                    t.title AS Task, 
                    t.status, 
                    u.username AS assignee, 
                    t.time_spent AS "Spent Time", 
                    p.name AS Project, 
                    t.start_date AS "Start Date",
                    t.deadline AS "Deadline",
                    (julianday(t.deadline) - julianday(t.start_date)) AS "Duration (days)",
                    t.priority AS Priority,
                    t.budget AS Budget,
                    t.actual_cost AS "Actual Cost",
                    t.budget_variance AS "Budget Variance"
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.id
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.assigned_to = ? OR p.user_id = ?
            """
            tasks = query_db(query, (st.session_state.user_id, st.session_state.user_id))
    
    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(tasks, columns=[
        "Task", "Status", "Assignee", "Spent Time", "Project", "Start Date", "Deadline", "Duration (days)", "Priority", "Budget", "Actual Cost", "Budget Variance"
    ])
    return df





def display_task_table():
    """
    Display tasks in a table format using Streamlit.
    Allow filtering by project.
    """
    # Fetch all projects for the logged-in user
    projects = query_db("SELECT id, name FROM projects WHERE user_id=?", (st.session_state.user_id,))
    project_names = [project[1] for project in projects]
    project_names.insert(0, "All Projects")  

    # Add a project filter dropdown
    selected_project = st.selectbox("Filter by Project", project_names)
    
    # Fetch tasks based on the selected project
    if selected_project == "All Projects":
        tasks_df = fetch_tasks()  
    else:
        project_id = query_db("SELECT id FROM projects WHERE name=?", (selected_project,), one=True)[0]
        tasks_df = fetch_tasks(project_id)  
    
    # Display the table
    if tasks_df.empty:
        st.warning("No tasks found.")
    else:
        st.dataframe(tasks_df)  
    
    return tasks_df     
        

# Helper Functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by the user."""
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()






# Helper function to display projects as cards
def display_projects_as_cards():
    """Display project cards with owner selection in edit form."""
    # Fetch all users for owner dropdown
    users = query_db("SELECT id, username FROM users")
    user_options = {user[0]: user[1] for user in users}  # {user_id: username}

    projects = query_db("""
        SELECT id, user_id, name, description, 
               start_date, end_date, budget 
        FROM projects
    """)
    
    if not projects:
        st.warning("No projects found in the database.")
        return

    # Success notifications
    if st.session_state.get('show_edit_success'):
        st.success("✓ Project updated successfully!")
        del st.session_state['show_edit_success']

    # State tracking
    st.session_state.setdefault('editing_project_id', None)
    st.session_state.setdefault('deleting_project_id', None)

    # Responsive grid
    num_columns = 3 if not st.session_state.is_mobile else 1
    cols = st.columns(num_columns)
    
    for i, project in enumerate(projects):
        with cols[i % num_columns]:
            with st.container():
                try:
                    project_id, owner_id, name, description, start_date, end_date, budget = project
                    
                    # Get owner's username
                    owner_username = user_options.get(owner_id, "Unknown")
                    
                    # Format budget
                    budget_display = (
                        "Not set" if budget is None else
                        f"${float(budget):,.2f}" if isinstance(budget, (int, float)) else
                        "Invalid value"
                    )
                    
                    # Project card display
                    st.markdown(f"""
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-title" style="font-size: 1.2em; margin-bottom: 10px;">
                            {name}
                        </div>
                        <div class="card-content">
                            <p><strong>Description:</strong> {description or 'No description'}</p>
                            <p><strong>Owner:</strong> {owner_username}</p>
                            <p><strong>Start Date:</strong> {start_date}</p> 
                            <p><strong>End Date:</strong> {end_date}</p>
                            <p><strong style="color: #2e8b57;">Budget:</strong>
                            <span style="font-weight: bold;">{budget_display}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Edit/Delete buttons
                    is_admin = st.session_state.user_role == "Admin"
                    is_owner = owner_id == st.session_state.user_id

                    if (is_admin or is_owner) and not st.session_state.editing_project_id:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Edit {name}", key=f"edit_{project_id}"):
                                st.session_state.editing_project_id = project_id
                        with col2:
                            if is_admin and st.button(f"Delete {name}", key=f"del_{project_id}"):
                                st.session_state.deleting_project_id = project_id

                    # Delete confirmation
                    if st.session_state.deleting_project_id == project_id:
                        st.warning(f"Permanently delete '{name}'?")
                        if st.button(f"Confirm Delete", key=f"conf_del_{project_id}"):
                            delete_project(project_id)
                            st.success(f"Project '{name}' deleted")
                            st.session_state.deleting_project_id = None
                            st.rerun()
                        if st.button("Cancel", key=f"cancel_del_{project_id}"):
                            st.session_state.deleting_project_id = None
                            st.rerun()

                    # Edit form with owner dropdown
                    if st.session_state.editing_project_id == project_id:
                        with st.form(f"edit_form_{project_id}"):
                            new_name = st.text_input("Project Name", value=name)
                            new_desc = st.text_area("Description", value=description)
                            
                            # Owner dropdown (only for admins)
                            if is_admin:
                                current_owner_name = user_options.get(owner_id, "Unknown")
                                new_owner_name = st.selectbox(
                                    "Project Owner",
                                    options=list(user_options.values()),
                                    index=list(user_options.values()).index(current_owner_name)
                                )
                                new_owner_id = [uid for uid, uname in user_options.items() if uname == new_owner_name][0]
                            else:
                                new_owner_id = owner_id  # Non-admins can't change owner
                            
                            new_start = st.date_input("Start Date", 
                                                    value=datetime.strptime(start_date, "%Y-%m-%d").date())
                            new_end = st.date_input("End Date", 
                                                  value=datetime.strptime(end_date, "%Y-%m-%d").date())
                            new_budget = st.number_input("Budget", value=float(budget) if budget else 0.0, step=0.01)
                            
                            if st.form_submit_button("Save Changes"):
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
                            
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_project_id = None
                                st.rerun()

                except Exception as e:
                    st.error(f"Error loading project: {e}")        

                                   
                
        





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

# Sidebar Navigation
st.sidebar.title("📊 Navigation")

# Logout Button
if st.session_state.authenticated:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_role = None
        st.session_state.breadcrumbs = []  # Clear breadcrumbs on logout
        st.success("You have been logged out.")
        st.rerun()

# Help Button in Sidebar
if st.session_state.authenticated:
    if st.sidebar.button("❓ Help"):
        st.session_state.show_help = not st.session_state.show_help

# Help Content
if st.session_state.authenticated and st.session_state.show_help:
    st.sidebar.markdown("### Help")
    st.sidebar.markdown("""
        - **Dashboard**: View an overview of your projects and tasks.
        - **Projects**: Create and manage projects.
        - **Tasks**: Add, update, and track tasks.
        - **Reports**: Analyze project progress and time tracking.
        - **Notifications**: Stay updated on upcoming and overdue tasks.
    """)





    

# Define status colors for tasks
status_colors = {
    "Pending": "#FFA500",  # Orange
    "In Progress": "#00BFFF",  # DeepSkyBlue
    "Completed": "#32CD32",  # LimeGreen
    "Overdue": "#FF4500"  # OrangeRed
}



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
    Each task will be an event with a color based on its status.
    """
    # Fetch tasks from the database
    query = """
        SELECT t.id, t.title AS Task, t.deadline AS Date, t.status, p.name AS Project
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.project_id IN (SELECT id FROM projects WHERE user_id = ?)
    """
    tasks = query_db(query, (st.session_state.user_id,))
    
    # Prepare events for the calendar
    events = []
    for task in tasks:
        event = {
            "Task": task[1],  # Task title
            "Date": task[2],  # Task deadline
            "Status": task[3],  # Task status
            "Project": task[4],  # Project name
            "Task ID": task[0]  # Task ID
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

# User Authentication
if not st.session_state.authenticated:
    st.title("Login or Register")
    
    # Login Form
    with st.form(key="login_form"):  # Use a unique key
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = query_db("SELECT * FROM users WHERE username=?", (username,), one=True)
            if user and verify_password(user[2], password):
                st.session_state.authenticated = True
                st.session_state.user_id = user[0]
                st.session_state.user_role = user[3]  # Store the user's role
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    
    # Registration Form
    with st.form("register_form"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.form_submit_button("Register"):
            if query_db("SELECT * FROM users WHERE username=?", (new_username,), one=True):
                st.error("Username already exists.")
            else:
                # First user is an Admin, others are Users
                role = "Admin" if len(query_db("SELECT * FROM users")) == 0 else "User"
                query_db("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (new_username, hash_password(new_password), role))
                st.success("Registration successful! Please login.")
                st.rerun()
else:
    # Main App
    if st.session_state.user_role == "Admin":
        page = st.sidebar.radio("Go to", ["Dashboard", "Projects", "Tasks", "Reports", "Notifications", "Calendar","Admin", "Profile", "Documentation"])
    else:
        page = st.sidebar.radio("Go to", ["Dashboard", "Projects", "Tasks", "Reports", "Notifications", "Calendar", "Profile","Documentation"])
    
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
        """
        Create a line chart showing the number of tasks completed over time.
        """
        if tasks_df.empty:
            st.warning("No tasks found for visualization.")
            return
        
        # Filter completed tasks
        completed_tasks = tasks_df[tasks_df["Status"] == "Completed"]
        
        if completed_tasks.empty:
            st.warning("No completed tasks found.")
            return
        
        # Convert "Start Date" to datetime and extract the date part
        completed_tasks["Start Date"] = pd.to_datetime(completed_tasks["Start Date"]).dt.date
        
        # Group by date and count completed tasks
        progress_data = completed_tasks.groupby("Start Date").size().reset_index(name="Completed Tasks")
        
        # Create line chart
        fig = px.line(
            progress_data,
            x="Start Date",
            y="Completed Tasks",
            title="Task Progress Over Time",
            labels={"Start Date": "Date", "Completed Tasks": "Number of Tasks Completed"},
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





    # Dashboard Page
    if page == "Dashboard":
        st.title("🏠 Dashboard")
        st.write("Welcome to the Project Management App!")

        # Summary Statistics
        st.subheader("📊 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_projects = len(get_projects())
            st.metric("Total Projects", total_projects)
        with col2:
            total_tasks = len(get_tasks())
            st.metric("Total Tasks", total_tasks)
        with col3:
            overdue_tasks_count = len(get_upcoming_and_overdue_tasks()[1])
            st.metric("Overdue Tasks", overdue_tasks_count)
        with col4:
            upcoming_tasks_count = len(get_upcoming_and_overdue_tasks()[0])
            st.metric("Upcoming Tasks", upcoming_tasks_count)

        # Collapsible Section for Overdue Tasks
        with st.expander("⚠️ Overdue Tasks", expanded=False):
            overdue_tasks = get_upcoming_and_overdue_tasks()[1]
            if overdue_tasks:
                for task in overdue_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    st.markdown(f"""
                        <p style="color: {color};">
                            - <strong>{task[2]}</strong> (Deadline: {task[6]})
                        </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No overdue tasks.")

        # Collapsible Section for Upcoming Tasks
        with st.expander("🔜 Upcoming Tasks", expanded=False):
            upcoming_tasks = get_upcoming_and_overdue_tasks()[0]
            if upcoming_tasks:
                for task in upcoming_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    st.markdown(f"""
                        <p style="color: {color};">
                            - <strong>{task[2]}</strong> (Deadline: {task[6]})
                        </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No upcoming tasks.")

        # Projects Section
        st.subheader("📂 Projects")
        projects = get_projects()
        if not projects:
            st.warning("No projects found in the database.")
        else:
            for project in projects:
                with st.expander(f"Project: {project[2]}"):
                    st.write(f"**Description:** {project[3]}")
                    st.write(f"**Start Date:** {project[4]} | **End Date:** {project[5]}")

                    # Fetch tasks for the current project
                    tasks = get_tasks(project[0])
                    st.write(f"**Tasks for project {project[2]}:**")
                    
                    if not tasks:
                        st.warning("No tasks found for this project.")
                    else:
                        # Calculate progress
                        completed_tasks = len([task for task in tasks if task[4] == "Completed"])
                        total_tasks = len(tasks)
                        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                        st.progress(int(progress))
                        st.write(f"**Progress:** {completed_tasks}/{total_tasks} tasks completed ({progress:.1f}%)")

                        # Create Gantt chart for the current project
                        gantt_data = []
                        for task in tasks:
                            start_date = datetime.strptime(task[11], "%Y-%m-%d").date() if task[11] else datetime.today().date()
                            deadline = datetime.strptime(task[6], "%Y-%m-%d").date()
                            gantt_data.append({
                                "Task": task[2],
                                "Start": start_date,
                                "Finish": deadline,
                                "Status": task[4],
                                "Color": status_colors.get(task[4], "#f0f0f0")
                            })

                        # Create a DataFrame for the Gantt chart
                        df = pd.DataFrame(gantt_data)

                        # Create the Gantt chart using Plotly
                        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Status", title=f"Gantt Chart for {project[2]}",
                                        color_discrete_map=status_colors)
                        st.plotly_chart(fig)



# Projects Page
    elif page == "Projects":
        st.title("📂 Projects")
        
        # Initialize success message state if it doesn't exist
        if 'show_project_success' not in st.session_state:
            st.session_state.show_project_success = False
        
        # Display success message if flag is True (this needs to be at the very top)
        if st.session_state.show_project_success:
            st.success("Project added successfully!")
            st.session_state.show_project_success = False  # Reset the flag
        
        # Fetch all registered users for the project owner dropdown
        users = query_db("SELECT id, username FROM users")
        user_options = {user[0]: user[1] for user in users}  # {user_id: username}

        # Add New Project - using a form key that changes after submission
        form_key = "project_form_" + str(st.session_state.get('form_counter', 0))
        with st.form(key=form_key):
            name = st.text_input("Project Name", key="project_name")
            description = st.text_area("Description", key="project_description")
            
            # Project Owner Dropdown
            project_owner = st.selectbox(
                "Project Owner",
                options=list(user_options.values()),
                format_func=lambda x: user_options.get(x, x)
            )
            
            # Project Start and Due Dates
            start_date = st.date_input("Start Date", key="project_start_date")
            due_date = st.date_input("Due Date", key="project_due_date")
            
            # Project Budget
            budget = st.number_input("Project Budget", min_value=0.0, value=0.0, key="project_budget")
            
            submitted = st.form_submit_button("➕ Add Project")
            if submitted:
                # Get the selected project owner's ID
                project_owner_id = [user_id for user_id, username in user_options.items() if username == project_owner][0]
                
                # Insert the new project into the database
                query_db("""
                    INSERT INTO projects (user_id, name, description, start_date, end_date, budget)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_owner_id, name, description, start_date, due_date, budget
                ))
                
                # Set the success flag and increment form counter
                st.session_state.show_project_success = True
                st.session_state.form_counter = st.session_state.get('form_counter', 0) + 1
                
                # Force a rerun
                st.rerun()
        
        # Display Projects as Cards
        display_projects_as_cards()




# Tasks Page
    elif page == "Tasks":
        st.title("✅ Tasks")
        
        # Fetch upcoming and overdue tasks
        upcoming_tasks, overdue_tasks = get_upcoming_and_overdue_tasks()
        
        # Collapsible section for Overdue Tasks
        with st.expander("⚠️ Overdue Tasks", expanded=False):
            if overdue_tasks:
                for task in overdue_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    st.markdown(f"""
                        <p style="color: {color};">
                            - <strong>{task[2]}</strong> (Deadline: {task[6]})
                        </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No overdue tasks.")
        
        # Collapsible section for Upcoming Tasks
        with st.expander("🔜 Upcoming Tasks", expanded=False):
            if upcoming_tasks:
                for task in upcoming_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    st.markdown(f"""
                        <p style="color: {color};">
                            - <strong>{task[2]}</strong> (Deadline: {task[6]})
                        </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No upcoming tasks.")
        
        # Add New Task Form
        with st.form("new_task"):
            projects = get_projects()
            project_names = [project[2] for project in projects]
            selected_project = st.selectbox("Select Project", project_names)
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            start_date = st.date_input("Start Date")
            deadline = st.date_input("Deadline")
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            recurrence = st.selectbox("Recurrence", ["None", "Daily", "Weekly", "Monthly"])
            budget = st.number_input("Budget", min_value=0.0, value=0.0)
            actual_cost = st.number_input("Actual Cost", min_value=0.0, value=0.0)
            budget_variance = st.number_input("Budget Variance", value=budget - (actual_cost if actual_cost is not None else 0.0), disabled=True)
            
            # Fetch team members (users) from the database
            team_members = query_db("SELECT id, username FROM users WHERE role='User' OR role='Admin'")
            
            # Assign task to a team member
            assigned_to = st.selectbox("Assign to", [member[1] for member in team_members], index=0)
            
            # Add a submit button
            if st.form_submit_button("➕ Add Task"):
                project_id = query_db("SELECT id FROM projects WHERE name=? AND user_id=?", (selected_project, st.session_state.user_id), one=True)[0]
                assigned_to_id = query_db("SELECT id FROM users WHERE username=?", (assigned_to,), one=True)[0]
                query_db("INSERT INTO tasks (project_id, title, description, start_date, deadline, priority, recurrence, assigned_to, budget, actual_cost, budget_variance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (project_id, title, description, start_date, deadline, priority, recurrence.lower() if recurrence != "None" else None, assigned_to_id, budget, actual_cost, budget - (actual_cost if actual_cost is not None else 0.0)))
                st.success("Task added successfully!")
                st.rerun()

        # Display the Task Table with Project Filter
        st.subheader("Task Management Table")
        tasks_df = display_task_table()  # Fetch tasks DataFrame
        
        # Add Visualizations
        st.subheader("📊 Visualizations")
        
        # Task Status Distribution (Pie Chart)
        st.write("### Task Status Distribution")
        plot_task_status_distribution(tasks_df)
        
        # Task Priority Distribution (Bar Chart)
        st.write("### Task Priority Distribution")
        plot_task_priority_distribution(tasks_df)
        
        # Task Progress Over Time (Line Chart)
        st.write("### Task Progress Over Time")
        plot_task_progress_over_time(tasks_df)
        
        # Upcoming vs Overdue Tasks (Bar Chart)
        st.write("### Upcoming vs Overdue Tasks")
        plot_upcoming_vs_overdue_tasks(tasks_df)
        
        # Budget Tracking (Bar Chart)
        st.write("### Budget Tracking")
        plot_budget_tracking(tasks_df)

        # Add main title above "Total Projects in database"
        st.header("Edit Project Tasks")  # Main title

        # Fetch all projects for the logged-in user
        projects = get_projects()
        st.write(f"**Total Projects in database:** {len(projects)}")
        
        if not projects:
            st.warning("No projects found in the database.")
        else:
            # Group tasks by project
            for project in projects:
                with st.expander(f"Project: {project[2]}", expanded=True):  
                    st.write(f"**Description:** {project[3]}")
                    st.write(f"**Start Date:** {project[4]} | **End Date:** {project[5]}")
                    
                    # Fetch tasks for the current project
                    tasks = get_tasks(project[0])
                    st.write(f"**Tasks for project {project[2]}:**")
                    
                    if not tasks:
                        st.warning("No tasks found for this project.")
                    else:
                        # Use the custom drag-and-drop component for tasks
                        drag_and_drop(tasks)




            

           # Inside the task display loop
            projects = get_projects()
            for project in projects:
                tasks = get_tasks(project[0])
                
                if not tasks:
                    continue  # Skip projects with no assignee tasks
                    
                with st.expander(f"Project: {project[2]}"):
                    for task in tasks:
                        # Only show tasks where user is assignee
                        if not is_task_assignee(task):
                            continue
                            
                        # Display task info (read-only)
                        st.subheader(task[2])
                        st.caption(f"Project: {project[2]}")
                        
                        # COMPLETE EDIT FORM
                        with st.form(f"full_edit_{task[0]}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_title = st.text_input("Title", value=task[2])
                                new_desc = st.text_area("Description", value=task[3], height=100)
                                new_priority = st.selectbox(
                                    "Priority", 
                                    ["High", "Medium", "Low"],
                                    index=["High", "Medium", "Low"].index(task[8]) if task[8] in ["High", "Medium", "Low"] else 1
                                )
                                
                            with col2:
                                new_start = st.date_input(
                                    "Start Date",
                                    value=datetime.strptime(task[11], "%Y-%m-%d").date() if task[11] else datetime.now().date()
                                )
                                new_deadline = st.date_input(
                                    "Deadline",
                                    value=datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else datetime.now().date()
                                )
                                new_status = st.selectbox(
                                    "Status",
                                    ["Pending", "In Progress", "Completed"],
                                    index=["Pending", "In Progress", "Completed"].index(task[4])
                                )
                            
                            # Bottom section
                            new_budget = st.number_input("Budget", value=float(task[12]) if task[12] else 0.0)
                            new_actual = st.number_input("Actual Cost", value=float(task[13]) if task[13] else 0.0)
                            st.number_input("Variance", value=new_budget-new_actual, disabled=True)
                            
                            if st.form_submit_button("Save Changes"):
                                query_db("""
                                    UPDATE tasks SET
                                        title=?, description=?, priority=?,
                                        start_date=?, deadline=?, status=?,
                                        budget=?, actual_cost=?, budget_variance=?
                                    WHERE id=?
                                """, (
                                    new_title, new_desc, new_priority,
                                    new_start, new_deadline, new_status,
                                    new_budget, new_actual, new_budget-new_actual,
                                    task[0]
                                ))
                                st.rerun()
                        
                        # Delete button
                        if st.button(f"Delete This Task", key=f"del_{task[0]}"):
                            delete_task(task[0])
                            st.rerun()





                            # Deadline Tracking
                            deadline_status = get_task_status(task[6])
                            if deadline_status == "Overdue":
                                st.error(f"⚠️ Overdue: Deadline was {task[6]}")
                            elif deadline_status == "Upcoming":
                                st.warning(f"🔜 Upcoming: Deadline is {task[6]}")
                            else:
                                st.success(f"✅ On Track: Deadline is {task[6]}")



                            # Task Editing Form
                            # EDIT FORM - PROPERLY SCOPE ALL VARIABLES
                            with st.form(f"edit_task_{task[0]}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    new_title = st.text_input("Task Title", value=task[2])
                                    new_description = st.text_area("Description", value=task[3], height=100)
                                    new_priority = st.selectbox(
                                        "Priority",
                                        ["High", "Medium", "Low"],
                                        index=["High", "Medium", "Low"].index(task[8]) if task[8] in ["High", "Medium", "Low"] else 1
                                    )
                                    
                                with col2:
                                    new_start_date = st.date_input(
                                        "Start Date",
                                        value=datetime.strptime(task[11], "%Y-%m-%d").date() if task[11] else datetime.now().date()
                                    )
                                    new_deadline = st.date_input(
                                        "Deadline", 
                                        value=datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else datetime.now().date()
                                    )
                                    new_status = st.selectbox(
                                        "Status",
                                        ["Pending", "In Progress", "Completed"],
                                        index=["Pending", "In Progress", "Completed"].index(task[4])
                                    )
                                
                                # Budget Section
                                st.subheader("Budget Tracking")
                                budget_col1, budget_col2, budget_col3 = st.columns(3)
                                with budget_col1:
                                    new_budget = st.number_input(
                                        "Budget ($)", 
                                        min_value=0.0, 
                                        value=float(task[12]) if task[12] is not None else 0.0
                                    )
                                with budget_col2:
                                    new_actual_cost = st.number_input(
                                        "Actual Cost ($)", 
                                        min_value=0.0, 
                                        value=float(task[13]) if task[13] is not None else 0.0
                                    )
                                with budget_col3:
                                    new_budget_variance = st.number_input(
                                        "Variance ($)", 
                                        value=new_budget - new_actual_cost,
                                        disabled=True
                                    )
                                
                                # Assignment and Recurrence
                                team_members = query_db("SELECT id, username FROM users")
                                current_assignee = task[10] if len(task) > 10 else None
                                new_assignee = st.selectbox(
                                    "Assigned To",
                                    [member[1] for member in team_members],
                                    index=[m[0] for m in team_members].index(current_assignee) if current_assignee else 0
                                )
                                
                                new_recurrence = st.selectbox(
                                    "Recurrence",
                                    ["None", "Daily", "Weekly", "Monthly"],
                                    index=["None", "Daily", "Weekly", "Monthly"].index(task[9]) if task[9] in ["None", "Daily", "Weekly", "Monthly"] else 0
                                )

                                if st.form_submit_button("Update Task"):
                                    if user_can_edit_task(task):
                                        try:
                                            assigned_to_id = [m[0] for m in team_members if m[1] == new_assignee][0]
                                            query_db("""
                                                UPDATE tasks SET
                                                    title=?, description=?, priority=?,
                                                    start_date=?, deadline=?, status=?,
                                                    budget=?, actual_cost=?, budget_variance=?,
                                                    assigned_to=?, recurrence=?
                                                WHERE id=?
                                            """, (
                                                new_title, new_description, new_priority,
                                                new_start_date, new_deadline, new_status,
                                                new_budget, new_actual_cost, new_budget_variance,
                                                assigned_to_id, new_recurrence if new_recurrence != "None" else None,
                                                task[0]
                                            ))
                                            st.success("Task updated successfully!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating task: {str(e)}")
                                    else:
                                        st.warning("You don't have permission to edit this task")






    # Reports Page
    elif page == "Reports":
        st.title("📊 Reports")

        # Summary Statistics
        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_tasks = len(get_tasks())
            st.metric("Total Tasks", total_tasks)
        with col2:
            completed_tasks = len([task for task in get_tasks() if task[4] == "Completed"])
            st.metric("Completed Tasks", completed_tasks)
        with col3:
            overdue_tasks = len(get_upcoming_and_overdue_tasks()[1])
            st.metric("Overdue Tasks", overdue_tasks)

        # Project Health Dashboard
        st.subheader("📈 Project Health Dashboard")
        
        # Fetch all projects for the logged-in user
        projects = get_projects()
        
        if not projects:
            st.warning("No projects found in the database.")
        else:
            # Create columns for each project's health metrics
            for project in projects:
                with st.expander(f"Project: {project[2]}", expanded=False):
                    # Fetch tasks for the current project
                    tasks = get_tasks(project[0])
                    
                    if not tasks:
                        st.warning("No tasks found for this project.")
                    else:
                        # Calculate metrics
                        total_tasks = len(tasks)
                        completed_tasks = len([task for task in tasks if task[4] == "Completed"])
                        overdue_tasks = len([task for task in tasks if task[4] != "Completed" and datetime.strptime(task[6], "%Y-%m-%d").date() < datetime.today().date()])
                        
                        # On-time completion rate
                        on_time_completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                        
                        # Budget utilization
                        total_budget = sum([task[12] for task in tasks if task[12] is not None])  # Sum of all task budgets
                        actual_cost = sum([task[13] for task in tasks if task[13] is not None])  # Sum of all actual costs
                        budget_utilization = (actual_cost / total_budget) * 100 if total_budget > 0 else 0
                        
                        # Display metrics in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("On-Time Completion Rate", f"{on_time_completion_rate:.1f}%")
                        with col2:
                            st.metric("Overdue Tasks", overdue_tasks)
                        with col3:
                            st.metric("Budget Utilization", f"{budget_utilization:.1f}%")
                        
                        # Progress bar for budget utilization
                        st.progress(int(budget_utilization))
                        st.write(f"**Budget Used:** ${actual_cost:.2f} / ${total_budget:.2f}")

        # Budget Variance by Project
        st.subheader("📉 Budget Variance by Project")
        
        if not projects:
            st.warning("No projects found in the database.")
        else:
            # Calculate budget variance for each project
            budget_variance_data = []
            for project in projects:
                tasks = get_tasks(project[0])
                if tasks:
                    total_budget = sum([task[12] for task in tasks if task[12] is not None])  # Sum of all task budgets
                    actual_cost = sum([task[13] for task in tasks if task[13] is not None])  # Sum of all actual costs
                    budget_variance = total_budget - actual_cost
                    budget_variance_data.append({
                        "Project": project[2],  # Project name
                        "Budget Variance": budget_variance
                    })
            
            if budget_variance_data:
                # Convert to DataFrame
                budget_variance_df = pd.DataFrame(budget_variance_data)
                
                # Create a bar chart
                fig = px.bar(
                    budget_variance_df,
                    x="Project",
                    y="Budget Variance",
                    title="Budget Variance by Project",
                    labels={"Project": "Project", "Budget Variance": "Budget Variance ($)"},
                    color="Budget Variance",
                    color_continuous_scale=px.colors.diverging.RdBu,  # Red for negative, Blue for positive
                )
                st.plotly_chart(fig)
            else:
                st.info("No budget data available for visualization.")

        # Interactive Filters in Sidebar
        st.sidebar.subheader("Filters")

        # Filter by Project
        projects = query_db("SELECT id, name FROM projects WHERE user_id=?", (st.session_state.user_id,))
        project_names = [project[1] for project in projects]
        selected_projects = st.sidebar.multiselect(
            "Filter by Project",
            options=project_names,
            default=project_names
        )

        # Function to filter tasks by project
        def filter_tasks_by_project(tasks, selected_projects):
            filtered_tasks = []
            for task in tasks:
                project_name = query_db("SELECT name FROM projects WHERE id=?", (task[1],), one=True)[0]
                if project_name in selected_projects:
                    filtered_tasks.append(task)
            return filtered_tasks

        # Apply filters to tasks
        tasks = get_tasks()
        filtered_tasks = filter_tasks_by_project(tasks, selected_projects)

        # Task Timeline by Project (Gantt Chart)
        st.subheader("📅 Task Timeline by Project")
        if filtered_tasks:
            # Prepare data for the Gantt chart
            gantt_data = []
            for task in filtered_tasks:
                start_date = datetime.strptime(task[11], "%Y-%m-%d").date() if task[11] else datetime.today().date()
                deadline = datetime.strptime(task[6], "%Y-%m-%d").date()
                gantt_data.append({
                    "Task": task[2],  # Task title
                    "Start": start_date,
                    "Finish": deadline,
                    "Status": task[4],  # Task status
                    "Priority": task[8],  # Task priority
                    "Project": query_db("SELECT name FROM projects WHERE id=?", (task[1],), one=True)[0]  # Project name
                })
            
            # Create a DataFrame for the Gantt chart
            gantt_df = pd.DataFrame(gantt_data)
            
            # Create the Gantt chart using Plotly
            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status",
                title="Task Timeline by Project",
                labels={"Task": "Task", "Start": "Start Date", "Finish": "Deadline"},
                hover_data=["Priority", "Project"]  # Show priority and project in tooltips
            )
            st.plotly_chart(fig)
        else:
            st.info("No tasks found for the selected projects.")

        # Task Distribution by Assignee (Independent of Filters)
        st.subheader("👤 Task Distribution by Assignee")
        
        # Fetch all tasks (ignoring filters)
        all_tasks = get_tasks()
        
        if all_tasks:
            # Fetch assignee names for each task
            assignee_counts = {}
            for task in all_tasks:
                assignee_id = task[10]  # Assigned To field
                if assignee_id:
                    assignee = query_db("SELECT username FROM users WHERE id=?", (assignee_id,), one=True)
                    if assignee:
                        assignee_name = assignee[0]
                        assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
            
            if assignee_counts:
                # Convert to DataFrame
                assignee_df = pd.DataFrame(list(assignee_counts.items()), columns=["Assignee", "Number of Tasks"])
                
                # Create a bar chart
                fig = px.bar(
                    assignee_df,
                    x="Assignee",
                    y="Number of Tasks",
                    title="Task Distribution by Assignee",
                    labels={"Assignee": "Assignee", "Number of Tasks": "Number of Tasks"}
                )
                st.plotly_chart(fig)
            else:
                st.info("No tasks assigned to team members.")
        else:
            st.info("No tasks found in the database.")

        # Export Options
        st.subheader("📤 Export Reports")
        
        # List of tables available for export
        export_tables = [
            "users", "projects", "tasks", "subtasks", 
            "task_dependencies", "sqlite_sequence", "comments"
        ]
        
        # Select table to export
        selected_table = st.selectbox("Select Table to Export", export_tables)
        
        # Fetch data from the selected table
        if st.button("Export Data"):
            try:
                # Fetch data from the selected table
                query = f"SELECT * FROM {selected_table}"
                data = query_db(query)
                
                if data:
                    # Convert to DataFrame
                    export_df = pd.DataFrame(data)
                    
                    # Export as CSV
                    csv = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{selected_table}_report.csv",
                        mime="text/csv",
                    )
                    
                    # Export as Excel
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                        export_df.to_excel(writer, index=False)
                    excel_buffer.seek(0)
                    st.download_button(
                        label="Download Excel",
                        data=excel_buffer,
                        file_name=f"{selected_table}_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.warning(f"No data found in the {selected_table} table.")
            except Exception as e:
                st.error(f"An error occurred while exporting data: {e}")






    # Notifications Page
    elif page == "Notifications":
        st.title("🔔 Notifications")

        # Fetch overdue and upcoming tasks
        overdue_tasks, upcoming_tasks = get_upcoming_and_overdue_tasks()

        # Summary Statistics
        st.subheader("📊 Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overdue Tasks", len(overdue_tasks))
        with col2:
            st.metric("Upcoming Tasks", len(upcoming_tasks))

        # Filter Options in Sidebar
        st.sidebar.subheader("Filters")
        
        # Filter by Priority
        priority_filter = st.sidebar.multiselect(
            "Filter by Priority",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )
        
        # Filter by Project
        projects = query_db("SELECT id, name FROM projects WHERE user_id=?", (st.session_state.user_id,))
        project_names = [project[1] for project in projects]
        project_filter = st.sidebar.multiselect(
            "Filter by Project",
            options=project_names,
            default=project_names
        )
        
        # Filter by Deadline (for upcoming tasks)
        # Ensure deadline_filter is always a tuple with two elements
        deadline_filter = st.sidebar.date_input(
            "Filter by Deadline",
            value=[datetime.today(), datetime.today() + timedelta(days=7)],  # Default range: today to next 7 days
            key="deadline_filter"
        )

        # Ensure deadline_filter has exactly two elements
        if len(deadline_filter) != 2:
            st.error("Please select a valid date range.")
            st.stop()  # Stop execution if the date range is invalid

        # Function to filter tasks
        def filter_tasks(tasks, priority_filter, project_filter, deadline_filter):
            filtered_tasks = []
            for task in tasks:
                priority = task[8] if len(task) > 8 else "Medium"  # Handle missing priority
                project_name = query_db("SELECT name FROM projects WHERE id=?", (task[1],), one=True)[0]
                deadline = datetime.strptime(task[6], "%Y-%m-%d").date()
                
                # Apply filters
                if (priority in priority_filter and
                    project_name in project_filter and
                    (deadline >= deadline_filter[0] and deadline <= deadline_filter[1])):
                    filtered_tasks.append(task)
            return filtered_tasks

        # Apply filters to overdue and upcoming tasks
        filtered_overdue_tasks = filter_tasks(overdue_tasks, priority_filter, project_filter, deadline_filter)
        filtered_upcoming_tasks = filter_tasks(upcoming_tasks, priority_filter, project_filter, deadline_filter)

        # Collapsible Section for Overdue Tasks
        with st.expander("⚠️ Overdue Tasks", expanded=True):
            if filtered_overdue_tasks:
                for task in filtered_overdue_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    with st.container():
                        st.markdown(f"""
                            <div class="card" style="border: 2px solid {color}; border-radius: 8px; padding: 16px; margin: 10px;">
                                <div class="card-title" style="color: {color}; font-size: 1.25rem; font-weight: bold;">
                                    {task[2]} (Priority: {priority})
                                </div>
                                <div class="card-content" style="color: {st.session_state.color_scheme['text']};">
                                    <p><strong>Deadline:</strong> {task[6]}</p>
                                    <p><strong>Project:</strong> {query_db("SELECT name FROM projects WHERE id=?", (task[1],), one=True)[0]}</p>
                                </div>
                                <div class="card-footer">
                                    <button onclick="markAsDone({task[0]})">Mark as Done</button>
                                    <button onclick="snoozeTask({task[0]})">Snooze for 1 Day</button>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No overdue tasks matching the filters.")

        # Collapsible Section for Upcoming Tasks
        with st.expander("🔜 Upcoming Tasks", expanded=True):
            if filtered_upcoming_tasks:
                for task in filtered_upcoming_tasks:
                    priority = task[8] if len(task) > 8 else "Medium"
                    color = priority_colors.get(priority, "#000000")
                    with st.container():
                        st.markdown(f"""
                            <div class="card" style="border: 2px solid {color}; border-radius: 8px; padding: 16px; margin: 10px;">
                                <div class="card-title" style="color: {color}; font-size: 1.25rem; font-weight: bold;">
                                    {task[2]} (Priority: {priority})
                                </div>
                                <div class="card-content" style="color: {st.session_state.color_scheme['text']};">
                                    <p><strong>Deadline:</strong> {task[6]}</p>
                                    <p><strong>Project:</strong> {query_db("SELECT name FROM projects WHERE id=?", (task[1],), one=True)[0]}</p>
                                </div>
                                <div class="card-footer">
                                    <button onclick="markAsDone({task[0]})">Mark as Done</button>
                                    <button onclick="snoozeTask({task[0]})">Snooze for 1 Day</button>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No upcoming tasks matching the filters.")





    # Calendar Page
    elif page == "Calendar":
        st.title("📅 Calendar")

        # Fetch tasks and prepare them for the calendar
        tasks = fetch_calendar_events()

        # Define status colors
        status_colors = {
            "Pending": "#FFA500",  # Orange
            "In Progress": "#00BFFF",  # DeepSkyBlue
            "Completed": "#32CD32",  # LimeGreen
            "Overdue": "#FF4500"  # OrangeRed
        }

        # Filter Options in Sidebar
        st.sidebar.subheader("Filters")

        # Filter by Project
        projects = query_db("SELECT id, name FROM projects WHERE user_id=?", (st.session_state.user_id,))
        project_names = [project[1] for project in projects]
        selected_projects = st.sidebar.multiselect(
            "Filter by Project",
            options=project_names,
            default=project_names
        )

        # Filter by Priority
        priority_filter = st.sidebar.multiselect(
            "Filter by Priority",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )

        # Filter by Status
        status_filter = st.sidebar.multiselect(
            "Filter by Status",
            options=["Pending", "In Progress", "Completed"],
            default=["Pending", "In Progress", "Completed"]
        )

        # Apply filters to tasks
        filtered_tasks = [task for task in tasks if (
            task["Project"] in selected_projects and
            (task.get("Priority", "Medium") in priority_filter) and
            task["Status"] in status_filter
        )]

        # Prepare filtered events for the calendar
        filtered_calendar_events = []
        for task in filtered_tasks:
            event = {
                "title": task["Task"],  # Task title
                "start": task["Date"],  # Task deadline
                "color": status_colors.get(task["Status"], "#f0f0f0"),  # Color based on status
                "extendedProps": {
                    "status": task["Status"],
                    "project": task["Project"],
                    "task_id": task["Task ID"]  # Add task ID for reference
                }
            }
            filtered_calendar_events.append(event)

        # Configure the calendar
        calendar_options = {
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
            },
            "initialView": "dayGridMonth",  # Default view
            "editable": True,  # Allow dragging and dropping tasks
            "selectable": True,  # Allow selecting dates
            "events": filtered_calendar_events,  # Add filtered tasks as events
            "eventClick": True,  # Enable event click callback
            "dateClick": True,  # Enable date click callback
            "eventDrop": True  # Enable event drop callback
        }

        # Display the filtered calendar
        calendar_result = calendar(events=filtered_calendar_events, options=calendar_options)

        # Handle the calendar result
        if calendar_result:
            if "eventClick" in calendar_result:  # Handle event click
                event = calendar_result["eventClick"]["event"]
                st.subheader(f"Task Details: {event['title']}")
                st.write(f"**Status:** {event['extendedProps']['status']}")
                st.write(f"**Project:** {event['extendedProps']['project']}")
                st.write(f"**Deadline:** {event['start']}")

            elif "dateClick" in calendar_result:  # Handle date click
                selected_date = calendar_result["dateClick"]["date"]
                st.subheader(f"Tasks for {selected_date}")
                
                # Filter tasks for the selected date
                tasks_for_date = [task for task in filtered_tasks if task["Date"] == selected_date]
                
                if tasks_for_date:
                    for task in tasks_for_date:
                        st.markdown(f"""
                            - **Task:** {task["Task"]}
                            - **Status:** {task["Status"]}
                            - **Project:** {task["Project"]}
                        """)
                else:
                    st.info("No tasks found for this date.")

            elif "eventDrop" in calendar_result:  # Handle event drop (drag-and-drop)
                event = calendar_result["eventDrop"]["event"]
                new_deadline = event["start"]
                task_id = event["extendedProps"]["task_id"]

                # Confirmation dialog
                if st.confirm(f"Are you sure you want to reschedule '{event['title']}' to {new_deadline}?"):
                    # Debugging: Print the task ID and new deadline
                    print(f"Updating task {task_id} to new deadline: {new_deadline}")

                    # Update the task deadline in the database
                    try:
                        query_db("UPDATE tasks SET deadline=? WHERE id=?", (new_deadline, task_id))
                        print("Database update successful!")
                    except Exception as e:
                        print(f"Database update failed: {e}")

                    st.success(f"Task '{event['title']}' rescheduled to {new_deadline}!")
                    st.rerun()  # Rerun the app to reflect changes

        # Export Calendar
        st.sidebar.subheader("Export Calendar")
        if st.sidebar.button("Export as iCal"):
            # Generate iCal file (example implementation)
            ical_content = "BEGIN:VCALENDAR\nVERSION:2.0\n"
            for task in filtered_tasks:
                ical_content += f"""
    BEGIN:VEVENT
    SUMMARY:{task["Task"]}
    DESCRIPTION:{task["Project"]}
    DTSTART:{task["Date"].replace("-", "")}
    DTEND:{task["Date"].replace("-", "")}
    END:VEVENT
    """
            ical_content += "END:VCALENDAR"

            # Provide the iCal file for download
            st.sidebar.download_button(
                label="Download iCal File",
                data=ical_content,
                file_name="tasks_calendar.ics",
                mime="text/calendar"
            )
            st.sidebar.success("Calendar exported successfully!")




    # Admin Page
    elif page == "Admin":
        st.title("👤 Admin Dashboard")

        # Summary Statistics
        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_users = len(query_db("SELECT * FROM users"))
            st.metric("Total Users", total_users)
        with col2:
            total_projects = len(query_db("SELECT * FROM projects"))
            st.metric("Total Projects", total_projects)
        with col3:
            active_projects = len(query_db("SELECT * FROM projects WHERE end_date >= ?", (datetime.today().date(),)))
            st.metric("Active Projects", active_projects)

        # User Management Section
        st.subheader("👥 User Management")

        # Add New User Form
        with st.expander("➕ Add New User", expanded=False):
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["User", "Admin"])
                new_email = st.text_input("Email")
                new_phone = st.text_input("Phone")

                if st.form_submit_button("Add User"):
                    if query_db("SELECT * FROM users WHERE username=?", (new_username,), one=True):
                        st.error("Username already exists.")
                    else:
                        query_db("""
                            INSERT INTO users (username, password, role, email, phone)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            new_username,
                            hash_password(new_password),
                            new_role,
                            new_email,
                            new_phone
                        ))
                        st.success("User added successfully!")
                        st.rerun()

        # Display Users in a Table
        st.write("### User List")
        users = query_db("SELECT id, username, role, email, phone FROM users")
        if users:
            user_df = pd.DataFrame(users, columns=["ID", "Username", "Role", "Email", "Phone"])
            st.dataframe(user_df, use_container_width=True)
        else:
            st.info("No users found.")

        # Edit and Delete Users
        st.write("### Edit or Delete Users")
        for user in users:
            with st.expander(f"Edit User: {user[1]}", expanded=False):
                with st.form(f"edit_user_{user[0]}"):
                    new_username = st.text_input("Username", value=user[1])
                    new_password = st.text_input("Password", type="password", placeholder="Leave blank to keep current password")
                    new_role = st.selectbox("Role", ["User", "Admin"], index=["User", "Admin"].index(user[2]))
                    new_email = st.text_input("Email", value=user[3])
                    new_phone = st.text_input("Phone", value=user[4])

                    if st.form_submit_button("Update User"):
                        if new_password:
                            query_db("""
                                UPDATE users
                                SET username=?, password=?, role=?, email=?, phone=?
                                WHERE id=?
                            """, (
                                new_username,
                                hash_password(new_password),
                                new_role,
                                new_email,
                                new_phone,
                                user[0]
                            ))
                        else:
                            query_db("""
                                UPDATE users
                                SET username=?, role=?, email=?, phone=?
                                WHERE id=?
                            """, (
                                new_username,
                                new_role,
                                new_email,
                                new_phone,
                                user[0]
                            ))
                        st.success("User updated successfully!")
                        st.rerun()

                if st.button(f"Delete User {user[1]}"):
                    if user[0] == st.session_state.user_id:
                        st.error("You cannot delete your own account.")
                    else:
                        query_db("DELETE FROM users WHERE id=?", (user[0],))
                        st.success("User deleted successfully!")
                        st.rerun()

        # Project Management Section
        st.subheader("📂 Project Management")

        # Display Projects in a Table
        projects = query_db("SELECT id, name, description, start_date, end_date FROM projects")
        if projects:
            project_df = pd.DataFrame(projects, columns=["ID", "Name", "Description", "Start Date", "End Date"])
            st.dataframe(project_df, use_container_width=True)
        else:
            st.info("No projects found.")

        # Edit and Delete Projects
        st.write("### Edit or Delete Projects")
        for project in projects:
            with st.expander(f"Edit Project: {project[1]}", expanded=False):
                with st.form(f"edit_project_{project[0]}"):
                    new_name = st.text_input("Project Name", value=project[1])
                    new_description = st.text_area("Description", value=project[2])
                    new_start_date = st.date_input("Start Date", value=datetime.strptime(project[3], "%Y-%m-%d").date())
                    new_end_date = st.date_input("End Date", value=datetime.strptime(project[4], "%Y-%m-%d").date())

                    if st.form_submit_button("Update Project"):
                        query_db("""
                            UPDATE projects
                            SET name=?, description=?, start_date=?, end_date=?
                            WHERE id=?
                        """, (
                            new_name,
                            new_description,
                            new_start_date,
                            new_end_date,
                            project[0]
                        ))
                        st.success("Project updated successfully!")
                        st.rerun()

                if st.button(f"Delete Project {project[1]}", key=f"delete_button_{project[0]}"):
                    delete_project(project[0])
                    st.success("Project deleted successfully!")
                    st.rerun()


        # System Settings Section
        st.subheader("⚙️ System Settings")
        with st.expander("Customize System Settings", expanded=False):
            with st.form("system_settings_form"):
                default_reminder_period = st.number_input("Default Reminder Period (days)", min_value=1, value=7)
                enable_email_notifications = st.checkbox("Enable Email Notifications", value=True)

                if st.form_submit_button("Save Settings"):
                    st.session_state.reminder_period = default_reminder_period
                    st.success("System settings updated successfully!")
                    st.rerun()
    



    # Profile Page
    elif page == "Profile":
        st.title("👤 Profile")

        # Fetch current user data
        user = query_db("SELECT * FROM users WHERE id=?", (st.session_state.user_id,), one=True)
        if not user:
            st.error("User not found.")
            st.stop()  # Stop execution if user is not found

        # Display Profile Picture
        st.subheader("🖼️ Profile Picture")
        if len(user) > 11 and user[11]:  # Check if profile_picture exists
            st.image(user[11], width=150, caption="Current Profile Picture", use_container_width=False)  # Updated parameter
        else:
            st.write("No profile picture uploaded.")

        # Upload New Profile Picture
        uploaded_file = st.file_uploader("Upload a new profile picture", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            profile_picture = uploaded_file.read()
            query_db("UPDATE users SET profile_picture=? WHERE id=?", (profile_picture, st.session_state.user_id))
            st.success("Profile picture updated successfully!")
            st.rerun()

        # Display User Information
        st.subheader("📝 Profile Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Username:** {user[1]}")
            st.write(f"**Email:** {user[9]}")
        with col2:
            st.write(f"**Phone:** {user[10]}")
            st.write(f"**Role:** {user[3]}")

        # Edit Profile Form
        st.subheader("✏️ Edit Profile")
        with st.form("edit_profile_form"):
            new_email = st.text_input("Email", value=user[9])
            new_phone = st.text_input("Phone", value=user[10])
            new_first_name = st.text_input("First Name", value=user[4])
            new_last_name = st.text_input("Last Name", value=user[5])
            new_job_title = st.text_input("Job Title", value=user[7])
            new_department = st.text_input("Department", value=user[8])

            if st.form_submit_button("Update Profile"):
                query_db("""
                    UPDATE users
                    SET email=?, phone=?, first_name=?, last_name=?, job_title=?, department=?
                    WHERE id=?
                """, (
                    new_email,
                    new_phone,
                    new_first_name,
                    new_last_name,
                    new_job_title,
                    new_department,
                    st.session_state.user_id
                ))
                st.success("Profile updated successfully!")
                st.rerun()

        # Change Password
        st.subheader("🔒 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Change Password"):
                if not verify_password(user[2], current_password):
                    st.error("Current password is incorrect.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    query_db("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), st.session_state.user_id))
                    st.success("Password updated successfully!")
                    st.rerun()

        # Activity Summary
        st.subheader("📊 Activity Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            tasks_assigned = len(get_tasks())
            st.metric("Tasks Assigned", tasks_assigned)
        with col2:
            tasks_completed = len([task for task in get_tasks() if task[4] == "Completed"])
            st.metric("Tasks Completed", tasks_completed)
        with col3:
            projects_involved = len(get_projects())
            st.metric("Projects Involved", projects_involved)

        # Visualize Activity
        st.write("### Task Completion Trends")
        if tasks_assigned > 0:
            completion_rate = (tasks_completed / tasks_assigned) * 100
            fig_completion = px.pie(
                names=["Completed", "Pending"],
                values=[tasks_completed, tasks_assigned - tasks_completed],
                title="Task Completion Rate"
            )
            st.plotly_chart(fig_completion)
        else:
            st.info("No tasks assigned.")



    
    
    
    
    # Documentation Page
    elif page == "Documentation":
        st.title("📚 Documentation")

        # Introduction
        st.write("Welcome to the **Project Management App Documentation**! This guide will help you get started with the app and make the most of its features.")

        # Getting Started
        with st.expander("🚀 Getting Started", expanded=True):
            st.write("""
            ### 1. **Create an Account**
            - If you're a new user, click on the **Register** button on the login page to create an account.
            - Fill in your details (e.g., username, password, email) and click **Register**.

            ### 2. **Log In**
            - Enter your username and password on the login page and click **Login**.

            ### 3. **Explore the Dashboard**
            - After logging in, you'll be taken to the **Dashboard**, where you can see an overview of your projects and tasks.
            """)

        # Projects
        with st.expander("📂 Projects", expanded=False):
            st.write("""
            ### 1. **Create a Project**
            - Go to the **Projects** page and click **Add Project**.
            - Fill in the project details (e.g., name, description, start date, end date) and click **Save**.

            ### 2. **Edit or Delete a Project**
            - On the **Projects** page, click the **Edit** or **Delete** button next to the project you want to modify.

            ### 3. **View Project Details**
            - Click on a project to view its details, including tasks, progress, and deadlines.
            """)

        # Tasks
        with st.expander("✅ Tasks", expanded=False):
            st.write("""
            ### 1. **Add a Task**
            - Go to the **Tasks** page and click **Add Task**.
            - Fill in the task details (e.g., title, description, deadline, priority) and click **Save**.

            ### 2. **Update Task Status**
            - On the **Tasks** page, use the status dropdown to update the task status (e.g., Pending, In Progress, Completed).

            ### 3. **Track Task Progress**
            - Use the **Gantt Chart** on the **Dashboard** or **Tasks** page to track task progress and deadlines.
            """)

        # Reports
        with st.expander("📊 Reports", expanded=False):
            st.write("""
            ### 1. **Generate Reports**
            - Go to the **Reports** page to view time tracking and task completion trends.
            - Use the filters to customize the report (e.g., by project, priority, date range).

            ### 2. **Export Reports**
            - Click the **Export** button to download the report as a CSV or Excel file.
            """)

        # Notifications
        with st.expander("🔔 Notifications", expanded=False):
            st.write("""
            ### 1. **View Notifications**
            - Go to the **Notifications** page to see overdue and upcoming tasks.
            - Use the filters to customize the notifications (e.g., by project, priority).

            ### 2. **Customize Reminders**
            - On the **Notifications** page, set the reminder period for upcoming tasks.
            """)

        # Profile
        with st.expander("👤 Profile", expanded=False):
            st.write("""
            ### 1. **Update Your Profile**
            - Go to the **Profile** page to update your personal information (e.g., email, phone, job title).
            - Upload a profile picture by clicking **Upload a new profile picture**.

            ### 2. **Change Password**
            - On the **Profile** page, click **Change Password** to update your password.
            """)

        # Admin
        if st.session_state.user_role == "Admin":
            with st.expander("👤 Admin", expanded=False):
                st.write("""
                ### 1. **Manage Users**
                - Go to the **Admin** page to view, add, edit, or delete users.
                - Assign roles (e.g., User, Admin) to control access to features.

                ### 2. **Manage Projects**
                - On the **Admin** page, view and manage all projects in the system.
                """)

        # FAQs
        with st.expander("❓ FAQs", expanded=False):
            st.write("""
            ### 1. **How do I reset my password?**
            - Go to the **Profile** page and click **Change Password**. Enter your current password and set a new one.

            ### 2. **How do I filter tasks by project?**
            - On the **Tasks** or **Reports** page, use the project filter in the sidebar to select the project you want to view.

            ### 3. **How do I export a report?**
            - On the **Reports** page, click the **Export** button and select the format (e.g., CSV, Excel).
            """)

        # Keyboard Shortcuts
        with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
            st.write("""
            - **Ctrl + S**: Save changes.
            - **Ctrl + F**: Search for tasks or projects.
            - **Ctrl + P**: Print the current page.
            """)

        # Best Practices
        with st.expander("🌟 Best Practices", expanded=False):
            st.write("""
            ### 1. **Organize Your Projects**
            - Use clear and descriptive names for your projects and tasks.
            - Set realistic deadlines and priorities.

            ### 2. **Track Your Progress**
            - Regularly update task statuses and time spent to keep your projects on track.

            ### 3. **Use Filters**
            - Use filters on the **Tasks**, **Reports**, and **Notifications** pages to focus on specific data.
            """)

    
