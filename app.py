import streamlit as st
import re
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="The Brain App", page_icon="🧠", layout="centered")

# -------- Firebase Setup ----------
if not firebase_admin._apps:
    f = st.secrets["firebase"]
    cred_dict = {
        "type": f["type"],
        "project_id": f["project_id"],
        "private_key_id": f["private_key_id"],
        "private_key": f["private_key"].replace("\\n","\n"),
        "client_email": f["client_email"],
        "client_id": f["client_id"],
        "auth_uri": f["auth_uri"],
        "token_uri": f["token_uri"],
        "auth_provider_x509_cert_url": f["auth_provider_x509_cert_url"],
        "client_x509_cert_url": f["client_x509_cert_url"]
    }
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------- Email Setup from Secrets ----------
EMAIL_ADDRESS = st.secrets["email"]["address"]
EMAIL_PASSWORD = st.secrets["email"]["app_password"]

# --------- Helper Functions ---------
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

def validate_email(email):
    domains = ["university.edu","uni.ac.uk"]
    return any(email.endswith(f"@{d}") for d in domains)

def send_password_email(to_email, password):
    msg = EmailMessage()
    msg['Subject'] = "Your Brain App Password"
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
