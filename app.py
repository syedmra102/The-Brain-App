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

def st_center_message(func, message):
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        func(message)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
        return True, "Password sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {e}"

def export_user_data(uid):
    user_doc = db.collection('users').document(uid).get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

# -------------------- Pages --------------------
def sign_in_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign In", tag="h2")

    def login_form():
        st.text_input("Username", key="signin_username")
        st.text_input("Password", type="password", key="signin_password")
        return st.form_submit_button("Login")

    login_btn = st_center_form(login_form, form_name="signin_form")

    if st_center_widget(lambda: st.button("Forgot Password")):
        st.session_state.page = "forgot_password"

    if st_center_widget(lambda: st.button("Go to Sign Up")):
        st.session_state.page = "signup"

    if login_btn:
        username = st.session_state.get("signin_username", "")
        password = st.session_state.get("signin_password", "")
        user_doc = db.collection('users').document(username).get()
        if user_doc.exists:
            user_info = user_doc.to_dict()
            if check_password(password, user_info.get("password","")):
                st.session_state.user = {"username": username, "role": user_info.get("role","student")}
                st_center_message(st.success, f"Welcome {username}, logged in successfully!")
                st_center_message(st.write, f"Role: {st.session_state.user['role']}")
            else:
                st_center_message(st.error, "Incorrect password!")
        else:
            st_center_message(st.error, "Username does not exist.")

def forgot_password_page():
    st_center_text("Forgot Password", tag="h2")

    def email_form():
        st.text_input("Enter your email", key="forgot_email")
        return st.form_submit_button("Send Password")

    submit_btn = st_center_form(email_form, form_name="forgot_form")
    st_center_widget(lambda: st.button("Back to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

    if submit_btn:
        email = st.session_state.get("forgot_email","").strip()
        users = db.collection('users').get()
        found = False
        for user_doc in users:
            user_info = user_doc.to_dict()
            if user_info.get("email","") == email:
                success, msg = send_password_email(email, user_info.get("plain_password",""))
                if success:
                    st_center_message(st.success, msg)
                else:
                    st_center_message(st.error, msg)
                found = True
                break
        if not found:
            st_center_message(st.success, "If this email exists, a password reset email would be sent!")

def sign_up_page():
    st_center_text("The Brain App", tag="h1")
    st_center_text("Sign Up", tag="h2")

    def signup_form():
        st.text_input("Username", key="signup_username")
        st.text_input("Email", key="signup_email")
        st.selectbox("Role", ["Student","Faculty","Admin"], key="signup_role")
        st.text_input("Password", type="password", key="signup_password")
        st.text_input("Confirm Password", type="password", key="signup_password2")
        return st.form_submit_button("Register")

    signup_btn = st_center_form(signup_form, form_name="signup_form")
    st_center_widget(lambda: st.button("Go to Sign In", on_click=lambda: st.session_state.update({"page":"signin"})))

    if signup_btn:
        username = st.session_state.get("signup_username","")
        email = st.session_state.get("signup_email","")
        role = st.session_state.get("signup_role","")
        password = st.session_state.get("signup_password","")
        password2 = st.session_state.get("signup_password2","")

        if username in [doc.id for doc in db.collection('users').get()]:
            st_center_message(st.error, "Username already exists!")
        elif password != password2:
            st_center_message(st.error, "Passwords do not match!")
        elif len(password)<7 or not re.search(r"[A-Z]",password) or not re.search(r"[a-z]",password) or not re.search(r"[0-9]",password):
            st_center_message(st.error, "Password must be at least 7 characters and contain uppercase, lowercase, and number.")
        else:
            hashed_password = hash_password(password)
            db.collection('users').document(username).set({
                "email": email,
                "password": hashed_password,
                "plain_password": password,
                "role": role.lower()
            })
            success, msg = send_password_email(email, password)
            if success:
                st_center_message(st.success, f"Sign up successful! {msg}")
            else:
                st_center_message(st.error, f"Sign up successful, but {msg}")

def data_export_page():
    if "user" not in st.session_state:
        st_center_text("Please log in to export your data.", tag="h2")
        return
    st_center_text("Export Your Data", tag="h2")
    if st_center_widget(lambda: st.button("Export My Data")):
        user_data = export_user_data(st.session_state.user["username"])
        if user_data:
            st.json(user_data)
            st_center_message(st.success, "Data exported successfully!")
        else:
            st_center_message(st.error, "No data found.")

# -------------------- Main --------------------
if "page" not in st.session_state:
    st.session_state.page = "signin"

if st.session_state.page=="signin":
    sign_in_page()
elif st.session_state.page=="signup":
    sign_up_page()
elif st.session_state.page=="forgot_password":
    forgot_password_page()
elif st.session_state.page=="export_data":
    data_export_page()
