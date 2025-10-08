import streamlit as st
import re

# Set page config
st.set_page_config(page_title="Brain App Login", page_icon="🧠", layout="centered")

# Custom CSS for blue background, white form, green buttons
st.markdown(
    """
    <style>
    /* Blue background for the entire page */
    .stApp {
        background-color: #0052cc; /* Vibrant blue */
    }
    /* White form container */
    .stForm {
        background-color: #ffffff; /* White background for form */
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    /* Title color (white for contrast on blue) */
    h1 {
        color: #ffffff; /* White for title */
    }
    /* Subheader color (white for contrast) */
    .centered-subheader {
        text-align: center;
        font-size: 20px;
        color: #ffffff; /* White for subheader */
        margin-bottom: 20px;
    }
    /* Green buttons */
    .stButton>button {
        background-color: #28a745; /* Green buttons */
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #218838; /* Darker green on hover */
    }
    /* Error message styling */
    .stAlert {
        background-color: #ffe6e6; /* Light red for error */
        color: #d91e18; /* Red text */
    }
    /* Success message styling */
    .stSuccess {
        background-color: #e6ffed; /* Light green for success */
        color: #2e7d32; /* Green text */
    }
    /* Input fields styling */
    .stTextInput>div>input {
        background-color: #f8f9fa; /* Light gray for input fields */
        border: 1px solid #cccccc;
        border-radius: 4px;
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
            # Validate username: alphanumeric, no spaces
            if not re.match(r"^[a-zA-Z0-9]+$", username):
                raise ValueError("Username mein sirf letters aur numbers hone chahiye, no spaces!")
            # Password length check
            if len(password) < 6:
                raise ValueError("Password kam se kam 6 characters ka hona chahiye!")
            # Placeholder for real auth
            if username == "user" and password == "pass123":
                st.success("Login successful! Ab dashboard pe redirect kar sakte hain.")
            else:
                raise ValueError("Galat username ya password!")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error("Kuch galat hua! Dobara koshish karein.")
    
    # Handle signup (placeholder)
    if signup_button:
        try:
            if not username or not password:
                raise ValueError("Signup ke liye username aur password zaroori hain!")
            st.info("Sign Up clicked! Yahan signup logic daal sakte hain.")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error("Kuch galat hua signup ke dauraan! Dobara koshish karein.")
