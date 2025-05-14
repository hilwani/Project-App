import streamlit as st
import sqlite3
import hashlib
import base64  # Add to imports at top
from PIL import Image  # Add this import for handling images

# --- DB Helpers ---
def get_connection():
    return sqlite3.connect("project_management.db", check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

@st.cache_data(show_spinner=False)
def get_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

# --- Registration Helper ---
def register_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        conn.close()
        return False, "Username already exists"
    hashed_pw = hash_password(password)
    cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'User')", (username, hashed_pw))
    conn.commit()
    conn.close()
    return True, "User registered successfully"

# --- Combined Login/Register UI ---
# In your login_screen() function:
def login_screen():
    st.set_page_config(page_title="Login - Project App", layout="centered")
    
    # Logo and title side by side
    try:
        logo = Image.open('logo.png')
        st.markdown(f"""
        <div style="
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        ">
            <img src="data:image/png;base64,{base64.b64encode(open('logo.png', "rb").read()).decode("utf-8")}" 
                width="80" 
                style="
                    border-radius: 12px;
                    padding: 5px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    object-fit: contain;
                ">
            <h1 style="margin: 0; color: #2c3e50;">Project Management App</h1>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
    except:
        st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <h1>🏢 Project Management App</h1>
        </div>
        """, unsafe_allow_html=True)

    # Centered login title below the logo+title row
    st.markdown("""
    <div style="text-align: center; margin: 20px 0 30px 0;">
        <h2>🔐 Account Login</h2>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["Login", "Register"])

    # Rest of your existing code remains the same...
    with tabs[0]:
        st.subheader("Login")

        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            login_submit = st.form_submit_button("Login")

        if login_submit:
            user = get_user(username)
            if not user:
                st.error("❌ User not found.")
            elif not verify_password(user[2], password):
                st.error("❌ Incorrect password.")
            else:
                st.session_state.authenticated = True
                st.session_state.user_id = user[0]
                st.session_state.user_role = user[3]
                st.success("✅ Login successful!")
                st.rerun()

    with tabs[1]:
        st.subheader("Register")

        with st.form("register_form"):
            new_username = st.text_input("Choose a Username", key="reg_user")
            new_password = st.text_input("Choose a Password", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            register_submit = st.form_submit_button("Register")

        if register_submit:
            if not new_username or not new_password:
                st.error("Username and password are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message + " 🎉 You can now login.")
                else:
                    st.error(message)