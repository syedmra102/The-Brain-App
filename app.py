import streamlit as st 
st.title('The Brain App')
with st.form("Login"):
    Username=st.text_input('Username')
    Password=st.text_inout('Password',type='password')
    Login_btn=st.form_submit_button('Login')

if Login_btn:
    if len(Password) > 7 :
        st.error('Your Password is too short !!please make a password at with 7 charactres!!')
    else:
        st.sucess(f'Welcome {Username} !! , You login sucessfully !!')
