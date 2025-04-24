# calendar_page.py
import streamlit as st
import sqlite3
import json 
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components

def fetch_calendar_events():
    """Fetch tasks and prepare them for the calendar visualization"""
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    if st.session_state.user_role == "Admin":
        cursor.execute("""
            SELECT t.id, t.title, t.start_date, t.deadline, t.status, p.name as project_name 
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
        """)
    else:
        cursor.execute("""
            SELECT t.id, t.title, t.start_date, t.deadline, t.status, p.name as project_name 
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.assigned_to = ? OR p.user_id = ? OR p.id IN (
                SELECT project_id FROM project_team WHERE user_id = ?
            )
        """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id))
    
    tasks = cursor.fetchall()
    conn.close()
    
    events = []
    today = datetime.today().date()
    
    for task in tasks:
        deadline = datetime.strptime(task[3], "%Y-%m-%d").date() if task[3] else today
        status = task[4]
        is_overdue = deadline < today and status != "Completed"
        final_status = "overdue" if is_overdue else status.lower().replace(" ", "_")
        
        events.append({
            'id': str(task[0]),
            'title': f"{task[1]} ({task[5]})",
            'start': task[2],
            'end': task[3] if task[3] else task[2],
            'color': {
                'pending': '#FFA500',
                'in_progress': '#1E90FF',
                'completed': '#32CD32',
                'overdue': '#FF4500'
            }.get(final_status, '#777777'),
            'extendedProps': {
                'task_id': task[0],
                'project': task[5],
                'status': status,
                'is_overdue': is_overdue
            }
        })
    return events


def show_calendar_page():
    # st.title("📅 Project Calendar")
    # st.markdown("---")
    # st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # Calendar view selector
    view_options = {
        "Month": "dayGridMonth",
        "Week": "timeGridWeek",
        "Day": "timeGridDay",
        "List": "listWeek"
    }
    selected_view = st.radio(
        "View Mode",
        options=list(view_options.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Calendar HTML/JavaScript with Roboto font
    calendar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8' />
        <link href='https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap' rel='stylesheet'>
        <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
        <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
        <script src='https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js'></script>
        <script src='https://cdn.jsdelivr.net/npm/tippy.js@6.3.7/dist/tippy-bundle.umd.min.js'></script>
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
            }}
            .fc {{
                font-family: 'Roboto', sans-serif;
            }}
            .fc-toolbar-title {{
                font-weight: 500;
            }}
            .fc-col-header-cell-cushion {{
                font-weight: 500;
            }}
            .fc-daygrid-day-number {{
                font-weight: 400;
            }}
            .fc-event-title {{
                font-weight: 400;
            }}
            .fc-list-day-text, .fc-list-day-side-text {{
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div id='calendar'></div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const calendarEl = document.getElementById('calendar');
                const calendar = new FullCalendar.Calendar(calendarEl, {{
                    initialView: '{view_options[selected_view]}',
                    headerToolbar: {{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
                    }},
                    eventDisplay: 'block',
                    events: {json.dumps(fetch_calendar_events())},
                    eventDidMount: function(info) {{
                        tippy(info.el, {{
                            content: `
                                <div style="padding: 8px; max-width: 300px; font-family: 'Roboto', sans-serif;">
                                    <div style="font-weight: 600;">${{info.event.title}}</div>
                                    <div>Project: ${{info.event.extendedProps.project}}</div>
                                    <div>Status: ${{info.event.extendedProps.status}}</div>
                                    <div>${{info.event.extendedProps.is_overdue ? '⚠️ Overdue' : ''}}</div>
                                </div>
                            `,
                            allowHTML: true,
                            placement: 'top'
                        }});
                    }},
                    eventClick: function(info) {{
                        window.parent.postMessage({{
                            streamlit: {{
                                type: 'streamlit:componentMessage',
                                data: {{ taskId: info.event.extendedProps.task_id }}
                            }}
                        }}, '*');
                        info.jsEvent.preventDefault();
                    }},
                    height: 'auto',
                    nowIndicator: true
                }});
                calendar.render();
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(calendar_html, height=750)
    
   
    
    # Task details modal
    if hasattr(st.session_state, '_component_value') and 'taskId' in st.session_state._component_value:
        task_id = st.session_state._component_value['taskId']
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, p.name as project_name, u.username as assignee_name
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.id=?
        """, (task_id,))
        task = cursor.fetchone()
        conn.close()
        
        if task:
            with st.expander(f"📝 Task Details: {task[2]}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Project:** {task[-2]}")
                    st.write(f"**Title:** {task[2]}")
                    st.write(f"**Status:** {task[4]}")
                with col2:
                    st.write(f"**Assignee:** {task[-1] or 'Unassigned'}")
                    st.write(f"**Start Date:** {task[11] if len(task) > 11 and task[11] else 'Not set'}")
                    st.write(f"**Deadline:** {task[6]}")
                
                st.divider()
                st.write("**Description:**")
                st.write(task[3] or "No description available")
                
                if st.button("Close Details"):
                    del st.session_state._component_value
                    st.rerun()