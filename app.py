import streamlit as st

# Make a form
with st.form("my_form"):
    name = st.text_input("Enter your name:")
    email = st.text_input("Enter your email:")
    age = st.number_input("Enter your age:", min_value=1, max_value=100)
    
    submitted = st.form_submit_button("Submit")

# When user clicks "Submit"
if submitted:
    st.success(f"Hello {name}! Your form is submitted ✅")
