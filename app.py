import streamlit as st
import re  # for password pattern checking

# --- PAGE STYLING ---
st.markdown(
    """
    <style>
    /* Center the title */
    .center-title {
        text-align: center;
        font-size: 40px;
        color: #00ffcc;
    }

    /* Make form area centered and smaller */
    .form-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }

    /* Style the form box */
    .form-box {
        background-color: #0a1931;
        padding: 40px;
        border-radius: 15px;
        width: 350px; /* form width */
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
    }

    label, input {
        color: white !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# --- PAGE TITLE ---
st.markdown("<h1 class='center-title'>🧠 The Brain App</h1>", unsafe_allow_html=True)

# --- FORM SECTION ---
st.markdown("<div class='form-container'><div class='form-box'>", unsafe_allow_html=True)

with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.form_submit_button("Login")

if login_btn:
    # Password rules: min 7 chars, 1 uppercase, 1 lowercase, 1 number
    if len(password) < 7:
        st.error("❌ Password too short! It must have at least 7 characters.")
    elif not re.search(r"[A-Z]", password):
        st.error("❌ Password must contain at least one uppercase letter.")
    elif not re.search(r"[a-z]", password):
        st.error("❌ Password must contain at least one lowercase letter.")
    elif not re.search(r"[0-9]", password):
        st.error("❌ Password must contain at least one number.")
    else:
        st.success(f"✅ Welcome, {username}! You logged in successfully.")

st.markdown("</div></div>", unsafe_allow_html=True)
