import streamlit as st
import re
import json
import os
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="The Brain App", layout="centered")
USER_FILE = "users.json"

# ------------------- Helper Functions -------------------
def st_center_text(text, tag="p"):
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

def st_center_form(form_callable, col_ratio=[1,3,1], form_name="form"):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        with st.form(form_name):
            return form_callable()

def st_center_widget(widget_callable, col_ratio=[1,3,1]):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        return widget_callable()

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
        except:
            return {}
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ------------------- Email Function -------------------
EMAIL_ADDRESS = "your_email@gmail.com"  # replace with your Gmail
EMAIL_PASSWORD = "hreebomqxpjkphpe"     # your 16-character App Password

def send_password_email(to_email, password):
    msg = EmailMessage()
    msg['Subject'] = 'Your Brain App Password'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"Hello,\n\nYour password is: {password}\n\n- The Brain App")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent to your email successfully!"
    except Exception as e:
        return False, f"Failed to send email: {e}"

# ------------------- Pages -------------------
def sign_in_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign In", tag="h2")

    def login_form():
        st.text_input("Username", key="signin_username")
        st.text_input("Password", type="password", key="signin_password")
        st.caption("Password must have 1 uppercase, 1 lowercase, 1 numeric character, and be at least 7 characters long.")
        return st.form_submit_button("Login")

    login_btn = st_center_form(login_form, form_name="signin_form")
    st_center_text("If you don't have an account, please Sign Up!", tag="p")

    if st_center_widget(lambda: st.button("Forgot Password")):
        st.session_state.page = "forgot_password"

    if st_center_widget(lambda: st.button("Go to Sign Up")):
        st.session_state.page = "signup"

    if login_btn:
        username = st.session_state.get("signin_username", "")
        password = st.session_state.get("signin_password", "")
        users = load_users()
        user_info = users.get(username)
        if isinstance(user_info, dict) and user_info.get("password","") == password:
            st_center_widget(lambda: st.success(f"Welcome {username}, you logged in successfully!"))
        elif isinstance(user_info, dict):
            st_center_widget(lambda: st.error("Incorrect password!"))
        else:
            st_center_widget(lambda: st.error("Username does not exist. Please Sign Up."))

def forgot_password_page():
    st_center_text("Forgot Password", tag="h2")

    def email_form():
        st.text_input("Enter your email", key="forgot_email")
        return st.form_submit_button("Send Password")

    submit_btn = st_center_form(email_form, form_name="forgot_form")
    st_center_widget(lambda: st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

    if submit_btn:
        email = st.session_state.get("forgot_email", "").strip()
        if not email:
            st_center_widget(lambda: st.error("Please enter your email!"))
            return
        users = load_users()
        found = False
        for info in users.values():
            if isinstance(info, dict) and info.get("email","") == email:
                success, msg = send_password_email(email, info.get("password",""))
                if success:
                    st_center_widget(lambda: st.success(msg))
                else:
                    st_center_widget(lambda: st.error(msg))
                found = True
                break
        if not found:
            st_center_widget(lambda: st.success("If this email exists, a password reset email would be sent!"))

def sign_up_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign Up", tag="h2")

    def signup_form():
        st.text_input("Username", key="signup_username")
        st.text_input("Email", key="signup_email")
        st.text_input("Password", type="password", key="signup_password")
        st.caption("Password must have 1 uppercase, 1 lowercase, 1 numeric character, and be at least 7 characters long.")
        st.text_input("Confirm Password", type="password", key="signup_password2")
        return st.form_submit_button("Register")

    signup_btn = st_center_form(signup_form, form_name="signup_form")
    st_center_text("If you already have an account, please Sign In!", tag="p")
    st_center_widget(lambda: st.button("Go to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

    if signup_btn:
        username = st.session_state.get("signup_username", "")
        email = st.session_state.get("signup_email", "")
        password = st.session_state.get("signup_password", "")
        password2 = st.session_state.get("signup_password2", "")
        users = load_users()

        if username in users:
            st_center_widget(lambda: st.error("Username already exists. Try logging in!"))
        elif password != password2:
            st_center_widget(lambda: st.error("Passwords do not match!"))
        elif len(password) < 7 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
            st_center_widget(lambda: st.error("Password must be at least 7 characters long, include uppercase, lowercase, and number."))
        else:
            users[username] = {"email": email, "password": password}
            save_users(users)
            st_center_widget(lambda: st.success("Sign up successful! You can now Sign In."))

# ------------------- Main -------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
