import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage

# -------------------- Page Config --------------------
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# -------------------- Firebase Initialization --------------------
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
    st.error(f"Firebase connection failed: {str(e)}")
    st.stop()

# -------------------- Email Setup --------------------
EMAIL_ADDRESS = "zada44919@gmail.com"
EMAIL_PASSWORD = "mrgklwomlcwwfxrd"

# -------------------- Helper Functions --------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def send_password_email(to_email, username, password):
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
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent successfully to your email"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

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
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).get()
    if query:
        for doc in query:
            return doc.id, doc.to_dict()
    return None, None

# -------------------- Pages --------------------
def sign_in_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign In to Your Account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            # Simple password requirements text
            st.caption("Password must contain at least 7 characters, one uppercase, one lowercase, and one number.")
            
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                    return
                    
                try:
                    user_doc = db.collection('users').document(username).get()
                    if user_doc.exists:
                        user_info = user_doc.to_dict()
                        if check_password(password, user_info.get("password", "")):
                            st.session_state.user = {
                                "username": username,
                                "email": user_info.get("email", ""),
                                "role": user_info.get("role", "student")
                            }
                            st.success(f"Welcome back {username}")
                        else:
                            st.error("Incorrect password")
                    else:
                        st.error("Username does not exist")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")

        st.button("Forgot Password", on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        st.button("Create Account", on_click=lambda: st.session_state.update({"page":"signup"}))

def forgot_password_page():
    st.markdown("<h2 style='text-align: center;'>Forgot Password</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Enter your email to receive your password</h4>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("forgot_form"):
            email = st.text_input("Enter your registered email")
            submit_btn = st.form_submit_button("Send My Password")
            
            if submit_btn:
                if not email:
                    st.error("Please enter your email")
                    return
                    
                try:
                    username, user_info = get_user_by_email(email)
                    if user_info:
                        original_password = user_info.get("plain_password", "")
                        if original_password:
                            success, message = send_password_email(email, username, original_password)
                            if success:
                                st.success(f"Password sent to {email}")
                            else:
                                st.error(f"{message}")
                        else:
                            st.error("No password found for this account")
                    else:
                        st.info("If this email exists in our system, you will receive a password email")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"}))

def sign_up_page():
    st.markdown("<h1 style='text-align: center;'>The Brain App</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create Your Account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Choose Username")
            email = st.text_input("Email Address")
            role = st.selectbox("Role", ["Student", "Faculty", "Admin"])
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm Password", type="password")
            
            # Real-time password validation
            if password:
                is_valid, msg = validate_password(password)
                if is_valid:
                    st.success(msg)
                else:
                    st.error(msg)
                    
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not all([username, email, password, password2]):
                    st.error("Please fill in all fields")
                    return
                    
                if password != password2:
                    st.error("Passwords do not match")
                    return
                    
                is_valid, msg = validate_password(password)
                if not is_valid:
                    st.error(f"{msg}")
                    return

                try:
                    if db.collection('users').document(username).get().exists:
                        st.error("Username already exists")
                        return
                        
                    existing_user, _ = get_user_by_email(email)
                    if existing_user:
                        st.error("Email already registered")
                        return

                    hashed_password = hash_password(password)
                    user_data = {
                        "email": email,
                        "password": hashed_password,
                        "plain_password": password,
                        "role": role.lower(),
                        "created_at": firestore.SERVER_TIMESTAMP
                    }
                    
                    db.collection('users').document(username).set(user_data)
                    
                    success, email_msg = send_password_email(email, username, password)
                    if success:
                        st.success(f"Account created successfully. {email_msg}")
                        st.session_state.page = "signin"
                        st.rerun()
                    else:
                        st.warning(f"Account created but {email_msg}")
                        
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")

        st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"}))

def user_dashboard_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
        
    user = st.session_state.user
    st.markdown(f"<h1 style='text-align: center;'>Welcome, {user['username']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Role: {user['role'].title()}</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("View My Data"):
            try:
                user_doc = db.collection('users').document(user['username']).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    safe_data = {k: v for k, v in user_data.items() if k != 'password'}
                    st.json(safe_data)
                else:
                    st.error("User data not found")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
        
        if st.button("Logout"):
            st.session_state.pop("user", None)
            st.session_state.page = "signin"
            st.rerun()

# -------------------- Main App Logic --------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

if "user" in st.session_state and st.session_state.page == "signin":
    st.session_state.page = "dashboard"

if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
elif st.session_state.page == "dashboard":
    user_dashboard_page()
