import streamlit as st

# Set page config
st.set_page_config(page_title="Brain App Login", page_icon="🧠", layout="centered")

# Title
st.title("The Brain that helps u to use your brain")

# Centered subheader using container and columns
with st.container():
    # Create a single column in the center
    col1, col2, col3 = st.columns([1, 2, 1])  # Middle column badi hai
    with col2:
        st.subheader("For login into your account press login and are u visiting for the first time please press sign up")

# Login form (same as before)
with st.form(key="login_form"):
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    col1, col2 = st.columns(2)
    with col1:
        login_button = st.form_submit_button("Login")
    with col2:
        signup_button = st.form_submit_button("Sign Up")
    if login_button:
        if username and password:
            st.success("Login clicked! Add your authentication logic here.")
        else:
            st.error("Please fill in both username and password.")
    if signup_button:
        st.info("Sign Up clicked! Redirect to signup page or logic here.")
