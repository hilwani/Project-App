        # ======= Project Analytics Section =======
        st.subheader("📂 Select Project")


        # First fetch all project data (same as before)
        projects_data = query_db("""
            SELECT 
                p.id, 
                p.user_id as owner_id, 
                p.name, 
                p.description, 
                p.start_date as planned_start_date,
                p.end_date as planned_deadline,
                p.budget,
                ROUND(COALESCE(SUM(t.actual_cost), 0)) as actual_cost,
                ROUND(p.budget - COALESCE(SUM(t.actual_cost), 0)) as budget_variance,
                COUNT(t.id) as task_count,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                u.username as owner_name,
                (ROUND(SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(t.id), 0), 2)) as completion_pct,
                julianday(p.end_date) - julianday(p.start_date) as planned_duration,
                CASE
                    WHEN MIN(t.actual_start_date) IS NULL OR MAX(t.actual_deadline) IS NULL THEN NULL
                    ELSE julianday(MAX(t.actual_deadline)) - julianday(MIN(t.actual_start_date))
                END as actual_duration
            FROM projects p
            LEFT JOIN tasks t ON t.project_id = p.id
            LEFT JOIN users u ON p.user_id = u.id
            GROUP BY p.id
        """)

        # Convert to DataFrame
        project_df = pd.DataFrame(projects_data, columns=[
            "ID", "Owner ID", "Project", "Description", "Planned Start Date", "Planned Deadline",
            "Budget", "Actual Cost", "Budget Variance", "Total Tasks",
            "Completed Tasks", "Owner", "Completion %",
            "Planned Duration (days)", "Actual Duration (days)"
        ])

        # Ensure date columns are proper datetime objects
        project_df["Planned Start Date"] = pd.to_datetime(project_df["Planned Start Date"])
        project_df["Planned Deadline"] = pd.to_datetime(project_df["Planned Deadline"])

        # Create filter widgets - matching your task page style but simplified
        with st.expander("🔍 Filter Projects", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Project filter - matches your task page dropdown style
                project_options = ['All Projects'] + sorted(project_df['Project'].unique().tolist())
                selected_project = st.selectbox(
                    "Filter by Project", 
                    project_options,
                    key="project_filter"
                )
            
            with col2:
                # Owner filter - matches your task page dropdown style
                owner_options = ['All Owners'] + sorted(project_df['Owner'].dropna().unique().tolist())
                selected_owner = st.selectbox(
                    "Filter by Owner",
                    owner_options,
                    key="owner_filter"
                )

        # Apply filters - same logic as your task page but simplified
        filtered_df = project_df.copy()

        if selected_project != 'All Projects':
            filtered_df = filtered_df[filtered_df['Project'] == selected_project]

        if selected_owner != 'All Owners':
            filtered_df = filtered_df[filtered_df['Owner'] == selected_owner]

        # Display the filtered table with same styling as your task page
        st.subheader("📊 Project Analytics")

        # Create a copy for display with formatted currency values
        display_df = filtered_df.copy()

        # Format currency columns as whole numbers (matches your task page style)
        display_df["Actual Cost"] = display_df["Actual Cost"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )
        display_df["Budget Variance"] = display_df["Budget Variance"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )
        display_df["Budget"] = display_df["Budget"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) else "$0"
        )

        # Format durations (matches your task page style)
        display_df["Planned Duration"] = display_df["Planned Duration (days)"].apply(
            lambda x: f"{float(x):.1f} days" if pd.notnull(x) else "N/A"
        )
        display_df["Actual Duration"] = display_df["Actual Duration (days)"].apply(
            lambda x: f"{float(x):.1f} days" if pd.notnull(x) else "N/A"
        )

        # Display the formatted table (matches your task page style)
        st.dataframe(
            display_df[[
                "Project", "Owner", "Planned Start Date", "Planned Deadline",
                "Planned Duration", "Actual Duration", "Total Tasks",
                "Completed Tasks", "Completion %", "Budget", "Actual Cost",
                "Budget Variance"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Planned Start Date": st.column_config.DateColumn("Planned Start Date"),
                "Planned Deadline": st.column_config.DateColumn("Planned Deadline"),
                "Completion %": st.column_config.NumberColumn(
                    "Completion %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

        st.write("</div>", unsafe_allow_html=True)  # Close the styled container