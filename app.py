import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage

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
    st.error("Database connection error")
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
        msg.set_content(f"Your password is: {password}")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent to email"
    except:
        return False, "Failed to send email"

def validate_password(password):
    if len(password) < 7:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True

def get_user_by_email(email):
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).get()
    if query:
        for doc in query:
            return doc.id, doc.to_dict()
    return None, None

# Pages
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    user_doc = db.collection('users').document(username).get()
                    if user_doc.exists:
                        user_info = user_doc.to_dict()
                        if check_password(password, user_info.get("password", "")):
                            st.success("Login successful")
                        else:
                            st.error("Incorrect password")
                    else:
                        st.error("Username does not exist")

        col1, col2 = st.columns(2)
        with col1:
            st.button("Forgot Password", use_container_width=True, on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        with col2:
            st.button("Create Account", use_container_width=True, on_click=lambda: st.session_state.update({"page":"signup"}))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>Forgot Password</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("forgot_form"):
            email = st.text_input("Enter your email")
            submit_btn = st.form_submit_button("Send Password")
            
            if submit_btn:
                if not email:
                    st.error("Please enter email")
                else:
                    username, user_info = get_user_by_email(email)
                    if user_info:
                        original_password = user_info.get("plain_password", "")
                        if original_password:
                            success, message = send_password_email(email, username, original_password)
                            if success:
                                st.success("Password sent to email")
                            else:
                                st.error("Failed to send email")
                        else:
                            st.error("No password found")
                    else:
                        st.info("If email exists, password will be sent")

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
                elif not validate_password(password):
                    st.error("Password must be 7+ characters with uppercase, lowercase, and number")
                else:
                    if db.collection('users').document(username).get().exists:
                        st.error("Username already exists")
                    else:
                        existing_user, _ = get_user_by_email(email)
                        if existing_user:
                            st.error("Email already registered")
                        else:
                            hashed_password = hash_password(password)
                            user_data = {
                                "email": email,
                                "password": hashed_password,
                                "plain_password": password,
                                "role": "student"
                            }
                            db.collection('users').document(username).set(user_data)
                            st.success("Account created successfully")
                            st.session_state.page = "signin"
                            st.rerun()

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
