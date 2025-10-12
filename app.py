import streamlit as st
import re

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# --- CSS DESIGN ---
st.markdown("""
<style>
/* Background gradient */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #001f3f 0%, #000814 100%);
}

/* Center the entire app vertically and horizontally */
.main {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
    flex-direction: column;
}

/* Title styling */
h1 {
    text-align: center;
    color: #00FFAA;
    font-size: 45px;
    margin-bottom: 20px;
    text-shadow: 0 0 15px rgba(0,255,170,0.6);
    letter-spacing: 1px;
}

/* Form box */
.form-box {
    background: rgba(255, 255, 255, 0.05);
    padding: 35px 40px;
    border-radius: 20px;
    backdrop-filter: blur(8px);
    box-shadow: 0 0 25px rgba(0,255,170,0.15);
    width: 300px; /* narrow width */
    text-align: center;
}

/* Form input label and button */
.stTextInput label {
    color: white !important;
    font-weight: 500;
}

div[data-testid="stFormSubmitButton"] button {
    background-color: #00ff99 !important;
    color: #001f3f !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    width: 100%;
}

.stTextInput input {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

# --- BODY CONTENT ---
st.markdown("<div class='main'>", unsafe_allow_html=True)
st.markdown("<h1>🧠 The Brain App</h1>", unsafe_allow_html=True)

st.markdown("<div class='form-box'>", unsafe_allow_html=True)

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.form_submit_button("Login")

if login_btn:
    # Password validation rules
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
