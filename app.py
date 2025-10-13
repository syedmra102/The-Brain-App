import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage
import time

# Page config
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# Firebase setup
try:
    firebase_secrets = st.secrets["firebase"]
    
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": firebase_secrets["type"],
            "project_id": firebase_secrets["project_id"],
            "private_key_id": firebase_secrets["private_key_id"],
            "private_key": firebase_secrets["private_key"].replace("\\n", "\n"),
            "client_email": firebase_secrets["client_email"],
            "client_id": firebase_secrets["client_id"],
            "auth_uri": firebase_secrets["auth_uri"],
            "token_uri": firebase_secrets["token_uri"],
            "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_secrets["client_x509_cert_url"]
        })
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
except Exception as e:
    st.error("System temporarily unavailable")
    st.stop()

# Email setup
EMAIL_ADDRESS = "zada44919@gmail.com"
EMAIL_PASSWORD = "mrgklwomlcwwfxrd"

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def send_password_email(to_email, username, password):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Your Brain App Password'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg.set_content(f"""
        Hello {username}

        Your Brain App Account Details:

        Username: {username}
        Password: {password}

        Please keep this information secure.

        Best regards,
        The Brain App Team
        """)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent to your email"
    except Exception as e:
        return False, "Email service temporarily unavailable"

def validate_password(password):
    if len(password) < 7:
        return False, "Password must be at least 7 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def get_user_by_email(email):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).get()
        if query:
            for doc in query:
                return doc.id, doc.to_dict()
        return None, None
    except:
        return None, None

def sanitize_input(text):
    return re.sub(r'[<>"\']', '', text.strip())

# Pages
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            st.write("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
            
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    # Show loading
                    with st.spinner("Signing in..."):
                        time.sleep(1)  # Simulate processing
                        
                        username_clean = sanitize_input(username)
                        password_clean = sanitize_input(password)
                        
                        try:
                            user_doc = db.collection('users').document(username_clean).get()
                            if user_doc.exists:
                                user_info = user_doc.to_dict()
                                if check_password(password_clean, user_info.get("password", "")):
                                    st.session_state.user = {
                                        "username": username_clean,
                                        "email": user_info.get("email", ""),
                                        "role": user_info.get("role", "student")
                                    }
                                    st.success("Login successful")
                                    # Don't store plain password
                                    if "plain_password" in user_info:
                                        del user_info["plain_password"]
                                else:
                                    st.error("Invalid username or password")
                            else:
                                st.error("Invalid username or password")
                        except:
                            st.error("System error. Please try again.")

        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("Create Account", use_container_width=True, on_allow_html=True, on_click=lambda: st.session_state.update({"page":"signup"}))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>Forgot Password</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("forgot_form"):
            email = st.text_input("Enter your email")
            submit_btn = st.form_submit_button("Send Password")
            
            if submit_btn:
                if not email:
                    st.error("Please enter your email")
                else:
                    email_clean = sanitize_input(email)
                    with st.spinner("Sending password..."):
                        time.sleep(1)
                        
                        username, user_info = get_user_by_email(email_clean)
                        if user_info:
                            original_password = user_info.get("plain_password", "")
                            if original_password:
                                success, message = send_password_email(email_clean, username, original_password)
                                if success:
                                    st.success("Password sent to your email")
                                else:
                                    st.error("Failed to send email")
                            else:
                                st.error("Account not found")
                        else:
                            st.info("If this email exists, password will be sent")

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

def sign_up_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                # Only show ONE error message
                if not all([username, email, password, password2]):
                    st.error("Please fill in all fields")
                elif password != password2:
                    st.error("Passwords do not match")
                elif not validate_password(password)[0]:
                    st.error("Password must be 7+ characters with uppercase, lowercase, and number")
                else:
                    with st.spinner("Creating account..."):
                        time.sleep(1)
                        
                        username_clean = sanitize_input(username)
                        email_clean = sanitize_input(email)
                        password_clean = sanitize_input(password)
                        
                        try:
                            if db.collection('users').document(username_clean).get().exists:
                                st.error("Username already exists")
                            else:
                                existing_user, _ = get_user_by_email(email_clean)
                                if existing_user:
                                    st.error("Email already registered")
                                else:
                                    hashed_password = hash_password(password_clean)
                                    user_data = {
                                        "email": email_clean,
                                        "password": hashed_password,
                                        "plain_password": password_clean,
                                        "role": "student"
                                    }
                                    db.collection('users').document(username_clean).set(user_data)
                                    st.success("Account created successfully")
                                    st.session_state.page = "signin"
                                    st.rerun()
                        except:
                            st.error("System error. Please try again.")

        st.button("Back to Sign In", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signin"}))

# Main app
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
