    # Main App
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"

    # Display welcome message if flag is set
    if st.session_state.get('show_welcome', False):
        user = query_db("SELECT username, first_name, last_name FROM users WHERE id=?", (st.session_state.user_id,), one=True)
        if user:
            # Use first name if available, otherwise username
            welcome_name = user[1] if user[1] else user[0]
            # Add last name if available
            if user[1] and user[2]:  # If both first and last name exist
                welcome_name = f"{user[1]} {user[2]}"
        else:
            welcome_name = "there"
        
        # Create a nice welcome container
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: #E1F0FF;
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 5px solid #4E8BF5;
                margin-bottom: 1.5rem;
            ">
                <h3 style="color: #2c3e50; margin-top: 0;">🎉 Welcome back, {welcome_name}!</h3>
                <p style="margin-bottom: 0.5rem;">You're logged in as <strong>{st.session_state.user_role}</strong>.</p>
                <p style="margin-bottom: 0;">Let's get productive! 🚀</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to dismiss the message
            if st.button("Got it!", key="dismiss_welcome"):
                st.session_state.show_welcome = False
                st.rerun()

    page = st.session_state.page