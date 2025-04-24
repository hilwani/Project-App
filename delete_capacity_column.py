import sqlite3

def delete_capacity_column():
    # Connect to the SQLite database
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()

    try:
        # Step 1: Create a new table without the capacity column
        cursor.execute('''
            CREATE TABLE tasks_new (
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
                start_date TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            );
        ''')

        # Step 2: Copy data from the old table to the new table
        cursor.execute('''
            INSERT INTO tasks_new (id, project_id, title, description, status, created_at, deadline, time_spent, priority, recurrence, assigned_to, start_date)
            SELECT id, project_id, title, description, status, created_at, deadline, time_spent, priority, recurrence, assigned_to, start_date
            FROM tasks;
        ''')

        # Step 3: Drop the old table
        cursor.execute('DROP TABLE tasks;')

        # Step 4: Rename the new table to the original table name
        cursor.execute('ALTER TABLE tasks_new RENAME TO tasks;')

        # Step 5: Recreate indexes and constraints (if needed)
        cursor.execute('CREATE INDEX idx_project_id ON tasks (project_id);')

        # Commit the changes
        conn.commit()
        print("Capacity column removed successfully!")

    except sqlite3.Error as e:
        # Rollback in case of error
        conn.rollback()
        print(f"An error occurred: {e}")

    finally:
        # Close the database connection
        conn.close()

# Call the function to delete the capacity column
delete_capacity_column()