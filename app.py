import streamlit as st
import re

# Page configuration
st.set_page_config(
    page_title="The Brain App",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional aesthetic look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 3.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .form-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.8rem;
        color: #2d3748;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stTextInput>div>div>input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 14px 28px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .success-message {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 500;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3);
    }
    
    .error-message {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 500;
        margin: 1rem 0;
    }
    
    .password-caption {
        color: #718096;
        font-size: 0.9rem;
        text-align: center;
        margin: 1rem 0;
        line-height: 1.5;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Main title with gradient effect
st.markdown('<div class="main-title">🧠 The Brain App</div>', unsafe_allow_html=True)

# Center the login form
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Form title
        st.markdown('<div class="form-title">Access Your Account</div>', unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input(
                "👤 Username",
                placeholder="Enter your username"
            )
            
            password = st.text_input(
                "🔒 Password", 
                type="password",
                placeholder="Enter your password"
            )
            
            # Password requirements
            st.markdown("""
            <div class="password-caption">
                <strong>Password Requirements:</strong><br>
                • Minimum 7 characters<br>
                • At least one uppercase letter (A-Z)<br>
                • At least one lowercase letter (a-z)<br>
                • At least one number (0-9)
            </div>
            """, unsafe_allow_html=True)
            
            login_btn = st.form_submit_button("🚀 Sign In")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Handle form submission
if login_btn:
    if not username or not password:
        st.markdown("""
        <div class="error-message">
            ⚠️ Please fill in both username and password
        </div>
        """, unsafe_allow_html=True)
    else:
        # Password validation
        if len(password) < 7:
            st.markdown("""
            <div class="error-message">
                ⚠️ Password must be at least 7 characters long
            </div>
            """, unsafe_allow_html=True)
        elif not re.search(r"[A-Z]", password):
            st.markdown("""
            <div class="error-message">
                ⚠️ Password must include at least one uppercase letter
            </div>
            """, unsafe_allow_html=True)
        elif not re.search(r"[a-z]", password):
            st.markdown("""
            <div class="error-message">
                ⚠️ Password must include at least one lowercase letter
            </div>
            """, unsafe_allow_html=True)
        elif not re.search(r"[0-9]", password):
            st.markdown("""
            <div class="error-message">
                ⚠️ Password must include at least one number
            </div>
            """, unsafe_allow_html=True)
        else:
            # Success message
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div class="success-message">
                    🎉 Welcome <span class="gradient-text">{username}</span>!<br>
                    You have successfully logged in to The Brain App!
                </div>
                """, unsafe_allow_html=True)

# Additional aesthetic elements
st.markdown("""
<br><br>
<div style='text-align: center; color: rgba(255,255,255,0.7); font-size: 0.9rem;'>
    Secure • Professional • Aesthetic
</div>
""", unsafe_allow_html=True)
