import streamlit as st
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# --- CSS STYLING ---
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #001F3F, #003366);
}
.main {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
}
.login-box {
    background: rgba(255, 255, 255, 0.08);
    padding: 40px 50px;
    border-radius: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 25px rgba(0, 255, 150, 0.2);
    width: 340px;
    text-align: center;
}
.login-box h1 {
    color: #00FFAA;
    margin-bottom: 30px;
    font-size: 30px;
    letter-spacing: 1px;
}
.stTextInput label {
    color: white !important;
}
.stTextInput input {
    border-radius: 10px;
}
div[data-testid="stFormSubmitButton"] button {
    background-color: #00FF99 !important;
    color: #001F3F !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- HTML STRUCTURE ---
st.markdown("<div class='main'><div class='login-box'>", unsafe_allow_html=True)
st.markdown("<h1>🧠 The Brain App</h1>", unsafe_allow_html=True)

# --- FORM ---
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.form_submit_button("Login")

    if login_btn:
        # Password Validation
        if len(password) < 7:
            st.error("❌ Password must be at least 7 characters long.")
        elif not re.search(r"[A-Z]", password):
            st.error("❌ Must include at least one uppercase letter.")
        elif not re.search(r"[a-z]", password):
            st.error("❌ Must include at least one lowercase letter.")
        elif not re.search(r"[0-9]", password):
            st.error("❌ Must include at least one number.")
        else:
            st.success(f"✅ Welcome, {username}! You’ve successfully logged in.")

st.markdown("</div></div>", unsafe_allow_html=True)
