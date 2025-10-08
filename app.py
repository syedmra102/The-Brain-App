import streamlit as st

# Set page config for consistent look
st.set_page_config(page_title="Brain App Login", page_icon="🧠", layout="centered")

# Title
st.title("The Brain that helps u to use your brain")

# Centered subheader
st.markdown(
    "<h3 style='text-align: center;'>"
    "For login into your account press login and are u visiting for the first time please press sign up"
    "</h3>",
    unsafe_allow_html=True
)

# Login form
with st.form(key="login_form"):
    # Credentials input
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    # Two buttons: Login and Sign Up
    col1, col2 = st.columns(2)
    with col1:
        login_button = st.form_submit_button("Login")
    with col2:
        signup_button = st.form_submit_button("Sign Up")
    
    # Placeholder actions for buttons
    if login_button:
        if username and password:
            st.success("Login clicked! Add your authentication logic here.")
        else:
            st.error("Please fill in both username and password.")
    if signup_button:
        st.info("Sign Up clicked! Redirect to signup page or logic here.")
