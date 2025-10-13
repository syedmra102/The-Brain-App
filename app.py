import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage
import json

# -------------------- Page Config --------------------
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# -------------------- Firebase Initialization with YOUR KEY --------------------
try:
    # Get Firebase credentials from Streamlit secrets
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
    st.success("Firebase connected successfully!")
    
except Exception as e:
    st.error(f"Firebase connection failed: {str(e)}")
    st.stop()

# -------------------- Email Setup --------------------
EMAIL_ADDRESS = "zada44919@gmail.com"
EMAIL_PASSWORD = "mrgklwomlcwwfxrd"

# -------------------- Helper Functions --------------------
def st_center_text(text, tag="p"):
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

def st_center_form(form_callable, col_ratio=[1,3,1], form_name="form"):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        with st.form(form_name):
            return form_callable()

def st_center_widget(widget_callable, col_ratio=[1,3,1]):
    col1, col2, col3 = st.columns(col_ratio)
    with col2:
        return widget_callable()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def send_password_email(to_email, username, password):
    """Send email with ORIGINAL password (not hashed)"""
    msg = EmailMessage()
    msg['Subject'] = 'Your Brain App Password'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"""
    Hello {username}!

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
        return True, "Password sent successfully to your email!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def validate_password(password):
    """Check if password meets requirements"""
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
    """Find user by email in Firebase"""
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).get()
    if query:
        for doc in query:
            return doc.id, doc.to_dict()  # username, user_data
    return None, None

# -------------------- Pages --------------------
def sign_in_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign In to Your Account", tag="h3")

    def login_form():
        username = st.text_input("Username", key="signin_username")
        password = st.text_input("Password", type="password", key="signin_password")
        
        # Password requirements
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7C3AED;">
            <div style="font-weight: 600; margin-bottom: 10px;">Password Requirements:</div>
            <div>• At least 7 characters</div>
            <div>• One uppercase letter</div>
            <div>• One lowercase letter</div>
            <div>• One number</div>
        </div>
        """, unsafe_allow_html=True)
        
        return st.form_submit_button("Login"), username, password

    login_btn, username, password = st_center_form(login_form, form_name="signin_form")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("Forgot Password", on_click=lambda: st.session_state.update({"page":"forgot_password"}))
        st.button("Create Account", on_click=lambda: st.session_state.update({"page":"signup"}))

    if login_btn:
        if not username or not password:
            st.error("Please fill in all fields!")
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
                    st.success(f"Welcome back {username}! Login successful!")
                    st.balloons()
                else:
                    st.error("Incorrect password!")
            else:
                st.error("Username does not exist.")
        except Exception as e:
            st.error(f"Login error: {str(e)}")

def forgot_password_page():
    st_center_text("Forgot Password", tag="h2")
    st_center_text("Enter your email to receive your password", tag="h4")

    def email_form():
        email = st.text_input("Enter your registered email", key="forgot_email")
        return st.form_submit_button("Send My Password"), email

    submit_btn, email = st_center_form(email_form, form_name="forgot_form")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"}))

    if submit_btn:
        if not email:
            st.error("Please enter your email!")
            return
            
        try:
            username, user_info = get_user_by_email(email)
            if user_info:
                # Send ORIGINAL password (not hashed)
                original_password = user_info.get("plain_password", "")
                if original_password:
                    success, message = send_password_email(email, username, original_password)
                    if success:
                        st.success(f"Password sent to {email}!")
                    else:
                        st.error(f"{message}")
                else:
                    st.error("No password found for this account.")
            else:
                st.info("If this email exists in our system, you will receive a password email shortly.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def sign_up_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Create Your Account", tag="h3")

    def signup_form():
        username = st.text_input("Choose Username", key="signup_username")
        email = st.text_input("Email Address", key="signup_email")
        role = st.selectbox("Role", ["Student", "Faculty", "Admin"], key="signup_role")
        password = st.text_input("Password", type="password", key="signup_password")
        password2 = st.text_input("Confirm Password", type="password", key="signup_password2")
        
        # Real-time password validation
        if password:
            is_valid, msg = validate_password(password)
            if is_valid:
                st.success(msg)
            else:
                st.error(msg)
                
        return st.form_submit_button("Create Account"), username, email, role, password, password2

    signup_btn, username, email, role, password, password2 = st_center_form(signup_form, form_name="signup_form")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"}))

    if signup_btn:
        # Validation
        if not all([username, email, password, password2]):
            st.error("Please fill in all fields!")
            return
            
        if password != password2:
            st.error("Passwords do not match!")
            return
            
        is_valid, msg = validate_password(password)
        if not is_valid:
            st.error(f"{msg}")
            return

        try:
            # Check if username exists
            if db.collection('users').document(username).get().exists:
                st.error("Username already exists!")
                return
                
            # Check if email exists
            existing_user, _ = get_user_by_email(email)
            if existing_user:
                st.error("Email already registered!")
                return

            # Create user in Firebase
            hashed_password = hash_password(password)
            user_data = {
                "email": email,
                "password": hashed_password,
                "plain_password": password,  # Store original password for email recovery
                "role": role.lower(),
                "created_at": firestore.SERVER_TIMESTAMP
            }
            
            db.collection('users').document(username).set(user_data)
            
            # Send welcome email with ORIGINAL password
            success, email_msg = send_password_email(email, username, password)
            if success:
                st.success(f"Account created successfully! {email_msg}")
                st.balloons()
                # Auto redirect to login after 3 seconds
                st.info("Redirecting to login page...")
                st.session_state.page = "signin"
                st.rerun()
            else:
                st.warning(f" Account created but {email_msg}")
                
        except Exception as e:
            st.error(f" Registration failed: {str(e)}")

def user_dashboard_page():
    if "user" not in st.session_state:
        st.session_state.page = "signin"
        st.rerun()
        return
        
    user = st.session_state.user
    st_center_text(f" Welcome, {user['username']}!", tag="h1")
    st_center_text(f"Role: {user['role'].title()}", tag="h3")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("View My Data"):
            try:
                user_doc = db.collection('users').document(user['username']).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    # Remove sensitive data for display
                    safe_data = {k: v for k, v in user_data.items() if k != 'password'}
                    st.json(safe_data)
                else:
                    st.error(" User data not found")
            except Exception as e:
                st.error(f" Error loading data: {str(e)}")
        
        if st.button(" Logout"):
            st.session_state.pop("user", None)
            st.session_state.page = "signin"
            st.rerun()

# -------------------- Main App Logic --------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

# Check if user is already logged in
if "user" in st.session_state and st.session_state.page == "signin":
    st.session_state.page = "dashboard"

# Page routing
if st.session_state.page == "signin":
    sign_in_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
elif st.session_state.page == "dashboard":
    user_dashboard_page()
