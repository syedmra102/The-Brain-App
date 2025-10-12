import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="The BrainApp",
    page_icon="🧠",
    layout="centered"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .login-container {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        width: 100%;
        max-width: 450px;
        text-align: center;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .app-subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .stTextInput>div>div>input, .stTextInput>div>div>input:focus {
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
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
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    .password-requirements {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 1.5rem 0;
        text-align: left;
        border-left: 4px solid #667eea;
    }
    
    .requirement-text {
        font-size: 0.9rem;
        color: #6c757d;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main login form
col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # App title and subtitle
    st.markdown('<div class="app-title">The BrainApp</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Intelligent Learning Platform</div>', unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        # Password requirements
        st.markdown("""
        <div class="password-requirements">
            <div class="requirement-text">🔐 Password must contain:</div>
            <div class="requirement-text">• At least 7 characters</div>
            <div class="requirement-text">• One uppercase letter</div>
            <div class="requirement-text">• One lowercase letter</div>
            <div class="requirement-text">• One number</div>
        </div>
        """, unsafe_allow_html=True)
        
        login_button = st.form_submit_button("🚀 Login to BrainApp")
        
        if login_button:
            if username and password:
                st.success(f"Welcome back, {username}! 🎉")
            else:
                st.error("Please fill in all fields! ⚠️")
    
    # Additional links
    st.markdown("""
    <div style="margin-top: 2rem; color: #6c757d; font-size: 0.9rem;">
        Don't have an account? <a href="#" style="color: #667eea; text-decoration: none; font-weight: 500;">Sign up here</a>
    </div>
    <div style="margin-top: 0.5rem; color: #6c757d; font-size: 0.9rem;">
        <a href="#" style="color: #667eea; text-decoration: none; font-weight: 500;">Forgot password?</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
