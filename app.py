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
    margin-bottom: 10px;
}

/* Form styling */
form {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.stTextInput {
    width: 300px !important;
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
    width: 300px;
    height: 45px;
    margin-top: 10px;
    transition: 0.3s;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #00cc88 !important;
}
</style>
""", unsafe_allow_html=True)

# ===== Title =====
st.markdown("<h1>🧠 The Brain App</h1>", unsafe_allow_html=True)

# ===== Login Form =====
with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    login_btn = st.form_submit_button("Login")

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
