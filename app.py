import streamlit as st
import re

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# --- CSS STYLING ---
st.markdown("""
<style>
/* Background */
.stApp {
    background: linear-gradient(180deg, #001f3f 0%, #000814 100%);
    color: white;
}

/* Title in center horizontally only */
.title {
    text-align: center;
    font-size: 45px;
    color: #00ffcc;
    font-weight: 800;
    text-shadow: 0 0 10px #00ffcc;
    margin-top: 60px;
}

/* Form container (smaller width, taller height) */
.form-box {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 40px 25px;
    margin: 0 auto;
    width: 320px;   /* 👈 Less width */
    min-height: 350px;  /* 👈 More height */
    box-shadow: 0 0 15px rgba(0,255,170,0.2);
    backdrop-filter: blur(8px);
}

/* Button styling */
.stButton>button {
    background-color: #00ff99 !important;
    color: #001f3f !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    width: 100%;
    height: 40px;
}

.stTextInput label {
    color: white !important;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# --- APP TITLE ---
st.markdown("<h1 class='title'>🧠 The Brain App</h1>", unsafe_allow_html=True)

# --- LOGIN FORM ---
st.markdown("<div class='form-box'>", unsafe_allow_html=True)

with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.form_submit_button("Login")

if login_btn:
    # Password validation
    if len(password) < 7:
        st.error("❌ Password must be at least 7 characters long.")
    elif not re.search(r"[A-Z]", password):
        st.error("❌ Must include at least one uppercase letter.")
    elif not re.search(r"[a-z]", password):
        st.error("❌ Must include at least one lowercase letter.")
    elif not re.search(r"[0-9]", password):
        st.error("❌ Must include at least one number.")
    else:
        st.success(f"✅ Welcome {username}! You’ve logged in successfully.")

st.markdown("</div>", unsafe_allow_html=True)
