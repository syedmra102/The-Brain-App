import streamlit as st
import re

# Set page config
st.set_page_config(page_title="Brain App Login", page_icon="🧠", layout="centered")

# Custom CSS for colors
st.markdown(
    """
    <style>
    /* Background color for the entire page */
    .stApp {
        background-color: #e6f3ff; /* Light blue-gray for AI vibe */
    }
    /* Title color */
    h1 {
        color: #1a3c6e; /* Dark blue for title */
    }
    /* Subheader color */
    .centered-subheader {
        text-align: center;
        font-size: 20px;
        color: #2e4b8c; /* Medium blue for subheader */
        margin-bottom: 20px;
    }
    /* Button colors */
    .stButton>button {
        background-color: #2e4b8c; /* Dark blue buttons */
        color: white;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #1a3c6e; /* Darker blue on hover */
    }
    /* Error message color */
    .stAlert {
        background-color: #ffe6e6; /* Light red for error background */
        color: #d91e18; /* Red for error text */
    }
    /* Success message color */
    .stSuccess {
        background-color: #e6ffed; /* Light green for success */
        color: #2e7d32; /* Green for success text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("The Brain that helps u to use your brain")

# Centered subheader
st.markdown(
    """
    <h3 class="centered-subheader">
        For login into your account press login and are u visiting for the first time please press sign up
    </h3>
    """,
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
    
    # Handle login with try-except
    if login_button:
        try:
            # Check if fields are empty
            if not username or not password:
                raise ValueError("Username aur password dono zaroori hain!")
            # Basic validation: username should be alphanumeric, no spaces
            if not re.match(r"^[a-zA-Z0-9]+$", username):
                raise ValueError("Username mein sirf letters aur numbers hone chahiye, no spaces!")
            # Password length check
            if len(password) < 6:
                raise ValueError("Password kam se kam 6 characters ka hona chahiye!")
            # Placeholder for real auth (e.g., check against database)
            if username == "user" and password == "pass123":
                st.success("Login successful! Ab dashboard pe redirect kar sakte hain.")
            else:
                raise ValueError("Galat username ya password!")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error("Kuch galat hua! Dobara koshish karein.")
    
    # Handle signup (placeholder with try-except)
    if signup_button:
        try:
            if not username or not password:
                raise ValueError("Signup ke liye username aur password zaroori hain!")
            st.info("Sign Up clicked! Yahan signup logic daal sakte hain.")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error("Kuch galat hua signup ke dauraan! Dobara koshish karein.")
