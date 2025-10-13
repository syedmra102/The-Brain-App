import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import smtplib
from email.message import EmailMessage

# Streamlit page config with university branding
st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="wide")

# Firebase setup (using Streamlit secrets)
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["firebase"])
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Email setup (temporary; move to Firebase Functions for production)
EMAIL_ADDRESS = st.secrets.get("email", {}).get("address", "zada44919@gmail.com")
EMAIL_PASSWORD = st.secrets.get("email", {}).get("password", "mrgklwomlcwwfxrd")

# Custom CSS for split-screen design, inspired by student project UIs
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #e6f0fa 0%, #f5f5f5 100%); }
    .stButton>button {
        background-color: #0047AB;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
    }
    .stTextInput>div>input {
        border-radius: 8px;
        border: 1px solid #0047AB;
        padding: 10px;
    }
    .split-container {
        display: flex;
        min-height: 100vh;
    }
    .left-panel {
        flex: 1;
        background: url('https://images.unsplash.com/photo-1516321318423-f06f85e504b3') no-repeat center;
        background-size: cover;
    }
    .right-panel {
        flex: 1;
        padding: 40px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 20px;
    }
    h1, h2 { color: #0047AB; text-align: center; }
    .caption { color: #666; font-size: 0.9em; }
    @media (max-width: 768px) {
        .split-container { flex-direction: column; }
        .left-panel { height: 200px; }
        .right-panel { margin: 10px; padding: 20px; }
        .stTextInput>div>input { width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------- Helper Functions -------------------
def st_center_text(text, tag="p"):
    st.markdown(f"<{tag} style='text-align:center;'>{text}</{tag}>", unsafe_allow_html=True)

def st_center_form(form_callable, form_name="form"):
    with st.container():
        with st.form(form_name):
            return form_callable()

def st_center_widget(widget_callable):
    with st.container():
        return widget_callable()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_email(email):
    university_domains = ["university.edu", "uni.ac.uk"]  # Customize domains
    return any(email.endswith(f"@{domain}") for domain in university_domains)

def verify_recaptcha(response_token):
    secret_key = st.secrets["recaptcha"]["secret_key"]
    payload = {"secret": secret_key, "response": response_token}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
    return response.json().get("success", False)

def send_password_email(to_email, password):
    msg = EmailMessage()
    msg['Subject'] = 'Your Brain App Password'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"Hello,\n\nYour password is: {password}\n\n- The Brain App")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, "Password sent to your email successfully!"
    except Exception as e:
        return False, f"Failed to send email: {e}"

def export_user_data(uid):
    user_doc = db.collection('users').document(uid).get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

# ------------------- Pages -------------------
def sign_in_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="left-panel"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x50?text=University+Logo", use_column_width=True)
        st_center_text("The Brain App", tag="h1")
        st_center_text("Sign In", tag="h2")

        if st_center_widget(lambda: st.button("Sign in with Google", key="google_signin")):
            st.write("Redirecting to Google SSO... (Implement OAuth flow in Firebase)")

        def login_form():
            st.text_input("Username", key="signin_username")
            st.text_input("Password", type="password", key="signin_password")
            st.markdown('<p class="caption">Password must have 1 uppercase, 1 lowercase, 1 numeric character, and be at least 7 characters long.</p>', unsafe_allow_html=True)
            st.checkbox("Remember Me", key="remember_me")
            return st.form_submit_button("Login")

        login_btn = st_center_form(login_form, form_name="signin_form")
        st_center_text("If you don't have an account, please Sign Up!", tag="p")
        if st_center_widget(lambda: st.button("Forgot Password")):
            st.session_state.page = "forgot_password"
        if st_center_widget(lambda: st.button("Go to Sign Up")):
            st.session_state.page = "signup"

        if login_btn:
            with st.spinner("Logging in..."):
                username = st.session_state.get("signin_username", "")
                password = st.session_state.get("signin_password", "")
                user_doc = db.collection('users').document(username).get()
                if user_doc.exists:
                    user_info = user_doc.to_dict()
                    if check_password(password, user_info.get("password", "")):
                        st.session_state.user = {"username": username, "role": user_info.get("role", "student")}
                        st_center_widget(lambda: st.success(f"Welcome {username}, you logged in successfully!"))
                        st.write(f"Role: {st.session_state.user['role']}")
                    else:
                        st_center_widget(lambda: st.error("Incorrect password!"))
                else:
                    st_center_widget(lambda: st.error("Username does not exist. Please Sign Up."))
        st.markdown('</div>', unsafe_allow_html=True)

def forgot_password_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="left-panel"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x50?text=University+Logo", use_column_width=True)
        st_center_text("Forgot Password", tag="h2")
        def email_form():
            st.text_input("Enter your email", key="forgot_email")
            return st.form_submit_button("Send Password")
        
        submit_btn = st_center_form(email_form, form_name="forgot_form")
        st_center_widget(lambda: st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

        if submit_btn:
            with st.spinner("Sending email..."):
                email = st.session_state.get("forgot_email", "").strip()
                if not email:
                    st_center_widget(lambda: st.error("Please enter your email!"))
                    return
                if not validate_email(email):
                    st_center_widget(lambda: st.error("Please use a university email (@university.edu)!"))
                    return
                users = db.collection('users').get()
                found = False
                for user_doc in users:
                    user_info = user_doc.to_dict()
                    if user_info.get("email", "") == email:
                        success, msg = send_password_email(email, user_info.get("password", ""))
                        if success:
                            st_center_widget(lambda: st.success(msg))
                        else:
                            st_center_widget(lambda: st.error(msg))
                        found = True
                        break
                if not found:
                    st_center_widget(lambda: st.success("If this email exists, a password reset email would be sent!"))
        st.markdown('</div>', unsafe_allow_html=True)

def sign_up_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="left-panel"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x50?text=University+Logo", use_column_width=True)
        st_center_text("The Brain App", tag="h1")
        st_center_text("Sign Up", tag="h2")
        
        def signup_form():
            st.text_input("Username", key="signup_username")
            st.text_input("Email", key="signup_email")
            st.selectbox("Role", ["Student", "Faculty", "Admin"], key="signup_role")
            st.text_input("Password", type="password", key="signup_password")
            st.markdown('<p class="caption">Password must have 1 uppercase, 1 lowercase, 1 numeric character, and be at least 7 characters long.</p>', unsafe_allow_html=True)
            st.text_input("Confirm Password", type="password", key="signup_password2")
            st.markdown("""
                <script src="https://www.google.com/recaptcha/api.js"></script>
                <div class="g-recaptcha" data-sitekey="{}"></div>
            """.format(st.secrets["recaptcha"]["site_key"]), unsafe_allow_html=True)
            st.text_input("reCAPTCHA Response", key="recaptcha_response", type="hidden")
            return st.form_submit_button("Register")

        signup_btn = st_center_form(signup_form, form_name="signup_form")
        st_center_text("If you already have an account, please Sign In!", tag="p")
        st_center_widget(lambda: st.button("Go to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

        if signup_btn:
            with st.spinner("Registering..."):
                username = st.session_state.get("signup_username", "")
                email = st.session_state.get("signup_email", "")
                role = st.session_state.get("signup_role", "")
                password = st.session_state.get("signup_password", "")
                password2 = st.session_state.get("signup_password2", "")
                recaptcha_response = st.session_state.get("recaptcha_response", "")

                if not verify_recaptcha(recaptcha_response):
                    st_center_widget(lambda: st.error("Please complete the reCAPTCHA!"))
                    return
                if not validate_email(email):
                    st_center_widget(lambda: st.error("Please use a university email (@university.edu)!"))
                    return
                if username in [doc.id for doc in db.collection('users').get()]:
                    st_center_widget(lambda: st.error("Username already exists. Try logging in!"))
                elif password != password2:
                    st_center_widget(lambda: st.error("Passwords do not match!"))
                elif len(password) < 7 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
                    st_center_widget(lambda: st.error("Password must be at least 7 characters long, include uppercase, lowercase, and number."))
                else:
                    hashed_password = hash_password(password)
                    db.collection('users').document(username).set({
                        "email": email,
                        "password": hashed_password,
                        "role": role.lower()
                    })
                    st_center_widget(lambda: st.success("Sign up successful! You can now Sign In."))
        st.markdown('</div>', unsafe_allow_html=True)

def data_export_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="left-panel"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x50?text=University+Logo", use_column_width=True)
        if "user" not in st.session_state:
            st_center_text("Please log in to export
