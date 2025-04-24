import sqlite3

def delete_all_tasks():
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    try:
        # Execute the DELETE statement to remove all tasks
        cursor.execute("DELETE FROM tasks")
        
        # Commit the transaction
        conn.commit()
        print("All tasks deleted successfully.")
    
    except sqlite3.Error as e:
        # Handle any errors
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        conn.close()

# Example usage
delete_all_tasks()