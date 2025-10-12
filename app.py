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
    
    # Initialize session state
    if 'users' not in st.session_state:
        st.session_state.users = {}
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    # Login Page
    def login_page():
        st.markdown("""
        <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white;'>
            <h1>🔐 Secure Login</h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", use_container_width=True):
                if username in st.session_state.users:
                    if st.session_state.users[username]['password'] == hash_password(password):
                        st.session_state.current_user = username
                        st.session_state.page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Wrong password!")
                else:
                    st.error("User not found!")
        
        with col2:
            st.subheader("Create Account")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            if st.button("Register", use_container_width=True):
                if new_user in st.session_state.users:
                    st.error("Username exists!")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match!")
                else:
                    is_valid, message = validate_password(new_pass)
                    if is_valid:
                        st.session_state.users[new_user] = {
                            'password': hash_password(new_pass),
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success("Account created! Please login.")
                        st.rerun()
                    else:
                        st.error(message)
    
    # Dashboard Page
    def dashboard_page():
        st.title(f"Welcome, {st.session_state.current_user}!")
        st.write("You are successfully logged in!")
        
        if st.button("Logout"):
            st.session_state.current_user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Page routing
    if st.session_state.page == 'login':
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
