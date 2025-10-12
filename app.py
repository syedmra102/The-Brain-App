import streamlit as st

st.set_page_config(page_title="Login", layout="centered")

st.title("🔐 The Brain App")

# Center the form in the page
col1, col2, col3 = st.columns([2, 1, 2])  # middle column narrower
with col2:
    st.write("### Login")  # form title
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")





# Add space below form (for height control)
st.write("")  
st.write("")

if login_btn:
    if len(password) < 7:
        st.error("Password must be at least 7 characters!")
    else:
        st.success(f"Welcome {username}! You logged in successfully.")
