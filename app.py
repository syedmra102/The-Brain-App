import streamlit as st

st.markdown("""
<div class="custom-container">
    <h1>🧠 The BrainApp</h1>
    <h2>Login to Your Account</h2>
    
   
""", unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="custom-container">', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            # Password requirements
            st.markdown("""
            <div class="password-req">
                <div style="font-weight: 600; margin-bottom: 10px; color: #FFFFFF;">🔐 Password Requirements:</div>
                <div>• At least 7 characters</div>
                <div>• One uppercase letter</div>
                <div>• One lowercase letter</div>
                <div>• One number</div>
            </div>
            """, unsafe_allow_html=True)
            
            login_button = st.form_submit_button("🚀 Login to BrainApp")
            
            if login_button:
                if username and password:
                    st.success("🎉 Welcome back! Login successful!")
                else:
                    st.error("⚠️ Please fill in all fields!")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; color: #CBD5E0;">
            <div>Don't have an account? <a href="#" style="color: #7C3AED; text-decoration: none; font-weight: 500;">Sign up here</a></div>
            <div style="margin-top: 0.5rem;"><a href="#" style="color: #7C3AED; text-decoration: none; font-weight: 500;">Forgot your password?</a></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
