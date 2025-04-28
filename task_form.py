def edit_task_form(task_id, project_id):
    task = query_db("SELECT * FROM tasks WHERE id=?", (task_id,), one=True)
    if not task:
        st.error("Task not found")
        return False
    
    # Main task editing form - using a container with consistent styling
    with st.container():
        st.markdown("### Edit Task")
        with st.form(key=f"edit_task_form_{task_id}"):
            # Two-column layout for better organization
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Task Title*", value=task[2])
                description = st.text_area("Description", value=task[3] or "")
                
                # Status and priority in the same row
                status_col, priority_col = st.columns(2)
                with status_col:
                    status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], 
                                        index=["Pending", "In Progress", "Completed"].index(task[4]))
                with priority_col:
                    priority = st.selectbox("Priority*", ["High", "Medium", "Low"], 
                                          index=["High", "Medium", "Low"].index(task[8]))
            
            with col2:
                # Date fields in the same row
                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    try:
                        task_start_date = datetime.strptime(task[5], "%Y-%m-%d").date() if task[5] else datetime.today().date()
                    except ValueError:
                        task_start_date = datetime.strptime(task[5], "%Y-%m-%d %H:%M:%S").date() if task[5] else datetime.today().date()
                    start_date = st.date_input("Start Date*", value=task_start_date)
                with date_col2:
                    try:
                        task_deadline = datetime.strptime(task[6], "%Y-%m-%d").date() if task[6] else datetime.today().date()
                    except ValueError:
                        task_deadline = datetime.strptime(task[6], "%Y-%m-%d %H:%M:%S").date() if task[6] else datetime.today().date()
                    deadline = st.date_input("Deadline*", value=task_deadline)
                
                # Budget and assignee
                budget = st.number_input("Budget ($)", min_value=0.0, value=float(task[12] or 0), step=0.01)
                
                team_members = query_db("SELECT id, username FROM users ORDER BY username")
                assigned_to = st.selectbox("Assign To", [member[1] for member in team_members], 
                                         index=[member[1] for member in team_members].index(
                                             query_db("SELECT username FROM users WHERE id=?", (task[10],), one=True)[0]))
            
            # Form submission buttons
            submit_col1, submit_col2 = st.columns(2)
            with submit_col1:
                submitted = st.form_submit_button("Update Task")
            with submit_col2:
                cancel = st.form_submit_button("Cancel")
            
            if submitted:
                if not title.strip():
                    st.error("Task title is required")
                elif deadline < start_date:
                    st.error("Deadline must be on or after the start date")
                else:
                    assigned_to_id = query_db(
                        "SELECT id FROM users WHERE username = ?", 
                        (assigned_to,), 
                        one=True
                    )[0]
                    
                    query_db("""
                        UPDATE tasks 
                        SET title=?, description=?, status=?, start_date=?, deadline=?, 
                        priority=?, assigned_to=?, budget=?
                        WHERE id=?
                    """, (
                        title.strip(), description, status, start_date, deadline, 
                        priority, assigned_to_id, budget, task_id
                    ))
                    
                    st.success("Task updated successfully!")
                    return True
            if cancel:
                return False
    
    # Subtask section - redesigned with consistent styling
    # Subtask section - completely reworked assignment handling
    st.markdown("---")
    st.subheader("Subtasks Management")
    
    # Get all subtasks with proper assignment handling
    subtasks = query_db("""
        SELECT s.id, s.title, s.description, s.status, s.start_date, s.deadline, 
               s.priority, s.assigned_to, s.budget, s.time_spent, u.username
        FROM subtasks s
        LEFT JOIN users u ON s.assigned_to = u.id
        WHERE s.task_id=?
        ORDER BY s.id
    """, (task_id,))
    
    if subtasks:
        st.write("### Current Subtasks")
        
        # Create a DataFrame with proper assignment display
        subtasks_df = pd.DataFrame(subtasks, columns=[
            "ID", "Title", "Description", "Status", "Start Date", "Deadline",
            "Priority", "Assigned To ID", "Budget", "Time Spent", "Assigned To"
        ])
        
        # Replace None with "Unassigned" for display
        subtasks_df["Assigned To"] = subtasks_df["Assigned To"].fillna("Unassigned")
        
        # Display the subtasks table
        st.dataframe(
            subtasks_df[["ID", "Title", "Status", "Priority", "Assigned To", 
                        "Start Date", "Deadline", "Budget", "Time Spent"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Start Date": st.column_config.DateColumn("Start Date"),
                "Deadline": st.column_config.DateColumn("Deadline"),
                "Budget": st.column_config.NumberColumn("Budget", format="$%.2f"),
                "Time Spent": st.column_config.NumberColumn("Time Spent (hrs)")
            }
        )
        
        # Subtask management form with reliable assignment handling
        st.markdown("---")
        st.subheader("Manage Subtask")
        
        if subtasks:
            selected_subtask = st.selectbox(
                "Select Subtask to Manage",
                [f"{subtask[0]}: {subtask[1]}" for subtask in subtasks],
                index=0,
                key="subtask_selector"
            )
            
            if selected_subtask:
                subtask_id = int(selected_subtask.split(":")[0])
                subtask = next((s for s in subtasks if s[0] == subtask_id), None)
                
                if subtask:
                    with st.form(key=f"manage_subtask_{subtask_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            subtask_title = st.text_input("Title", value=subtask[1])
                            subtask_description = st.text_area(
                                "Description", 
                                value=subtask[2] or ""
                            )
                            
                            status_col, priority_col = st.columns(2)
                            with status_col:
                                subtask_status = st.selectbox(
                                    "Status", 
                                    ["Pending", "In Progress", "Completed"], 
                                    index=["Pending", "In Progress", "Completed"].index(subtask[3])
                                )
                            with priority_col:
                                subtask_priority = st.selectbox(
                                    "Priority", 
                                    ["High", "Medium", "Low"], 
                                    index=["High", "Medium", "Low"].index(subtask[6])
                                )
                        
                        with col2:
                            date_col1, date_col2 = st.columns(2)
                            with date_col1:
                                subtask_start_date = st.date_input(
                                    "Start Date", 
                                    value=datetime.strptime(subtask[4], "%Y-%m-%d").date() if subtask[4] else start_date
                                )
                            with date_col2:
                                subtask_deadline = st.date_input(
                                    "Deadline", 
                                    value=datetime.strptime(subtask[5], "%Y-%m-%d").date() if subtask[5] else deadline
                                )
                            
                            subtask_budget = st.number_input(
                                "Budget ($)", 
                                min_value=0.0, 
                                value=float(subtask[8] or 0), 
                                step=0.01
                            )
                            
                            # Get all available users
                            team_members = query_db("SELECT id, username FROM users ORDER BY username")
                            assignee_options = ["Unassigned"] + [member[1] for member in team_members]
                            
                            # Find current assignee
                            current_assignee = "Unassigned"
                            if subtask[7]:  # If there's an assigned_to value
                                current_assignee = subtask[10] if subtask[10] else "Unassigned"
                            
                            subtask_assigned_to = st.selectbox(
                                "Assign To", 
                                assignee_options,
                                index=assignee_options.index(current_assignee) if current_assignee in assignee_options else 0
                            )
                        
                        col1, col2, col3 = st.columns([1,1,2])
                        with col1:
                            if st.form_submit_button("Update Subtask"):
                                try:
                                    # Handle assignment
                                    assigned_to_id = None
                                    if subtask_assigned_to != "Unassigned":
                                        assigned_to_id = query_db(
                                            "SELECT id FROM users WHERE username = ?", 
                                            (subtask_assigned_to,), 
                                            one=True
                                        )[0]
                                    
                                    query_db("""
                                        UPDATE subtasks 
                                        SET title=?, description=?, status=?, start_date=?, deadline=?, 
                                        priority=?, assigned_to=?, budget=?
                                        WHERE id=?
                                    """, (
                                        subtask_title, subtask_description, subtask_status, 
                                        subtask_start_date, subtask_deadline, subtask_priority, 
                                        assigned_to_id, subtask_budget, subtask_id
                                    ))
                                    st.success("Subtask updated!")
                                    st.rerun()  # Force complete refresh
                                except Exception as e:
                                    st.error(f"Error updating subtask: {str(e)}")
                        with col2:
                            if st.form_submit_button("Delete"):
                                query_db("DELETE FROM subtasks WHERE id=?", (subtask_id,))
                                st.success("Subtask deleted!")
                                st.rerun()  # Force complete refresh
    
    # Add new subtask form with reliable assignment handling
    st.markdown("---")
    st.subheader("Create New Subtask")
    with st.form(key=f"add_subtask_form_{task_id}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_subtask_title = st.text_input("Title*", placeholder="Enter subtask name")
            new_subtask_description = st.text_area("Description", placeholder="Enter subtask description")
            
            status_col, priority_col = st.columns(2)
            with status_col:
                new_subtask_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
            with priority_col:
                new_subtask_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        
        with col2:
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                new_subtask_start_date = st.date_input("Start Date", value=start_date)
            with date_col2:
                new_subtask_deadline = st.date_input("Deadline", value=deadline)
            
            new_subtask_budget = st.number_input("Budget ($)", min_value=0.0, value=0.0, step=0.01)
            
            team_members = query_db("SELECT id, username FROM users ORDER BY username")
            new_subtask_assigned_to = st.selectbox(
                "Assign To", 
                ["Unassigned"] + [member[1] for member in team_members]
            )
        
        submit_col1, submit_col2 = st.columns(2)
        with submit_col1:
            if st.form_submit_button("Create Subtask"):
                if not new_subtask_title.strip():
                    st.error("Subtask title is required")
                elif new_subtask_deadline < new_subtask_start_date:
                    st.error("Deadline must be on or after the start date")
                else:
                    assigned_to_id = None
                    if new_subtask_assigned_to != "Unassigned":
                        assigned_to_id = query_db(
                            "SELECT id FROM users WHERE username = ?", 
                            (new_subtask_assigned_to,), 
                            one=True
                        )[0]
                    
                    query_db("""
                        INSERT INTO subtasks 
                        (task_id, title, description, status, start_date, deadline, 
                         priority, assigned_to, budget)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task_id, new_subtask_title.strip(), new_subtask_description, 
                        new_subtask_status, new_subtask_start_date, new_subtask_deadline,
                        new_subtask_priority, assigned_to_id, new_subtask_budget
                    ))
                    st.success("Subtask created successfully!")
                    st.rerun()  # Force complete refresh
        with submit_col2:
            if st.form_submit_button("Cancel"):
                st.rerun()
    
    return False

# Update the plot_subtask_analytics function with filters and budget column
def plot_subtask_analytics(tasks_df):
    if not tasks_df.empty:
        # Fetch all subtasks with extended information including budget
        subtasks = query_db("""
            SELECT 
                p.name as project_name,
                t.id as task_id, 
                t.title as task_title,
                s.id as subtask_id, 
                s.title as subtask_title, 
                s.description,
                s.status,
                s.start_date,
                s.deadline,
                s.priority,
                u.username as assigned_to,
                s.budget,
                s.time_spent
            FROM subtasks s
            JOIN tasks t ON s.task_id = t.id
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u ON s.assigned_to = u.id
            ORDER BY p.name, t.id, s.id
        """)
        
        if subtasks:
            # Create DataFrame with all subtask information
            subtasks_df = pd.DataFrame(subtasks, columns=[
                "Project", "Task ID", "Task Title", "Subtask ID", 
                "Subtask Title", "Description", "Status", "Start Date",
                "Deadline", "Priority", "Assigned To", "Budget", "Time Spent"
            ])
            
            # Convert date columns
            subtasks_df['Start Date'] = pd.to_datetime(subtasks_df['Start Date'], errors='coerce')
            subtasks_df['Deadline'] = pd.to_datetime(subtasks_df['Deadline'], errors='coerce')
            
            # Add filters section
            with st.expander("🔍 Filter Subtasks", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    project_filter = st.selectbox(
                        "Filter by Project",
                        ["All Projects"] + sorted(subtasks_df['Project'].unique().tolist())
                    )
                    
                    task_filter = st.selectbox(
                        "Filter by Task",
                        ["All Tasks"] + sorted(subtasks_df['Task Title'].unique().tolist())
                    )
                
                with col2:
                    subtask_filter = st.selectbox(
                        "Filter by Subtask",
                        ["All Subtasks"] + sorted(subtasks_df['Subtask Title'].unique().tolist())
                    )
                    
                    assignee_filter = st.selectbox(
                        "Filter by Assignee",
                        ["All Assignees"] + sorted(subtasks_df['Assigned To'].dropna().unique().tolist())
                    )
                
                with col3:
                    status_filter = st.selectbox(
                        "Filter by Status",
                        ["All Statuses"] + sorted(subtasks_df['Status'].unique().tolist())
                    )
            
            # Apply filters
            filtered_df = subtasks_df.copy()
            
            if project_filter != 'All Projects':
                filtered_df = filtered_df[filtered_df['Project'] == project_filter]
            
            if task_filter != 'All Tasks':
                filtered_df = filtered_df[filtered_df['Task Title'] == task_filter]
            
            if subtask_filter != 'All Subtasks':
                filtered_df = filtered_df[filtered_df['Subtask Title'] == subtask_filter]
            
            if assignee_filter != 'All Assignees':
                filtered_df = filtered_df[filtered_df['Assigned To'] == assignee_filter]
            
            if status_filter != 'All Statuses':
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            # Display the filtered subtasks table
            st.subheader("Subtasks Overview")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_order=["Project", "Task Title", "Subtask Title", "Status", 
                             "Priority", "Assigned To", "Start Date", "Deadline",
                             "Budget", "Time Spent"],
                column_config={
                    "Start Date": st.column_config.DateColumn("Start Date"),
                    "Deadline": st.column_config.DateColumn("Deadline"),
                    "Budget": st.column_config.NumberColumn("Budget", format="$%.2f"),
                    "Time Spent": st.column_config.NumberColumn("Time Spent (hrs)")
                }
            )
            
            # Completion analysis
            st.subheader("Completion Analysis")
            col1, col2 = st.columns(2)
            with col1:
                status_counts = filtered_df['Status'].value_counts()
                fig = px.pie(
                    status_counts, 
                    values=status_counts.values, 
                    names=status_counts.index,
                    title="Subtask Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                completion_rate = (len(filtered_df[filtered_df['Status'] == 'Completed']) / len(filtered_df)) * 100
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=completion_rate,
                    title={'text': "Overall Completion Rate"},
                    gauge={'axis': {'range': [0, 100]}}
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            # Budget analysis
            st.subheader("Budget Analysis")
            if 'Budget' in filtered_df.columns:
                budget_df = filtered_df.dropna(subset=['Budget'])
                if not budget_df.empty:
                    fig = px.bar(
                        budget_df,
                        x='Subtask Title',
                        y='Budget',
                        color='Project',
                        title="Subtask Budgets by Project",
                        hover_data=['Task Title', 'Priority', 'Assigned To']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No budget data available for filtered subtasks")
            
            # Timeline analysis by project
            st.subheader("Timeline Analysis by Project")
            if 'Start Date' in filtered_df.columns and 'Deadline' in filtered_df.columns:
                filtered_df['Duration'] = (filtered_df['Deadline'] - filtered_df['Start Date']).dt.days
                fig = px.bar(
                    filtered_df,
                    x='Subtask Title',
                    y='Duration',
                    color='Project',
                    title="Subtask Durations by Project",
                    hover_data=['Task Title', 'Priority', 'Assigned To', 'Budget']
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No subtasks found in the database")
    else:
        st.warning("No tasks available for subtask analysis")