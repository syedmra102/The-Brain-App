import streamlit as st
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    # Header with nice design
    st.markdown("""
    <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white; margin-bottom:2rem;'>
        <h1>🚀 Performance Predictor</h1>
        <p>Login to your account</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form in center
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login to Your Account")
            
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if login_btn:
                if username and password:
                    # Yaha aap database check kar sakte hain
                    st.success(f"Welcome back, {username}!")
                else:
                    st.error("Please fill all fields")
    
    # Sign up section - Center mein aur professional
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("### Don't have an account?")
        st.write("Create your account to start your journey")
        
        if st.button("📝 Sign Up Now", use_container_width=True, type="secondary"):
            st.session_state.show_register = True
            st.rerun()

def register_page():
    # Header
    st.markdown("""
    <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white; margin-bottom:2rem;'>
        <h1>🚀 Create Your Account</h1>
        <p>Start your performance journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Register form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            st.subheader("Create New Account")
            
            new_username = st.text_input("👤 Choose Username", placeholder="Enter username")
            email = st.text_input("📧 Email Address", placeholder="Enter your email")
            new_password = st.text_input("🔒 Create Password", type="password", placeholder="Create password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password")
            
            # Terms checkbox
            agree_terms = st.checkbox("I agree to the Terms and Conditions")
            
            register_btn = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if register_btn:
                if not all([new_username, email, new_password, confirm_password]):
                    st.error("❌ Please fill all fields")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif not agree_terms:
                    st.error("❌ Please agree to terms and conditions")
                else:
                    # Yaha aap user ko save kar sakte hain
                    st.session_state.users[new_username] = hash_password(new_password)
                    st.success("✅ Account created successfully! Please login.")
                    st.session_state.show_register = False
                    st.rerun()
    
    # Back to login
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()

# Initialize session state
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Main app logic
if st.session_state.show_register:
    register_page()
else:
    login_page()
