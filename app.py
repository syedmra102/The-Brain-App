import streamlit as st
import re

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# ===== Custom CSS =====
st.markdown("""
<style>
/* Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #001f3f, #003366);
    color: white;
}

/* Title */
h1 {
    text-align: center;
    font-size: 45px;
    font-weight: 800;
    color: white;
    text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
    margin-top: 40px;
    margin-bottom: 20px;
}

/* Center box container */
.login-box {
    background-color: rgba(255, 255, 255, 0.08);
    border: 2px solid #00ffaa55;
    border-radius: 20px;
    box-shadow: 0 0 25px rgba(0,255,255,0.2);
    padding: 40px;
    width: 400px;
    margin: 0 auto;
    backdrop-filter: blur(10px);
}

/* Input styling */
.stTextInput {
    width: 100% !important;
}

.stTextInput input {
    border-radius: 10px;
    height: 45px;
    border: 2px solid #00FFAA;
    background-color: #002244;
    color: white;
    font-size: 15px;
}

/* Button styling */
div[data-testid="stFormSubmitButton"] button {
    background-color: #00FFAA !important;
    color: #001f3f !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    width: 100%;
    height: 45px;
    margin-top: 15px;
    transition: 0.3s;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #00cc88 !important;
}
</style>
""", unsafe_allow_html=True)

# ===== Title =====
st.markdown("<h1>🧠 The Brain App</h1>", unsafe_allow_html=True)

# ===== Box Container =====
st.markdown('<div class="login-box">', unsafe_allow_html=True)

with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    login_btn = st.form_submit_button("Login")

st.markdown('</div>', unsafe_allow_html=True)

# ===== Validation Logic =====
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
        st.success(f"✅ Welcome, {username}! You’ve successfully logged in.")
