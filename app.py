import streamlit as st
import re

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# ===== CSS Styling =====
st.markdown("""
<style>
/* Background */
[data-testid="stAppViewContainer"] {
    background-color: #0d1117;
}

/* Centered title */
h1 {
    text-align: center;
    color: #00FFAA;
    font-size: 42px;
    margin-top: 40px;
    margin-bottom: 10px;
    text-shadow: 0 0 15px rgba(0,255,170,0.5);
}

/* Form box */
.form-box {
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.05);
    padding: 25px 30px;
    border-radius: 15px;
    box-shadow: 0 0 20px rgba(0,255,170,0.15);
    width: 320px;  /* less width */
}

/* Button styling */
div[data-testid="stFormSubmitButton"] button {
    background-color: #00FF99 !important;
    color: #001f3f !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    width: 100%;
}

/* Input fields */
.stTextInput input {
    border-radius: 8px !important;
    height: 45px !important;
}
</style>
""", unsafe_allow_html=True)

# ===== App Title =====
st.markdown("<h1>🧠 The Brain App</h1>", unsafe_allow_html=True)



with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    login_btn = st.form_submit_button("Login")

if login_btn:
    if len(password) < 7:
        st.error('❌ Password must be at least 7 characters long.')
    elif not re.search(r"[A-Z]", password):
        st.error("❌ Must include at least one uppercase letter.")
    elif not re.search(r"[a-z]", password):
        st.error("❌ Must include at least one lowercase letter.")
    elif not re.search(r"[0-9]", password):
        st.error("❌ Must include at least one number.")
    else:
        st.success(f"✅ Welcome, {username}! You’ve successfully logged in.")

st.markdown("</div>", unsafe_allow_html=True)
