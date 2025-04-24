import plotly.express as px
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import datetime as dt
from datetime import datetime
import logging


def plot_project_timeline(project_df):
    """Create a Gantt chart visualization of project timelines"""
    if project_df.empty:
        st.warning("No project data available for timeline visualization")
        return
    
    try:
        # Create a copy with just the columns we need
        timeline_df = project_df[[
            'Project', 
            'Planned Start Date', 
            'Planned Deadline',
            'Completion %',
            'Owner'
        ]].copy()
        
        # Rename columns to match Plotly's expected names while keeping our naming convention
        timeline_df = timeline_df.rename(columns={
            'Planned Start Date': 'Planned_Start_Date',
            'Planned Deadline': 'Planned_Deadline'
        })
        
        # Convert to datetime and handle missing values
        timeline_df['Planned_Start_Date'] = pd.to_datetime(timeline_df['Planned_Start_Date'])
        timeline_df['Planned_Deadline'] = pd.to_datetime(timeline_df['Planned_Deadline'])
        timeline_df = timeline_df.dropna(subset=['Planned_Start_Date', 'Planned_Deadline'])
        
        if timeline_df.empty:
            st.warning("No valid date ranges available for visualization")
            return
        
        # Create the Gantt chart with our renamed columns
        fig = px.timeline(
            timeline_df,
            x_start="Planned_Start_Date",
            x_end="Planned_Deadline",
            y="Project",
            color="Completion %",
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Project Timeline",
            hover_data=['Owner'],
            labels={
                "Planned_Start_Date": "Planned Start Date",
                "Planned_Deadline": "Planned Deadline",
                "Project": "Project Name",
                "Completion %": "Progress (%)"
            }
        )
        
        # Customize the chart
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            height=600,
            xaxis_title="Timeline",
            yaxis_title="Projects",
            coloraxis_colorbar=dict(title="Progress (%)"),
            hovermode="closest"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating project timeline: {str(e)}")
        logging.exception("Error in plot_project_timeline")
    
    # Add download button
    with st.expander("Export Options"):
        st.download_button(
            label="Download Timeline as PNG",
            data=fig.to_image(format="png"),
            file_name="project_timeline.png",
            mime="image/png"
        )

def plot_budget_comparison(project_df):
    """Compare budget vs actual costs across projects"""
    fig = px.bar(
        project_df,
        x="Project",
        y=["Budget", "Actual Cost"],
        barmode='group',
        title="Budget vs Actual Cost Comparison",
        labels={"value": "Amount ($)"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Add download button
    with st.expander("Export Options"):
        st.download_button(
            label="Download Budget Comparison as PNG",
            data=fig.to_image(format="png"),
            file_name="budget_comparison.png",
            mime="image/png"
        )

def plot_completion_heatmap(project_df):
    """Create a heatmap of project completion percentages with project names"""
    if project_df.empty:
        st.warning("No project data available for heatmap visualization")
        return
    
    try:
        # Prepare data - use Project names instead of IDs
        heatmap_data = project_df[['Project', 'Completion %']].copy()
        
        # Format completion percentage to 2 decimal places
        heatmap_data['Completion %'] = heatmap_data['Completion %'].round(2)
        
        # Create heatmap with project names on y-axis
        fig = px.imshow(
            heatmap_data.set_index('Project').T,
            labels=dict(x="Project", y="", color="Completion %"),
            color_continuous_scale='RdYlGn',
            aspect="auto",
            text_auto=True
        )
        
        # Customize layout
        fig.update_layout(
            title="Project Completion Heatmap",
            xaxis_title="Projects",
            yaxis_title="",
            height=400 + len(heatmap_data) * 20,  # Dynamic height based on number of projects
            margin=dict(l=50, r=50, b=100, t=50)
        )
        
        # Rotate project names for better readability
        fig.update_xaxes(tickangle=0)
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating completion heatmap: {str(e)}")

    # Add download button
    with st.expander("Export Options"):
            st.download_button(
                label="Download Heatmap as PNG",
                data=fig.to_image(format="png"),
                file_name="completion_heatmap.png",
                mime="image/png"
            )          


def plot_duration_variance(project_df):
    """Show variance between planned and actual durations with 2 decimal places"""
    if project_df.empty:
        st.warning("No project data available for duration variance visualization")
        return
    
    try:
        # Prepare data with project names and formatted percentages
        variance_data = project_df[[
            'Project',
            'Planned Duration (days)',
            'Actual Duration (days)',
            'Completion %'
        ]].copy()
        
        # Calculate variance and format completion %
        variance_data['Duration Variance'] = variance_data['Actual Duration (days)'] - variance_data['Planned Duration (days)']
        variance_data['Completion %'] = variance_data['Completion %'].round(2)
        
        # Create figure with project names
        fig = px.bar(
            variance_data,
            x='Project',
            y='Duration Variance',
            color='Completion %',
            color_continuous_scale='RdYlGn',
            title="Project Duration Variance (Actual - Planned)",
            labels={
                'Project': 'Project Name',
                'Duration Variance': 'Duration Variance (days)',
                'Completion %': 'Completion (%)'
            },
            hover_data=['Planned Duration (days)', 'Actual Duration (days)']
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Projects",
            yaxis_title="Duration Variance (days)",
            hovermode="closest"
        )
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating duration variance visualization: {str(e)}")

        # Add download button
        with st.expander("Export Options"):
                st.download_button(
                    label="Download Duration Variance as PNG",
                    data=fig.to_image(format="png"),
                    file_name="duration_variance.png",
                    mime="image/png"
                )          



def plot_project_health(project_df):
    """Quadrant analysis of project health"""
    fig = px.scatter(
        project_df,
        x="Completion %",
        y="Budget Variance",
        color="Project",
        size="Total Tasks",
        hover_name="Project",
        title="Project Health Quadrant Analysis",
        labels={
            "Completion %": "Progress (%) →",
            "Budget Variance": "Budget Performance ($) ↑"
        }
    )
    fig.add_hline(y=0, line_dash="dash")
    fig.add_vline(x=50, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)


def plot_plan_vs_actual_gantt(project_df):
    # Prepare data with proper datetime handling
    gantt_data = project_df.copy()
    
    # Convert to datetime objects
    gantt_data['Planned Start'] = pd.to_datetime(gantt_data['Start Date'])
    gantt_data['Planned End'] = pd.to_datetime(gantt_data['End Date'])
    
    # Calculate actual end date (fallback to planned if not available)
    if 'Actual End' not in gantt_data.columns:
        gantt_data['Actual End'] = gantt_data['Planned End']
    else:
        gantt_data['Actual End'] = pd.to_datetime(gantt_data['Actual End'])
    
    # Create figure using plotly.graph_objects
    fig = go.Figure()
    
    # Add planned duration bars
    for _, row in gantt_data.iterrows():
        fig.add_trace(go.Bar(
            y=[row['Project']],
            x=[(row['Planned End'] - row['Planned Start']).days],
            base=row['Planned Start'],
            name='Planned',
            orientation='h',
            marker_color='#636EFA',
            hoverinfo='text',
            hovertext=f"<b>{row['Project']}</b><br>"
                     f"Planned: {row['Planned Start'].strftime('%b %d, %Y')} - {row['Planned End'].strftime('%b %d, %Y')}<br>"
                     f"Duration: {(row['Planned End'] - row['Planned Start']).days} days"
        ))
        
        # Add actual duration indicator
        fig.add_trace(go.Scatter(
            x=[row['Actual End']],
            y=[row['Project']],
            mode='markers',
            marker=dict(
                color='#EF553B',
                size=12,
                symbol='diamond'
            ),
            name='Actual End',
            hoverinfo='text',
            hovertext=f"<b>{row['Project']}</b><br>"
                     f"Actual End: {row['Actual End'].strftime('%b %d, %Y')}<br>"
                     f"Variance: {(row['Actual End'] - row['Planned End']).days} days"
        ))
    
    # Add today's line using a shape instead of vline
    today = datetime.now().date()
    fig.add_shape(
        type="line",
        x0=today,
        x1=today,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(
            color="gray",
            width=2,
            dash="dot"
        )
    )
    
    # Add today's annotation
    fig.add_annotation(
        x=today,
        y=1.02,
        yref="paper",
        text="Today",
        showarrow=False,
        font=dict(color="gray")
    )
    
    # Style the layout
    fig.update_layout(
        title='Project Timeline: Planned vs Actual',
        barmode='overlay',
        height=600,
        xaxis_title='Timeline',
        yaxis_title='Projects',
        hovermode='closest',
        showlegend=True,
        xaxis=dict(
            type='date',
            tickformat='%b %d, %Y'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_duration_variance(project_df):
    variance_df = project_df.copy()
    variance_df['Duration Variance'] = variance_df['Actual Duration (days)'] - variance_df['Planned Duration (days)']
    
    fig = go.Figure(go.Waterfall(
        name="Duration",
        orientation="v",
        measure=["relative"] * len(variance_df),
        x=variance_df['Project'],
        textposition="outside",
        text=[f"{x:+.1f} days" for x in variance_df['Duration Variance']],
        y=variance_df['Duration Variance'],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
        increasing={"marker":{"color":"#EF553B"}},  # Red for delays
        decreasing={"marker":{"color":"#00CC96"}},  # Green for early completion
    ))
    
    fig.update_layout(
        title="Project Duration Variance (Actual - Planned)",
        yaxis_title="Days Difference",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Add download button
    with st.expander("Export Options"):
            st.download_button(
                label="Download Duration Variance as PNG",
                data=fig.to_image(format="png"),
                file_name="duration_variance.png",
                mime="image/png"
            )        


def plot_duration_comparison(project_df):
    """Compare planned vs actual durations"""
    if 'Planned Duration (days)' in project_df.columns and 'Actual Duration (days)' in project_df.columns:
        # Create a melted dataframe for plotting
        duration_df = project_df.melt(
            id_vars=["Project"], 
            value_vars=["Planned Duration (days)", "Actual Duration (days)"],
            var_name="Duration Type", 
            value_name="Days"
        )
        
        fig = px.bar(
            duration_df,
            x="Project",
            y="Days",
            color="Duration Type",
            barmode="group",
            title="Planned vs Actual Durations",
            labels={"Days": "Duration (days)"},
            color_discrete_map={
                "Planned Duration (days)": "#636EFA",
                "Actual Duration (days)": "#EF553B"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add analysis metrics
        project_df['Duration Variance'] = (
            project_df['Actual Duration (days)'] - project_df['Planned Duration (days)']
        )
        st.metric(
            "Average Duration Variance", 
            f"{project_df['Duration Variance'].mean():.1f} days",
            delta_color="inverse"
        )

        # Add download button
        with st.expander("Export Options"):
                st.download_button(
                    label="Download Duration Comparison as PNG",
                    data=fig.to_image(format="png"),
                    file_name="duration_comparison.png",
                    mime="image/png"
                )        