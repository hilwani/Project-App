import streamlit as st
import sqlite3
import hashlib

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
def login_screen():
    st.set_page_config(page_title="Login - Project App", layout="centered")
    st.title("🔐 Welcome to Project Management App")

    tabs = st.tabs(["Login", "Register"])

    # --- LOGIN TAB ---
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

    # --- REGISTER TAB ---
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
