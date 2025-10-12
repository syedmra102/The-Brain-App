import streamlit as st
import hashlib
import re

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_strength(password):
    """Check password strength and return detailed report"""
    if len(password) < 6:
        return {
            'strong': False,
            'score': 0,
            'message': 'Password too short (min 6 characters)',
            'details': {
                'length': False,
                'capital': False,
                'small': False, 
                'digit': False
            }
        }
    
    # Count requirements
    capital_count = len(re.findall(r'[A-Z]', password))
    small_count = len(re.findall(r'[a-z]', password))
    digit_count = len(re.findall(r'[0-9]', password))
    
    # Calculate score
    score = 0
    details = {
        'length': len(password) >= 6,
        'capital': capital_count >= 1,
        'small': small_count >= 3,
        'digit': digit_count >= 1
    }
    
    if details['length']: score += 1
    if details['capital']: score += 1  
    if details['small']: score += 1
    if details['digit']: score += 1
    
    # Generate message
    messages = []
    if not details['capital']:
        messages.append("1 capital letter (A-Z)")
    if not details['small']:
        messages.append("3 small letters (a-z)")
    if not details['digit']:
        messages.append("1 digit (0-9)")
    
    if messages:
        message = "Missing: " + ", ".join(messages)
        strong = False
    else:
        message = "✅ Strong password!"
        strong = True
    
    return {
        'strong': strong,
        'score': score,
        'message': message,
        'details': details
    }

def show_password_strength_meter(password):
    """Show visual password strength meter"""
    if not password:
        return
    
    result = check_password_strength(password)
    
    # Strength meter
    st.write("**Password Strength:**")
    
    # Visual progress bar
    progress = result['score'] / 4  # 4 total requirements
    st.progress(progress)
    
    # Color coded message
    if result['strong']:
        st.success(result['message'])
    else:
        st.error(result['message'])
    
    # Detailed requirements
    st.write("**Requirements:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"📏 Length (6+): {'✅' if result['details']['length'] else '❌'}")
        st.write(f"🔠 Capital letter: {'✅' if result['details']['capital'] else '❌'}")
    
    with col2:
        st.write(f"🔡 3 Small letters: {'✅' if result['details']['small'] else '❌'}")
        st.write(f"🔢 1 Digit: {'✅' if result['details']['digit'] else '❌'}")

def register_page():
    st.markdown("""
    <div style='background:#1E90FF; padding:2rem; border-radius:10px; text-align:center; color:white; margin-bottom:2rem;'>
        <h1>📝 Create Your Account</h1>
        <p>Secure password required</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("register_form"):
        st.subheader("Account Details")
        
        new_user = st.text_input("👤 Username")
        email = st.text_input("📧 Email")
        
        st.subheader("Password Requirements")
        st.write("Your password must contain:")
        st.write("• **1 CAPITAL letter** (A-Z)")
        st.write("• **3 small letters** (a-z)") 
        st.write("• **1 digit** (0-9)")
        st.write("• **Minimum 6 characters**")
        
        new_pass = st.text_input("🔒 Create Password", type="password", 
                               key="new_pass", help="Follow the requirements above")
        
        # Show password strength in real-time
        if new_pass:
            show_password_strength_meter(new_pass)
        
        confirm_pass = st.text_input("🔒 Confirm Password", type="password", key="confirm_pass")
        
        agree_terms = st.checkbox("I agree to Terms and Conditions")
        
        register_btn = st.form_submit_button("🚀 Create Account", use_container_width=True)
        
        if register_btn:
            # Validate all fields
            if not all([new_user, email, new_pass, confirm_pass]):
                st.error("❌ Please fill all fields")
            
            elif new_user in st.session_state.users:
                st.error("❌ Username already exists!")
            
            elif new_pass != confirm_pass:
                st.error("❌ Passwords don't match!")
            
            elif not agree_terms:
                st.error("❌ Please agree to terms and conditions")
            
            else:
                strength_result = check_password_strength(new_pass)
                
                if strength_result['strong']:
                    # Save user
                    st.session_state.users[new_user] = {
                        'password': hash_password(new_pass),
                        'email': email,
                        'created_at': str(st.datetime.now())
                    }
                    st.success("✅ Account created successfully!")
                    st.balloons()
                    st.session_state.current_page = 'login'
                    st.rerun()
                else:
                    st.error(f"❌ {strength_result['message']}")

# Initialize
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'register'

# Run register page
register_page()
