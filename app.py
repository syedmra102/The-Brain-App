import streamlit as st



import re



st.set_page_config(page_title="Login", layout="centered")







st.markdown("<h1 style='text-align: center;'> The Brain App</h1>", unsafe_allow_html=True)











# Center the form in the page



col1, col2, col3 = st.columns([1, 3, 1])  # middle column narrower



with col2:



    st.markdown("### Login")



    with st.container():



        with st.form("login_form"):



            username = st.text_input("Username")



            password = st.text_input("Password", type="password")



            st.caption("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")



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



        col1, col2, col3 = st.columns([1, 3, 1])



        with col2:



             st.success(f"Welcome {username}, You login successfully!!")



    # your login form here
