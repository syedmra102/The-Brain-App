import streamlit as st

def login_page():
    st.title("🔐 Login")
    
    # Login Form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if username == "admin" and password == "password":  # Temporary check
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")
    
    # Sign up section below login form
    st.markdown("---")
    st.write("Don't have an account?")
    
    if st.button("Sign Up"):
        st.session_state.current_page = 'register'  # Register page pe switch karo
        st.rerun()

def register_page():
    st.title("📝 Create Account")
    
    with st.form("register_form"):
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        register_button = st.form_submit_button("Create Account")
        
        if register_button:
            if new_password == confirm_password:
                st.success("Account created successfully!")
                # Yaha aap user ko save kar sakte hain
                st.session_state.current_page = 'login'  # Wapas login pe
                st.rerun()
            else:
                st.error("Passwords don't match!")
    
    # Back to login button
    if st.button("← Back to Login"):
        st.session_state.current_page = 'login'
        st.rerun()

# Main app
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

if st.session_state.current_page == 'login':
    login_page()
else:
    register_page()
