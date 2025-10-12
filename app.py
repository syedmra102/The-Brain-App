# app.py - Aesthetic and Professional Streamlit Login Page

import streamlit as st
import re
import time
import hashlib

# --- CONFIGURATION AND CUSTOM AESTHETIC CSS ---

st.set_page_config(
    page_title="The Brain App Login", 
    page_icon="🧠", 
    layout="centered"
)

# Custom CSS for a professional, classy dark theme
st.markdown(
    """
    <style>
    /* 1. Global Aesthetic Theme */
    .stApp {
        background-color: #1E1E1E; /* Dark Charcoal Background */
        color: #FFFFFF; /* White Text */
        font-family: 'Inter', sans-serif;
    }
    .stApp * {
        color: #FFFFFF; /* Ensure all text is white */
    }

    /* 2. Classy Title Box Styling */
    .brain-app-title {
        text-align: center;
        padding: 20px;
        margin-bottom: 30px;
        background-color: #2C3E50; /* Deep Slate Blue */
        border-radius: 12px;
        border-left: 5px solid #4FC3F7; /* Light Blue Accent */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); /* Subtle Shadow */
    }
    .brain-app-title h1 {
        font-size: 2.5em;
        font-weight: 800;
        color: #4FC3F7 !important; /* Title Accent Color */
        letter-spacing: 2px;
    }

    /* 3. Form Container and Inputs */
    .stContainer {
        background-color: #2C3E50; /* Same Deep Slate Blue for Form Area */
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .stTextInput label {
        color: #B0BEC5 !important; /* Light Gray label text */
        font-weight: 600;
    }
    .stTextInput input {
        background-color: #1E1E1E; /* Input fields are darker */
        border: 1px solid #4FC3F7; /* Light Blue Border */
        border-radius: 6px;
        color: white;
    }

    /* 4. Professional Green Login Button */
    .stButton > button {
        background-color: #4CAF50 !important; /* Vibrant Green */
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #45A049 !important; /* Darker green on hover */
    }
    
    /* 5. Classy Output Messages (Aesthetic E-Signs) */
    .stAlert {
        border-radius: 8px;
        font-weight: 500;
        padding: 15px;
        margin-top: 15px;
    }
    .stAlert.success {
        background-color: #1B5E20; /* Darker Green Success BG */
        color: #E8F5E9;
    }
    .stAlert.error {
        background-color: #B71C1C; /* Darker Red Error BG */
        color: #FFEBEE;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- APP TITLE ---
# Place the title inside the styled box
st.markdown('<div class="brain-app-title"><h1>The Brain App</h1></div>', unsafe_allow_html=True)

# --- LOGIN FORM LOGIC ---

# Center the form in the page using columns
col1, col2, col3 = st.columns([1, 3, 1]) 

with col2:
    # Use a clean header for the form section
    st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
    
    # Use st.container to apply the dark blue background to the form area
    with st.container():
        
        # NOTE: Using a simple form without persistent state for this aesthetic demo.
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            # The password requirement caption is styled by the general CSS
            st.caption("🔒 Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
            
            login_btn = st.form_submit_button("Login")

# --- AUTHENTICATION AND FEEDBACK ---

if login_btn:
    
    # --- Client-Side Validation (Matching user's request) ---
    is_valid = True
    error_message = ""
    
    if len(password) < 7:
        is_valid = False
        error_message = '❌ Password must be at least 7 characters long.'
    elif not re.search(r"[A-Z]", password):
        is_valid = False
        error_message = "❌ Password must include at least one uppercase letter."
    elif not re.search(r"[a-z]", password):
        is_valid = False
        error_message = "❌ Password must include at least one lowercase letter."
    elif not re.search(r"[0-9]", password):
        is_valid = False
        error_message = "❌ Password must include at least one number."
    
    
    # --- Display Classy Output ---
    
    # We use the same central column for the output message
    with col2:
        if is_valid:
            # Aesthetic Success Output
            st.markdown(
                f"""
                <div class="stAlert success">
                    <span style='font-size: 1.5em;'>✅</span> 
                    <span style='font-size: 1.1em; font-weight: 700;'>ACCESS GRANTED:</span> 
                    Welcome, {username}. You have successfully logged in!
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Placeholder for the Dashboard (Shows the professional aesthetic continues)
            st.markdown("---")
            st.markdown(
                """
                <div style='background-color: #2E475E; padding: 20px; border-radius: 8px; margin-top: 15px;'>
                    <h3 style='color: #4FC3F7 !important;'>🧠 Dashboard Preview</h3>
                    <p style='color: #B0BEC5;'>Your professional dashboard starts here. All content uses the same clean dark theme and typography.</p>
                </div>
                """, unsafe_allow_html=True
            )
            
        else:
            # Aesthetic Error Output
            st.markdown(
                f"""
                <div class="stAlert error">
                    <span style='font-size: 1.5em;'>🛑</span> 
                    <span style='font-size: 1.1em; font-weight: 700;'>VALIDATION ERROR:</span> 
                    {error_message}
                </div>
                """, 
                unsafe_allow_html=True
            )
