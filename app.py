import streamlit as st
import re

st.set_page_config(page_title="Login", layout="centered")

# Helper function to center text
def st_center_text(text, tag="p"):
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

# Helper function to center widgets
def st_center_widget(widget_callable, col_ratio=[1,3,1]):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        widget_callable()

# Title
st_center_text("The Brain App", tag="h1")

# Sign In header
st_center_text("Sign In", tag="h2")

# Centered login form
def login_form():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        st.caption("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
        login_btn = st.form_submit_button("Login")
    return username, password, login_btn

# Place form in center
username, password, login_btn = None, None, None
st_center_widget(lambda: (lambda u_pw_btn: u_pw_btn())(lambda: login_form()))

# Form validation
if login_btn:
    def show_error(msg):
        st_center_widget(lambda: st.error(msg))
    def show_success(msg):
        st_center_widget(lambda: st.success(msg))
    
    if len(password) < 7:
        show_error('Password must be at least 7 characters long.')
    elif not re.search(r"[A-Z]", password):
        show_error("Password must include at least one uppercase letter.")
    elif not re.search(r"[a-z]", password):
        show_error("Password must include at least one lowercase letter.")
    elif not re.search(r"[0-9]", password):
        show_error("Password must include at least one number.")
    else:
        show_success(f"Welcome {username}, you logged in successfully!")

# Sign up section
st_center_text("Don't have an account? Please Sign up!", tag="p")
st_center_widget(lambda: st.button('Sign up'))
