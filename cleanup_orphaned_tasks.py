import sqlite3

def clean_up_orphaned_tasks():
    # Connect to the SQLite database
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    try:
        # Execute the cleanup query
        cursor.execute("DELETE FROM tasks WHERE project_id NOT IN (SELECT id FROM projects);")
        
        # Commit the transaction
        conn.commit()
        
        # Print the number of orphaned tasks deleted
        print(f"Deleted {cursor.rowcount} orphaned tasks.")
    
    except sqlite3.Error as e:
        # Handle any errors
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        conn.close()

# Run the cleanup function
clean_up_orphaned_tasks()