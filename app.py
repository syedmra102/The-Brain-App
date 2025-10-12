import streamlit as st
import re

# ---- PAGE CONFIG ----
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# ---- CUSTOM CSS ----
st.markdown("""
<style>

body {
    background: linear-gradient(135deg, #001F3F, #005F99);
    font-family: 'Poppins', sans-serif;
    color: white;
}

h1 {
    text-align: center;
    color: white;
    font-weight: 700;
    letter-spacing: 2px;
}

div.stForm {
    background-color: rgba(255, 255, 255, 0.1);
    padding: 35px 30px;
    border-radius: 20px;
    box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(8px);
}

input {
    border-radius: 10px !important;
}

.stButton>button {
    background-color: #00FFAB;
    color: black;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    padding: 10px 25px;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    background-color: #00C896;
    color: white;
    transform: scale(1.05);
}

.success-box {
    background-color: rgba(0, 255, 171, 0.15);
    border: 1px solid #00FFAB;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)

# ---- TITLE ----
st.markdown("<h1>🧠 THE BRAIN APP</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center; color:#E0E0E0;'>Unlock the Power of AI — Log in to Begin</h5>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---- CENTER FORM ----
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    with st.form("login_form"):
        st.markdown("<h3 style='text-align:center; color:#00FFAB;'>Sign In</h3>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        st.caption("🔐 Password must have 7+ chars, one uppercase, one lowercase, and one number.")
        login_btn = st.form_submit_button("Login")

# ---- VALIDATION ----
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
        st.markdown(f"""
        <div class='success-box'>
            ✅ <strong>Welcome, {username}!</strong><br>
            You’ve successfully logged in to <em>The Brain App</em>.
        </div>
        """, unsafe_allow_html=True)
