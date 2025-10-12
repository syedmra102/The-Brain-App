import streamlit as st
import re

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

st.markdown("<style>...</style>")
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
