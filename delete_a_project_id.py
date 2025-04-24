import sqlite3 

def delete_project(project_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    try:
        # Execute the DELETE statement to remove the project
        cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
        
        # Commit the transaction
        conn.commit()
        print(f"Project with ID {project_id} and all related tasks deleted successfully.")
    
    except sqlite3.Error as e:
        # Handle any errors
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        conn.close()

# Example usage
project_id_to_delete = 40  # Replace with the actual project ID you want to delete
delete_project(project_id_to_delete)