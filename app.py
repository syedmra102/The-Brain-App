import streamlit as st
import re

# Set page configuration
st.set_page_config(page_title="The Brain App - Login", layout="centered")

# Custom CSS for aesthetic, classy design
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Poppins:wght@400;500&display=swap');

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
    }

    /* Title container */
    .title-container {
        background: linear-gradient(45deg, #e6b800, #ffdd4a);
        color: #1a1a2e;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 2rem;
    }

    .title-container h1 {
        font-family: 'Montserrat', sans-serif;
        font-size: 2.5rem;
        margin: 0;
        letter-spacing: 2px;
    }

    /* Form container */
    .form-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #2a2a4a;
        color: #ffffff;
        border: 1px solid #ffdd4a;
        border-radius: 8px;
        padding: 10px;
        font-family: 'Poppins', sans-serif;
        transition: border-color 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #e6b800;
        box-shadow: 0 0 8px rgba(230, 184, 0, 0.5);
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #e6b800, #ffdd4a);
        color: #1a1a2e;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(230, 184, 0, 0.4);
    }

    /* Caption and error/success messages */
    .stCaption {
        color: #cccccc;
        font-size: 0.9rem;
    }

    .stError, .stSuccess {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px;
        font-family: 'Poppins', sans-serif;
    }

    .stError {
        border: 1px solid #ff4d4d;
    }

    .stSuccess {
        border: 1px solid #e6b800;
    }

    /* Centered form layout */
    .center-form {
        max-width: 400px;
        margin: auto;
    }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    """,
    unsafe_allow_html=True
)

# Title in a styled box
st.markdown(
    """
    <div class="title-container">
        <h1><i class="fas fa-brain"></i> The Brain App</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Center the form
col1, col2, col3 = st.columns([1, 3, 1])  # middle column narrower
with col2:
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.markdown("### <i class='fas fa-sign-in-alt'></i> Login", unsafe_allow_html=True)
    with st.container():
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.caption("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
            login_btn = st.form_submit_button("Login")
    st.markdown('</div>', unsafe_allow_html=True)

# Login validation
if login_btn:
    if len(password) < 7:
        st.error('❌ Password must be at least 7 characters long.')
    elif not re.search(r"[A-Z]", password):
        st.error("❌ Password must include at least one uppercase letter.")
    elif not re.search(r"[a-z]", password):
        st.error("❌ Password must include at least one lowercase letter.")
    elif not re.search(r"[0-9]", password):
        st.error("❌ Password must include at least one number.")
    else:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.success(f"Welcome {username}, You login successfully!!")
