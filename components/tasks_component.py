# Create new file for reusable task components
from utils import query_db
import pandas as pd
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.express as px
from utils import get_projects, get_team_members, save_task





# Add to task_page.py's show_task_page()
def display_task_table(tasks):
    # Convert to DataFrame with proper columns
    df = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Status",
                                     "Created", "Deadline", "Time Spent",
                                     "Priority", "Project ID", "Assignee"])
    
    # Add filtering controls
    with st.expander("🔍 Filter Tasks", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=df['Status'].unique(),
                default=df['Status'].unique()
            )
        with col2:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=df['Priority'].unique(),
                default=df['Priority'].unique()
            )
        with col3:
            assignee_filter = st.multiselect(
                "Filter by Assignee",
                options=df['Assignee'].unique(),
                default=df['Assignee'].unique()
            )
    
    # Apply filters
    filtered_df = df[
        (df['Status'].isin(status_filter)) &
        (df['Priority'].isin(priority_filter)) &
        (df['Assignee'].isin(assignee_filter))
    ]
    
    # Enhanced display
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "Deadline": st.column_config.DateColumn("Deadline"),
            "Time Spent": st.column_config.NumberColumn("Hours"),
            "Priority": st.column_config.SelectboxColumn(
                "Priority",
                options=["High", "Medium", "Low"]
            )
        },
        hide_index=True
    )


# Move status_badge to AFTER display_task_table
def status_badge(status):
    color = {
        "Pending": "orange",
        "In Progress": "blue",
        "Completed": "green",
        "Overdue": "red"
    }.get(status, "gray")
    return f"<span style='color:white; background-color:{color}; padding:2px 8px; border-radius:12px;'>{status}</span>"

# Add this new function
def show_task_progress(tasks):
    if not tasks:
        return st.warning("No tasks to analyze")
    
    df = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Status",
                                     "Created", "Deadline", "Time Spent",
                                     "Priority", "Project ID", "Assignee"])
    
    # Completion rate
    completed = df[df['Status'] == "Completed"].shape[0]
    progress = completed / df.shape[0]
    
    st.metric("Completion Rate", f"{progress:.0%}")
    st.progress(progress)
    
    # Priority distribution
    fig = px.pie(df, names='Priority', title='Tasks by Priority')
    st.plotly_chart(fig)







def task_creation_form():
    with st.form("create_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Task Title*", placeholder="Enter task name")
            project = st.selectbox("Project*", get_projects())
            assignee = st.selectbox("Assignee", get_team_members())
        with col2:
            priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
            deadline = st.date_input("Deadline*", min_value=datetime.today())
        
        description = st.text_area("Description", height=100)
        subtasks = st.text_area("Subtasks (one per line)")
        
        if st.form_submit_button("Create Task"):
            # Validation and save logic
            if not title.strip():
                st.error("Title is required")
            else:
                save_task(title, description, project, assignee, priority, deadline, subtasks)
                st.success("Task created!")
                st.rerun()




def show_task_dependencies(task_id):
    dependencies = query_db("""
        SELECT t.id, t.title 
        FROM task_dependencies td
        JOIN tasks t ON td.depends_on_task_id = t.id
        WHERE td.task_id = ?
    """, (task_id,))
    
    if dependencies:
        st.subheader("🔗 Dependencies")
        for dep in dependencies:
            st.write(f"- {dep[1]} (ID: {dep[0]})")
        
        # Visual graph
        try:
            import networkx as nx
            G = nx.DiGraph()
            G.add_node(task_id)
            for dep in dependencies:
                G.add_node(dep[0])
                G.add_edge(task_id, dep[0])
            
            pos = nx.spring_layout(G)
            fig, ax = plt.subplots()
            nx.draw(G, pos, with_labels=True, ax=ax)
            st.pyplot(fig)
        except ImportError:
            st.warning("Install networkx and matplotlib for dependency graphs")