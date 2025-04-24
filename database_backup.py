import sqlite3 

def init_db():
    conn = sqlite3.connect('project_management.db')
    c = conn.cursor()
    
    # Create users table with a role column
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User'  -- Default role is 'User'
        )
    ''')
    
    # Check if the role column exists, and if not, add it
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'role' not in column_names:
        # Add the role column with a default value of 'User'
        c.execute('ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT "User"')
    
    # Create projects table with user_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create tasks table
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
            priority TEXT DEFAULT 'Medium',  -- Priority column
            recurrence TEXT,  -- Recurrence pattern (e.g., daily, weekly, monthly)
            assigned_to INTEGER,  -- New: Assign task to a user
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    ''')
    
    # Check if the priority column exists, and if not, add it
    c.execute("PRAGMA table_info(tasks)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'priority' not in column_names:
        # Add the priority column with a default value of 'Medium'
        c.execute('ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT "Medium"')
    
    # Check if the recurrence column exists, and if not, add it
    if 'recurrence' not in column_names:
        # Add the recurrence column
        c.execute('ALTER TABLE tasks ADD COLUMN recurrence TEXT')
    
    # Check if the assigned_to column exists, and if not, add it
    if 'assigned_to' not in column_names:
        # Add the assigned_to column
        c.execute('ALTER TABLE tasks ADD COLUMN assigned_to INTEGER')
    
    # Create task_dependencies table
    c.execute('''
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,  -- Task that depends on another task
            depends_on_task_id INTEGER,  -- Task that must be completed first
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (depends_on_task_id) REFERENCES tasks (id)
        )
    ''')
    
    # Create comments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,  -- Task the comment belongs to
            user_id INTEGER,  -- User who posted the comment
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create subtasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    ''')
    
    # Create attachments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect('project_management.db')
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Initialize the database
init_db()