     # Dashboard Page 
    if page == "Dashboard":
        st.markdown("---")
      

        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
            .doc-header {
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
        </style>
        """, unsafe_allow_html=True)


        # Header Section with Gradient
        st.markdown("""
        <div class="doc-header">
            <h1 style="color: white; margin-bottom: 0.5rem;">🏠 Dashboard</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;"></p>
        </div>
        """, unsafe_allow_html=True)

        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  

       
        # ======= Project Summary Statistics =======
        # ======= Project Summary Statistics =======
        st.subheader("📊 Project Overview")

        # Calculate project metrics
        total_projects = len(query_db("SELECT * FROM projects"))
        active_projects = len(query_db("SELECT * FROM projects WHERE end_date >= ?", (datetime.today().date(),)))
        overdue_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE p.end_date < ? 
            AND EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """, (datetime.today().date(),)))
        completed_projects = len(query_db("""
            SELECT p.id 
            FROM projects p
            WHERE NOT EXISTS (
                SELECT 1 FROM tasks t 
                WHERE t.project_id = p.id 
                AND t.status != 'Completed'
            )
        """))

        # Update the columns from 3 to 4
        cols = st.columns(4)  # Changed from 3 to 4 columns

        # Existing cards (just showing the new one added)
        with cols[0]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4E8BF5;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Projects'}}}}, '*')">
                <div class="metric-title"> 
                    <span class="metric-icon">📂</span>
                    <span class="metric-name">Total Projects</span>
                </div>
                <p class="metric-value">{total_projects}</p>
            </div>
            """, unsafe_allow_html=True)




        with cols[1]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #32CD32;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Projects'}}}}, '*')">
                <div class="metric-title"> 
                    <span class="metric-icon">🟢</span>
                    <span class="metric-name">Active Projects</span>
                </div>
                <p class="metric-value">{active_projects}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FF4500;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Projects'}}}}, '*')">
                <div class="metric-title"> 
                    <span class="metric-icon">⚠️</span>
                    <span class="metric-name">Overdue Projects</span>
                </div>
                <p class="metric-value">{overdue_projects}</p>
            </div>
            """, unsafe_allow_html=True)


        # Add the new Completed Projects card
        with cols[3]:  
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #32CD32;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Projects'}}}}, '*')">
                <div class="metric-title"> 
                    <span class="metric-icon">✅</span>
                    <span class="metric-name">Completed Projects</span>
                </div>
                <p class="metric-value">{completed_projects}</p>
            </div>
            """, unsafe_allow_html=True)



        # Divider with spacing
        # ======= Task Summary Statistics =======
        # ======= Task Summary Statistics =======
        st.markdown("---")
        st.subheader("✅ Task Overview")

        # Remove the admin restriction from these queries - let all users see all tasks
        total_tasks = query_db("SELECT COUNT(*) FROM tasks")[0][0]
        overdue_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Completed' AND deadline < DATE('now')
        """)[0][0]

        upcoming_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Completed' 
            AND deadline BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
        """, (st.session_state.reminder_period,))[0][0]

        completed_tasks_count = query_db("""
            SELECT COUNT(*) FROM tasks 
            WHERE status = 'Completed'
        """)[0][0]

        # Create task metric cards with clickable functionality
        cols = st.columns(4)
        with cols[0]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4E8BF5;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Tasks'}}}}, '*')">
                <div class="metric-title">
                    <span class="metric-icon">✅</span>
                    <span class="metric-name">Total Tasks</span>
                </div>
                <p class="metric-value">{total_tasks}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FF4500;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Tasks'}}}}, '*')">
                <div class="metric-title">
                    <span class="metric-icon">⚠️</span>
                    <span class="metric-name">Overdue Tasks</span>
                </div>
                <p class="metric-value">{overdue_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #FFA500;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Tasks'}}}}, '*')">
                <div class="metric-title">
                    <span class="metric-icon">🔜</span>
                    <span class="metric-name">Upcoming Tasks</span>
                </div>
                <p class="metric-value">{upcoming_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)

        # Add JavaScript to handle card clicks
        components.html("""
        <script>
            // Handle clicks on metric cards
            document.addEventListener('click', function(e) {
                if (e.target.closest('.dashboard-metric-card')) {
                    const card = e.target.closest('.dashboard-metric-card');
                    const page = card.getAttribute('data-page');
                    if (page) {
                        window.parent.postMessage({
                            'streamlit:setComponentValue': {
                                'page': page
                            }
                        }, '*');
                    }
                }
            });
            
            // Listen for messages from Streamlit
            window.addEventListener('message', function(event) {
                if (event.data && event.data.page) {
                    // This will trigger Streamlit to update the page
                    window.parent.postMessage({
                        streamlit: {
                            type: 'streamlit:componentMessage',
                            data: {page: event.data.page}
                        }
                    }, '*');
                }
            });
        </script>
        """, height=0)


        # Add the new Completed Tasks card
        with cols[3]:                                                                                                                                                                                                   
            st.markdown(f"""
            <div class="dashboard-metric-card" style="border-left-color: #4CAF50;" onclick="window.parent.postMessage({{'streamlit:setComponentValue': {{'page': 'Tasks'}}}}, '*')">
                <div class="metric-title">
                    <span class="metric-icon">✔️</span>
                    <span class="metric-name">Completed Tasks</span>
                </div>
                <p class="metric-value">{completed_tasks_count}</p>
            </div>
            """, unsafe_allow_html=True)



        # Divider with spacing
        st.markdown("---")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        

        # ======= Project Health Dashboard =======
        st.subheader("📈 Project Health")
        
        # Project Selection (single selection point for entire dashboard)
        projects = get_projects()
        project_options = ["All Projects"] + [p[2] for p in projects]
        selected_project = st.selectbox("Select Project", project_options, key="health_project_select")
        
        # Filter tasks based on selection
        if selected_project == "All Projects":
            tasks_df = fetch_tasks()  
            selected_project_id = None
        else:
            selected_project_id = query_db("SELECT id FROM projects WHERE name=?", (selected_project,), one=True)[0]
            tasks_df = fetch_tasks(selected_project_id)

        # Divider with spacing
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
        
        # Create tabs (always show all tabs)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Progress", 
            "Distribution", 
            "Budget", 
            "Assignees", 
            "Productivity"
        ])
        
        # Helper function to export data and images
        def export_tab_data(tab_name, data, fig=None):
            with st.expander(f"📤 Export {tab_name} Data", expanded=False):
                col1, col2 = st.columns(2)
                
                # Export as CSV
                with col1:
                    st.download_button(
                        label="Download as CSV",
                        data=data.to_csv(index=False),
                        file_name=f"{tab_name.lower().replace(' ', '_')}_data.csv",
                        mime="text/csv"
                    )
                
                # Export image if figure exists
                if fig:
                    with col2:
                        buf = io.BytesIO()
                        fig.write_image(buf, format="png", width=1000)
                        st.download_button(
                            label="Download as PNG",
                            data=buf.getvalue(),
                            file_name=f"{tab_name.lower().replace(' ', '_')}_chart.png",
                            mime="image/png"
                        )
        
        # Tab1
        with tab1:  # Progress tab
            st.write("### Project Progress with Gantt Chart")
            
            if selected_project_id:
                # Get the selected project's details
                project_data = query_db("""
                    SELECT p.name, p.start_date, p.end_date, 
                        COUNT(t.id) as total_tasks,
                        SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
                    FROM projects p
                    LEFT JOIN tasks t ON p.id = t.project_id
                    WHERE p.id = ?
                    GROUP BY p.id
                """, (selected_project_id,), one=True)
                
                if project_data:
                    name, start_date, end_date, total_tasks, completed_tasks = project_data
                    
                    # Fetch tasks for the selected project with both planned and actual dates
                    tasks = query_db("""
                        SELECT id, title, 
                            start_date as planned_start_date, 
                            deadline as planned_deadline, 
                            actual_start_date,
                            actual_deadline,
                            status, priority 
                        FROM tasks 
                        WHERE project_id = ?
                        ORDER BY deadline
                    """, (selected_project_id,))
                    
                    if tasks:
                        # Prepare Gantt chart data
                        gantt_data = []
                        today = datetime.now().date()
                        
                        for task in tasks:
                            task_id, title, planned_start, planned_end, actual_start, actual_end, status, priority = task
                            
                            # Convert dates to datetime.date objects with fallbacks
                            planned_start_date = pd.to_datetime(planned_start).date() if planned_start else pd.to_datetime(start_date).date()
                            planned_deadline = pd.to_datetime(planned_end).date() if planned_end else pd.to_datetime(end_date).date()
                            actual_start_date = pd.to_datetime(actual_start).date() if actual_start else planned_start_date
                            actual_deadline = pd.to_datetime(actual_end).date() if actual_end else planned_deadline
                            
                            # Add both planned and actual tasks to the data
                            gantt_data.append({
                                "Task": title,
                                "Start": planned_start_date,
                                "Finish": planned_deadline,
                                "Type": "Planned",
                                "Status": status,
                                "Priority": priority
                            })
                            
                            if actual_start and actual_end:  # Only add actual timeline if dates exist
                                gantt_data.append({
                                    "Task": title,
                                    "Start": actual_start_date,
                                    "Finish": actual_deadline,
                                    "Type": "Actual",
                                    "Status": status,
                                    "Priority": priority
                                })
                        
                        gantt_df = pd.DataFrame(gantt_data)
                        
                        # Convert dates to strings for Plotly timeline
                        gantt_df['Start'] = gantt_df['Start'].astype(str)
                        gantt_df['Finish'] = gantt_df['Finish'].astype(str)


                        

                        
                        # Create Gantt chart with proper bar sizing                                     
                        fig = px.timeline(
                            gantt_df,
                            x_start="Start",
                            x_end="Finish",
                            y="Task",
                            color="Type",
                            color_discrete_map={
                                "Planned": "rgba(158, 202, 225, 0.7)",  # Semi-transparent light blue
                                "Actual": "rgba(78, 121, 167, 0.9)"     # Darker blue with slight transparency
                            },
                            title=f"Gantt Chart for {name}",
                            hover_data=["Status", "Priority"],
                            width=1000  # Fixed width for better control
                        )

                        # Reverse the y-axis to show tasks in correct order
                        fig.update_yaxes(autorange="reversed")
                        
                        # Customize the chart appearance with better bar sizing
                        fig.update_traces(
                            marker_line_color='rgba(0,0,0,0.5)',  # Add border to bars
                            marker_line_width=1,                  # Border width
                            width=0.4                            # Make bars thicker (0-1 scale)
                        )

                        # Calculate today's position correctly
                        min_date = pd.to_datetime(gantt_df['Start'].min())
                        max_date = pd.to_datetime(gantt_df['Finish'].max())
                        today_dt = pd.to_datetime(today)
                        
                        # Convert to milliseconds since epoch for precise positioning
                        min_ms = min_date.value // 10**6  # Convert nanoseconds to milliseconds
                        max_ms = max_date.value // 10**6
                        today_ms = today_dt.value // 10**6
                        
                        # Calculate position (0-1 range)
                        if max_ms > min_ms:
                            today_position = (today_ms - min_ms) / (max_ms - min_ms)
                        else:
                            today_position = 0.5  # Default to middle if no date range

                        # Add today's line with precise positioning
                        fig.add_vline(
                            x=today_position * (max_ms - min_ms) + min_ms,  # Convert back to absolute position
                            line_dash="dot",
                            line_color="red",
                            line_width=3,  # Thicker line
                            annotation_text=f"Today: {today.strftime('%b %d, %Y')}",
                            annotation_position="top right",
                            annotation_font_size=12,
                            annotation_font_color="red"
                        )

                        # Adjust layout for better readability
                        fig.update_layout(
                            height=max(800, len(tasks) * 50),  # Taller chart with more space per task
                            bargap=0.2,                       # Space between bars
                            xaxis_range=[min_ms, max_ms],     # Set exact date range
                            xaxis_tickformat='%b %d, %Y',     # Better date formatting
                            hoverlabel=dict(
                                bgcolor="white",
                                font_size=12,
                                font_family="Arial"
                            )
                        )

                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True, use_container_height=True)
                        
                        # Project summary metrics
                        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                        status = "Completed" if progress == 100 else "In Progress" if progress > 0 else "Not Started"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Tasks", total_tasks)
                        with col2:
                            st.metric("Completed Tasks", completed_tasks)
                        with col3:
                            st.metric("Progress", f"{progress:.1f}%", status)
                        
                        # Task timeline details table with standardized column names
                        st.write("### Task Timeline Details")
                        display_df = pd.DataFrame([{
                            "Task": task[1],
                            "Status": task[6],
                            "Priority": task[7],
                            "Planned Start Date": pd.to_datetime(task[2]).date() if task[2] else pd.to_datetime(start_date).date(),
                            "Planned Deadline": pd.to_datetime(task[3]).date() if task[3] else pd.to_datetime(end_date).date(),
                            "Actual Start Date": pd.to_datetime(task[4]).date() if task[4] else "Not started",
                            "Actual Deadline": pd.to_datetime(task[5]).date() if task[5] else "Not completed",
                            "Planned Duration": (pd.to_datetime(task[3]).date() - pd.to_datetime(task[2]).date()).days if task[2] and task[3] else "N/A",
                            "Actual Duration": (pd.to_datetime(task[5]).date() - pd.to_datetime(task[4]).date()).days if task[4] and task[5] else "N/A",
                            "Variance": "N/A" if not task[4] or not task[5] else 
                                ((pd.to_datetime(task[5]).date() - pd.to_datetime(task[4]).date()).days - 
                                (pd.to_datetime(task[3]).date() - pd.to_datetime(task[2]).date()).days)
                        } for task in tasks])
                        
                        st.dataframe(
                            display_df,
                            column_config={
                                "Planned Start Date": st.column_config.DateColumn("Planned Start Date"),
                                "Planned Deadline": st.column_config.DateColumn("Planned Deadline"),
                                "Actual Start Date": st.column_config.DateColumn("Actual Start Date"),
                                "Actual Deadline": st.column_config.DateColumn("Actual Deadline"),
                                "Planned Duration": st.column_config.NumberColumn("Planned Duration (days)"),
                                "Actual Duration": st.column_config.NumberColumn("Actual Duration (days)"),
                                "Variance": st.column_config.NumberColumn("Variance (days)")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Export functionality
                        export_tab_data("Progress", display_df, fig)                                                           
                    else:
                        st.warning(f"No tasks found for project {name}")
                else:
                    st.warning("Project data not available")
            else:
                st.warning("Please select a specific project to view the Gantt chart (not 'All Projects')")


        with tab2:  # Distribution tab
            if not tasks_df.empty:
                # Status/Priority Distribution
                col1, col2 = st.columns(2)
                with col1:
                    fig_status = px.pie(
                        tasks_df,
                        names="Status",
                        title="Task Status Distribution",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                    
                    # Prepare status data for export
                    status_counts = tasks_df["Status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    export_tab_data("Status Distribution", status_counts, fig_status)
                    
                with col2:
                    fig_priority = px.pie(
                        tasks_df,
                        names="Priority",
                        title="Task Priority Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig_priority, use_container_width=True)
                    
                    # Prepare priority data for export
                    priority_counts = tasks_df["Priority"].value_counts().reset_index()
                    priority_counts.columns = ["Priority", "Count"]
                    export_tab_data("Priority Distribution", priority_counts, fig_priority)
            else:
                st.warning("No tasks found for visualization")

        with tab3:  # Budget tab
            if not tasks_df.empty:
                # Budget Variance Visualization
                st.write("### Budget Variance by Project")
                budget_data = tasks_df.groupby("Project").agg({
                    "Budget": "sum",
                    "Actual Cost": "sum"
                }).reset_index()
                budget_data["Variance"] = budget_data["Budget"] - budget_data["Actual Cost"]
                
                fig_budget = px.bar(
                    budget_data,
                    x="Project",
                    y=["Budget", "Actual Cost"],
                    title="Budget vs Actual Cost",
                    barmode="group",
                    labels={"value": "Amount ($)", "variable": "Type"},
                    color_discrete_map={
                        "Budget": '#3498db',
                        "Actual Cost": '#e74c3c'
                    }
                )
                st.plotly_chart(fig_budget, use_container_width=True)
                
                # Variance breakdown
                fig_variance = px.bar(
                    budget_data,
                    x="Project",
                    y="Variance",
                    title="Budget Variance (Budget - Actual)",
                    color="Variance",
                    color_continuous_scale=px.colors.diverging.RdBu,
                    labels={"Variance": "Amount ($)"}
                )
                st.plotly_chart(fig_variance, use_container_width=True)
                
                # Export functionality
                export_tab_data("Budget Analysis", budget_data, fig_budget)
                export_tab_data("Budget Variance", budget_data, fig_variance)
            else:
                st.warning("No tasks found for budget analysis")

        with tab4:  # Assignees tab
            if not tasks_df.empty and "Assignee" in tasks_df.columns:
                # Task Distribution by Assignee
                st.write("### Task Distribution by Assignee")
                assignee_dist = tasks_df["Assignee"].value_counts().reset_index()
                assignee_dist.columns = ["Assignee", "Task Count"]
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_assignee_pie = px.pie(
                        assignee_dist,
                        names="Assignee",
                        values="Task Count",
                        title="Tasks per Assignee",
                        hole=0.4
                    )
                    st.plotly_chart(fig_assignee_pie, use_container_width=True)
                    export_tab_data("Assignee Distribution", assignee_dist, fig_assignee_pie)
                
                with col2:
                    fig_assignee_bar = px.bar(
                        assignee_dist,
                        x="Assignee",
                        y="Task Count",
                        title="Task Count by Assignee",
                        color="Assignee"
                    )
                    st.plotly_chart(fig_assignee_bar, use_container_width=True)
                    export_tab_data("Assignee Task Count", assignee_dist, fig_assignee_bar)
            else:
                st.warning("No assignee data available")

        with tab5:  # Productivity tab
            if not tasks_df.empty:
                st.write("### Assignee Productivity Metrics")
                
                # Fetch assignee productivity data
                if st.session_state.user_role == "Admin":
                    productivity_query = """
                        SELECT 
                            u.username as Assignee,
                            COUNT(t.id) as TotalTasks,
                            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                            SUM(t.time_spent) as TotalTimeSpent,
                            AVG(julianday(t.deadline) - julianday(t.start_date)) as AvgDuration
                        FROM tasks t
                        LEFT JOIN users u ON t.assigned_to = u.id
                        GROUP BY u.username
                        ORDER BY CompletedTasks DESC
                    """
                    productivity_data = query_db(productivity_query)
                else:
                    productivity_query = """
                        SELECT 
                            u.username as Assignee,
                            COUNT(t.id) as TotalTasks,
                            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                            SUM(t.time_spent) as TotalTimeSpent,
                            AVG(julianday(t.deadline) - julianday(t.start_date)) as AvgDuration
                        FROM tasks t
                        LEFT JOIN users u ON t.assigned_to = u.id
                        WHERE t.assigned_to = ?
                        GROUP BY u.username
                        ORDER BY CompletedTasks DESC
                    """
                    productivity_data = query_db(productivity_query, (st.session_state.user_id,))
                
                if productivity_data:
                    # Create DataFrame
                    productivity_df = pd.DataFrame(productivity_data, columns=[
                        "Assignee", "Total Tasks", "Completed Tasks", "Time Spent (hours)", "Avg Duration (days)"
                    ])
                    
                    # Calculate completion rate and efficiency
                    productivity_df["Completion Rate"] = (productivity_df["Completed Tasks"] / productivity_df["Total Tasks"] * 100).round(1)
                    productivity_df["Tasks/Hour"] = (productivity_df["Completed Tasks"] / productivity_df["Time Spent (hours)"]).round(2)
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Most Productive", productivity_df.iloc[0]["Assignee"])
                    with col2:
                        st.metric("Highest Completion Rate", 
                                f"{productivity_df['Completion Rate'].max()}%")
                    with col3:
                        st.metric("Most Efficient", 
                                f"{productivity_df['Tasks/Hour'].max()} tasks/hour")
                    
                    # Display the productivity table
                    st.dataframe(
                        productivity_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Visualizations
                    col1, col2 = st.columns(2)
                    with col1:
                        # Completion Rate by Assignee
                        fig_completion = px.bar(
                            productivity_df,
                            x="Assignee",
                            y="Completion Rate",
                            title="Completion Rate by Assignee",
                            color="Completion Rate",
                            color_continuous_scale=px.colors.sequential.Blues
                        )
                        st.plotly_chart(fig_completion, use_container_width=True)
                        export_tab_data("Completion Rate", productivity_df, fig_completion)
                    
                    with col2:
                        # Efficiency by Assignee
                        fig_efficiency = px.bar(
                            productivity_df,
                            x="Assignee",
                            y="Tasks/Hour",
                            title="Task Efficiency (Tasks per Hour)",
                            color="Tasks/Hour",
                            color_continuous_scale=px.colors.sequential.Greens
                        )
                        st.plotly_chart(fig_efficiency, use_container_width=True)
                        export_tab_data("Efficiency", productivity_df, fig_efficiency)
                    
                    # Time Spent vs Tasks Completed
                    fig_time_vs_tasks = px.scatter(
                        productivity_df,
                        x="Time Spent (hours)",
                        y="Completed Tasks",
                        size="Total Tasks",
                        color="Assignee",
                        title="Time Spent vs Tasks Completed",
                        hover_name="Assignee",
                        labels={
                            "Time Spent (hours)": "Time Spent (hours)",
                            "Completed Tasks": "Completed Tasks"
                        }
                    )
                    st.plotly_chart(fig_time_vs_tasks, use_container_width=True)
                    export_tab_data("Time vs Tasks", productivity_df, fig_time_vs_tasks)
                else:
                    st.warning("No productivity data available")
            else:
                st.warning("No tasks found for productivity analysis")

        # ======= Global Export Options =======
        st.markdown("---")
        st.subheader("📤 Export All Data")
        with st.expander("💾 Comprehensive Export Options", expanded=False):
            if not tasks_df.empty:
                st.download_button(
                    label="Download All Task Data as CSV",
                    data=tasks_df.to_csv(index=False),
                    file_name="all_task_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No task data available for export")