import streamlit as st
import re

st.set_page_config(page_title="Login", layout="centered")

# Helper function to center any widget or text
def st_center(widget=None, text=None, tag="p", unsafe_html=True):
    """
    widget : callable, a Streamlit widget like st.button, st.text_input
    text : str, raw HTML/text to display
    tag : HTML tag for the text (h1, h2, p, etc.)
    """
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if widget:
            widget()
        elif text:
            st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=unsafe_html)

# Title
st_center(text="The Brain App", tag="h1")

# Sign In header
st_center(text="Sign In", tag="h2")

# Login form
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    st.caption("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
    login_btn = st.form_submit_button("Login")

# Form validation
if 'login_btn' in locals() and login_btn:
    if len(password) < 7:
        st_center(lambda: st.error('Password must be at least 7 characters long.'))
    elif not re.search(r"[A-Z]", password):
        st_center(lambda: st.error("Password must include at least one uppercase letter."))
    elif not re.search(r"[a-z]", password):
        st_center(lambda: st.error("Password must include at least one lowercase letter."))
    elif not re.search(r"[0-9]", password):
        st_center(lambda: st.error("Password must include at least one number."))
    else:
        st_center(lambda: st.success(f"Welcome {username}, you logged in successfully!"))

# Sign up section
st_center(text="Don't have an account? Please Sign up!", tag="p")
st_center(lambda: st.button('Sign up'))
