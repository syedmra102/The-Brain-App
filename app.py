import streamlit as st
import re
import json
import os
import smtplib
from email.message import EmailMessage

# ------------------- Configuration -------------------
st.set_page_config(page_title="The Brain App", layout="centered")
USER_FILE = "users.json"

# ------------------- Helper Functions -------------------
def st_center_text(text, tag="p"):
    """Center text anywhere in the app"""
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

def st_center_form(form_callable, col_ratio=[1,3,1], form_name="form"):
    """Center a form in the page"""
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        with st.form(form_name):
            return form_callable()

def st_center_widget(widget_callable, col_ratio=[1,3,1]):
    """Center any Streamlit widget (button, etc.)"""
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        return widget_callable()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def send_password_email(to_email, password):
    EMAIL_ADDRESS = "your_email@gmail.com"      # Replace with your email
    EMAIL_PASSWORD = "your_app_password"        # Replace with Gmail app password

    msg = EmailMessage()
    msg['Subject'] = 'Your Brain App Password'
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

    # Helpful captions outside form
    st_center_text("Your password must have at least 1 uppercase, 1 lowercase, 1 numeric character and be at least 7 characters long.", tag="p")
    st_center_text("If you don't have an account, please Sign Up!", tag="p")

    def login_form():
        st.text_input("Username", key="signin_username")
        st.text_input("Password", type="password", key="signin_password")
        return st.form_submit_button("Login")

    login_btn = st_center_form(login_form, form_name="signin_form")

    # Forgot password button
    if st_center_widget(lambda: st.button("Forgot Password")):
        forgot_password()

    # Go to Sign Up
    if st_center_widget(lambda: st.button("Go to Sign Up")):
        st.session_state.page = "signup"

    # Handle login
    if login_btn:
        username = st.session_state.get("signin_username", "")
        password = st.session_state.get("signin_password", "")
        users = load_users()
        if username in users and users[username]["password"] == password:
            st_center_text(f"Welcome {username}, you logged in successfully!", tag="h3")
        elif username in users:
            st_center_text("Incorrect password!", tag="h3")
        else:
            st_center_text("Username does not exist. Please Sign Up.", tag="h3")

def forgot_password():
    users = load_users()
    username = st.session_state.get("signin_username", "")
    if username in users:
        email = users[username]["email"]
        send_password_email(email, users[username]["password"])
    else:
        st_center_text("Username not found!", tag="h3")

def sign_up_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign Up", tag="h2")

    # Helpful captions outside form
    st_center_text("Your password must have at least 1 uppercase, 1 lowercase, 1 numeric character and be at least 7 characters long.", tag="p")
    st_center_text("If you already have an account, please Sign In!", tag="p")

    def signup_form():
        st.text_input("Username", key="signup_username")
        st.text_input("Email", key="signup_email")
        st.text_input("Password", type="password", key="signup_password")
        st.text_input("Confirm Password", type="password", key="signup_password2")
        return st.form_submit_button("Register")

    signup_btn = st_center_form(signup_form, form_name="signup_form")

    # Go to Sign In
    if st_center_widget(lambda: st.button("Go to Sign In")):
        st.session_state.page = "signin"

    # Handle signup
    if signup_btn:
        username = st.session_state.get("signup_username", "")
        email = st.session_state.get("signup_email", "")
        password = st.session_state.get("signup_password", "")
        password2 = st.session_state.get("signup_password2", "")
        users = load_users()

        if username in users:
            st_center_text("Username already exists. Try logging in!", tag="h3")
            send_password_email(users[username]["email"], users[username]["password"])
        elif password != password2:
            st_center_text("Passwords do not match!", tag="h3")
        elif len(password) < 7 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
            st_center_text("Password must be at least 7 characters long, include uppercase, lowercase, and number.", tag="h3")
        else:
            users[username] = {"email": email, "password": password}
            save_users(users)
            st_center_text("Sign up successful! You can now Sign In.", tag="h3")

# ------------------- Main -------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
