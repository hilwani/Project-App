import streamlit as st
import sqlite3
import datetime
import time
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import hashlib
from components.drag_and_drop import drag_and_drop
from streamlit_calendar import calendar
import io
import logging
import streamlit.components.v1 as components
import json
import base64
import plotly.graph_objects as go

# Import page modules
from calendar_page import show_calendar_page
from workspace_page import workspace_page
from task_page import show_task_page

# Page Config
st.set_page_config(page_title="Project Management App", layout="wide")

# Initialize database and session state
def init_db():
    conn = sqlite3.connect('project_management.db')
    c = conn.cursor()
    
    # Database tables creation (your existing init_db code)
    # ...
    conn.commit()
    conn.close()

# Shared functions
def query_db(query, args=(), one=False):
    conn = sqlite3.connect('project_management.db')
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Initialize database
init_db()

# Authentication
if not st.session_state.authenticated:
    # Login/register UI (your existing code)
    # ...
    pass
else:
    # Main App Layout
    with st.sidebar:
        # Sidebar content (your existing code)
        # ...
        
        # Navigation menu
        menu_items = [
            {"icon": "🏠", "label": "Dashboard", "page": "Dashboard"},
            {"icon": "📂", "label": "Projects", "page": "Projects"},
            {"icon": "✅", "label": "Tasks", "page": "Tasks"},
            {"icon": "🖥️", "label": "Workspace", "page": "Workspace"},
            {"icon": "📅", "label": "Calendar", "page": "Calendar"}
        ]
        
        for item in menu_items:
            if st.button(f"{item['icon']} {item['label']}"):
                st.session_state.page = item['page']
                st.rerun()

    # Main content area
    if st.session_state.page == "Dashboard":
        st.title("Dashboard")
        # Dashboard content...
        
    elif st.session_state.page == "Tasks":
        show_task_page()  # Call the task page
        
    elif st.session_state.page == "Calendar":
        show_calendar_page()
        
    elif st.session_state.page == "Workspace":
        workspace_page()