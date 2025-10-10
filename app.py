import streamlit as st

def inject_style():
    css = """
    <style>
    /* 🌄 Background image with dark overlay */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1503264116251-35a269479413?auto=format&fit=crop&w=1650&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        position: relative;
        color: white;
        min-height: 100vh;
        overflow: hidden;
    }
    .stApp::before {
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        z-index: 0;
    }

    /* ✨ Bring all elements above the overlay */
    .stApp > * {
        position: relative;
        z-index: 1;
    }

    /* 🎨 Button styling */
    div.stButton > button, .stButton button {
        background-color: #1DB954 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover, .stButton button:hover {
        background-color: #169e43 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    /* 🧱 Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(8, 61, 107, 0.85) !important;
        backdrop-filter: blur(6px);
        color: #EAF6FF !important;
    }
    section[data-testid="stSidebar"] * {
        color: #EAF6FF !important;
    }

    /* 🧾 Headers and text */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }

    p, label, span {
        color: #F5F5F5 !important;
        font-size: 16px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
