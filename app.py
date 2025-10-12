import streamlit as st
import hashlib
import re
from datetime import datetime

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Password validation
def validate_password(password):
    if len(password) < 7:
        return False, "Password must be at least 7 characters"
    
    capital_count = len(re.findall(r'[A-Z]', password))
    small_count = len(re.findall(r'[a-z]', password))
    digit_count = len(re.findall(r'[0-9]', password))
    
    errors = []
    if capital_count < 1:
        errors.append("1 capital letter")
    if small_count < 5:
        errors.append("5 small letters")
    if digit_count < 1:
        errors.append("1 numeric number")
    
    if errors:
        return False, "Missing: " + ", ".join(errors)
    
    return True, "Strong password!"

# Main app
def main():
    st.set_page_config(page_title="Secure App", layout="centered")
    
    # Simple blue background with white text
    st.markdown("""
    <style>
    .stApp {
        background-color: lightblue;
        color: white;
    }
    .stButton button {
        background-color: green;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stTextInput input, .stTextInput label {
        color: black !important;
    }
    .dashboard-box {
        background-color: blue;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
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
        st.title("Login to Your Account")
        
        # Login Form in a nice box
        with st.container():
            st.subheader("Login Form")
            with st.form("login_form"):
                username = st.text_input("Enter Your Username")
                password = st.text_input("Enter Your Password", type="password")
                login_btn = st.form_submit_button("Login")
                
                if login_btn:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    elif username in st.session_state.users:
                        if st.session_state.users[username]['password'] == hash_password(password):
                            st.session_state.current_user = username
                            st.session_state.page = 'dashboard'
                            st.success("Login successful! Taking you to dashboard...")
                            st.rerun()
                        else:
                            st.error("Wrong password! Please try again.")
                    else:
                        st.error("Account does not exist. Please create an account first.")
        
        # Sign up section
        st.write("---")
        st.write("Don't have an account?")
        
        if st.button("Create New Account", key="signup_btn"):
            st.session_state.page = 'signup'
            st.rerun()
    
    # Sign Up Page
    def signup_page():
        st.title("Create Your Account")
        
        with st.container():
            st.subheader("Account Registration")
            
            # Password requirements
            st.write("**Password Requirements:**")
            st.write("- 1 capital letter (A-Z)")
            st.write("- 5 small letters (a-z)")
            st.write("- 1 numeric number (0-9)")
            st.write("- Minimum 7 characters")
            
            with st.form("signup_form"):
                new_user = st.text_input("Choose Your Username")
                new_pass = st.text_input("Create Your Password", type="password")
                confirm_pass = st.text_input("Confirm Your Password", type="password")
                
                signup_btn = st.form_submit_button("Create Account")
                
                if signup_btn:
                    if not new_user or not new_pass or not confirm_pass:
                        st.error("Please fill in all fields")
                    elif new_user in st.session_state.users:
                        st.error("Username already exists! Please choose another one.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match! Please try again.")
                    else:
                        is_valid, message = validate_password(new_pass)
                        if is_valid:
                            st.session_state.users[new_user] = {
                                'password': hash_password(new_pass),
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.success("Account created successfully! Going to login page...")
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(f"Password is weak! {message}")
        
        # Back to login button
        st.write("---")
        if st.button("Back to Login Page", key="back_login"):
            st.session_state.page = 'login'
            st.rerun()
    
    # Dashboard Page
    def dashboard_page():
        st.markdown("""
        <div class="dashboard-box">
        """, unsafe_allow_html=True)
        
        st.title("Welcome to Your Dashboard")
        st.write(f"Hello, **{st.session_state.current_user}**!")
        st.write("You are successfully logged in and can now access all features.")
        
        # Some dashboard content
        st.write("---")
        st.subheader("Your Account Details")
        st.write(f"Username: {st.session_state.current_user}")
        st.write(f"Account Created: {st.session_state.users[st.session_state.current_user]['created_at']}")
        
        # Green logout button
        st.write("---")
        if st.button("Logout", key="logout_btn"):
            st.session_state.current_user = None
            st.session_state.page = 'login'
            st.rerun()
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Show current page
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()

if __name__ == "__main__":
    main()
