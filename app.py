import streamlit as st
import re
import json
import os
import smtplib
from email.message import EmailMessage

# ------------------- Configuration -------------------
st.set_page_config(page_title="The Brain App", layout="centered")

USER_FILE = "users.json"  # JSON file to store users

# ------------------- Helper Functions -------------------
def st_center_text(text, tag="p"):
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

def st_center_widget(widget_callable, col_ratio=[1,3,1]):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        widget_callable()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def send_password_email(to_email, password):
    # Simple SMTP email sending (example using Gmail SMTP)
    # Make sure to replace with your credentials
    EMAIL_ADDRESS = "your_email@gmail.com"
    EMAIL_PASSWORD = "your_app_password"  # Gmail app password recommended

    msg = EmailMessage()
    msg['Subject'] = 'Your Account Password'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"Hello,\n\nYour password is: {password}\n\n- The Brain App")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        st.success("Password sent to your email!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# ------------------- App Pages -------------------
def sign_in_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign In", tag="h2")

    def login_form():
        st.text_input("Username", key="signin_username")
        st.text_input("Password", type="password", key="signin_password")
        st_center_widget(lambda: st.form_submit_button("Login"))
        if st.button("Forgot Password?"):
            forgot_password()

    st_center_widget(lambda: st.form("login_form", clear_on_submit=False)(login_form))

    # Handle login
    users = load_users()
    username = st.session_state.get("signin_username", "")
    password = st.session_state.get("signin_password", "")
    if st.session_state.get("login_form"):
        if username in users and users[username]["password"] == password:
            st.success(f"Welcome {username}, you logged in successfully!")
        elif username in users:
            st.error("Incorrect password!")
        else:
            st.error("Username does not exist. Please Sign Up.")

    if st.button("Go to Sign Up"):
        st.session_state.page = "signup"

def forgot_password():
    users = load_users()
    username = st.session_state.get("signin_username", "")
    if username in users:
        email = users[username]["email"]
        send_password_email(email, users[username]["password"])
    else:
        st.error("Username not found!")

def sign_up_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign Up", tag="h2")

    def signup_form():
        st.text_input("Username", key="signup_username")
        st.text_input("Email", key="signup_email")
        st.text_input("Password", type="password", key="signup_password")
        st.text_input("Confirm Password", type="password", key="signup_password2")
        st_center_widget(lambda: st.form_submit_button("Register"))

    st_center_widget(lambda: st.form("signup_form", clear_on_submit=False)(signup_form))

    # Handle signup
    users = load_users()
    username = st.session_state.get("signup_username", "")
    email = st.session_state.get("signup_email", "")
    password = st.session_state.get("signup_password", "")
    password2 = st.session_state.get("signup_password2", "")

    if st.session_state.get("signup_form"):
        if username in users:
            st.error("Username already exists. Try logging in!")
            send_password_email(users[username]["email"], users[username]["password"])
        elif password != password2:
            st.error("Passwords do not match!")
        elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password) or len(password) < 7:
            st.error("Password must be at least 7 chars, include uppercase, lowercase, and number.")
        else:
            users[username] = {"email": email, "password": password}
            save_users(users)
            st.success("Sign up successful! You can now Sign In.")
    
    if st.button("Go to Sign In"):
        st.session_state.page = "signin"

# ------------------- Main -------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
