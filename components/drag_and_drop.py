import streamlit.components.v1 as components
from database import query_db  # Import the query_db function

def drag_and_drop(tasks):
    """
    A custom Streamlit component for drag-and-drop functionality.
    """
    # Define status colors
    status_colors = {
        "Pending": "#FFA500",  # Orange
        "In Progress": "#00BFFF",  # DeepSkyBlue
        "Completed": "#32CD32",  # LimeGreen
        "Overdue": "#FF4500"  # OrangeRed
    }

    # Calculate dynamic height based on the number of tasks
    base_height = 400  # Base height for the container
    task_height = 50   # Height per task
    max_height = 800   # Maximum height to avoid the container becoming too large
    container_height = min(base_height + (len(tasks) * task_height), max_height)

    # HTML and JavaScript for drag-and-drop
    html_code = f"""
    <style>
        .task-item {{
            position: relative;
            padding: 10px;
            margin: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: grab;
            background-color: #ffffff;  /* Default background color */
            font-family: sans-serif;  /* Match Streamlit's font family */
        }}
        .status-badge {{
            position: absolute;
            top: 5px;
            right: 5px;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            color: #ffffff;  /* White text */
            font-family: sans-serif;  /* Match Streamlit's font family */
        }}
        .assignee {{
            position: absolute;
            bottom: 5px;
            right: 5px;
            font-size: 12px;
            color: #555555;  /* Dark gray text */
            font-family: sans-serif;  /* Match Streamlit's font family */
        }}
    </style>

    <div id="task-list" style="padding: 10px; border: 1px solid #ccc; border-radius: 5px; height: {container_height}px; overflow-y: auto;">
        {"".join([
            f'<div class="task-item" id="task-{task[0]}" style="background-color: {status_colors.get(task[4], "#f0f0f0")};">'
            f'<div class="status-badge" style="background-color: {status_colors.get(task[4], "#f0f0f0")};">{task[4]}</div>'
            f'<strong>{task[2]}</strong><br>'
            f'Deadline: {task[6]}'
            f'<div class="assignee">Assigned to: {query_db("SELECT username FROM users WHERE id=?", (task[10],), one=True)[0] if task[10] else "Unassigned"}</div>'
            f'</div>'
            for task in tasks
        ])}
    </div>

    <script>
        function allowDrop(ev) {{
            ev.preventDefault();
        }}

        function drag(ev) {{
            ev.dataTransfer.setData("text", ev.target.id);
        }}

        function drop(ev) {{
            ev.preventDefault();
            var data = ev.dataTransfer.getData("text");
            ev.target.appendChild(document.getElementById(data));
        }}

        // Make all task elements draggable
        document.querySelectorAll('.task-item').forEach(function(element) {{
            element.setAttribute('draggable', true);
            element.addEventListener('dragstart', drag);
        }});

        // Make the task list droppable
        document.getElementById('task-list').addEventListener('drop', drop);
        document.getElementById('task-list').addEventListener('dragover', allowDrop);
    </script>
    """

    # Render the HTML/JavaScript in Streamlit
    components.html(html_code, height=container_height + 50)  # Add extra padding for the container