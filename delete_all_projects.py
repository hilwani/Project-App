import sqlite3

def delete_all_projects():
    # Connect to the SQLite database
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    try:
        # Execute the DELETE statement to remove all projects
        cursor.execute("DELETE FROM projects")
        
        # Commit the transaction
        conn.commit()
        print("All projects and related tasks deleted successfully.")
    
    except sqlite3.Error as e:
        # Handle any errors
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        conn.close()

# Example usage
delete_all_projects() 