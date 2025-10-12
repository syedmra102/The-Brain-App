import streamlit as st
import hashlib
import re
from datetime import datetime

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Password validation
def validate_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    capital_count = len(re.findall(r'[A-Z]', password))
    small_count = len(re.findall(r'[a-z]', password))
    digit_count = len(re.findall(r'[0-9]', password))
    
    errors = []
    if capital_count < 1:
        errors.append("1 capital letter")
    if small_count < 3:
        errors.append("3 small letters")
    if digit_count < 1:
        errors.append("1 digit")
    
    if errors:
        return False, "Missing: " + ", ".join(errors)
    
    return True, "Strong password!"

# Main app
def main():
    st.set_page_config(page_title="Secure App", layout="centered")
    
    # Simple blue background
    st.markdown("""
    <style>
    .stApp {
        background-color: blue;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'users' not in st.session_state:
        st.session_state.users = {}
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    # Login Page
    def login_page():
        st.title("🔐 Login")
        
        # Login Form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                if username in st.session_state.users:
                    if st.session_state.users[username]['password'] == hash_password(password):
                        st.session_state.current_user = username
                        st.session_state.page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Wrong password!")
                else:
                    st.error("You don't exist! First make an account.")
        
        # Sign up section below login form
        st.write("---")
        st.write("If you don't have an account please make an account")
        
        if st.button("Sign Up"):
            st.session_state.page = 'signup'
            st.rerun()
    
    # Sign Up Page
    def signup_page():
        st.title("📝 Create Account")
        
        with st.form("signup_form"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Create Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if new_user in st.session_state.users:
                    st.error("Username already exists!")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match!")
                else:
                    is_valid, message = validate_password(new_pass)
                    if is_valid:
                        st.session_state.users[new_user] = {
                            'password': hash_password(new_pass),
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success("Account created! Going to login page...")
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error(message)
        
        # Back to login button
        st.write("---")
        if st.button("← Back to Login"):
            st.session_state.page = 'login'
            st.rerun()
    
    # Dashboard Page - Dark Blue Background
    def dashboard_page():
        # Dark blue background for dashboard
        st.markdown("""
        <style>
        .dashboard {
            background-color: darkblue;
            color: white;
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="dashboard">', unsafe_allow_html=True)
        st.title(f"🎉 Welcome, {st.session_state.current_user}!")
        st.write("You are successfully logged in to your dashboard!")
        
        # Green logout button
        if st.button("🚪 Logout", type="primary"):
            st.session_state.current_user = None
            st.session_state.page = 'login'
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show current page
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()

if __name__ == "__main__":
    main()
