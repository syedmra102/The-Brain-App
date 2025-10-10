import streamlit as st

# ==============================
# 🌈 Custom Styling
# ==============================
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

    /* 🌟 Input fields */
    .stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.9);
        color: #000;
        border-radius: 8px;
        border: none;
        padding: 8px 10px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ==============================
# 🚀 App Layout
# ==============================
def main():
    inject_style()

    # Sidebar
    with st.sidebar:
        st.title("🧠 Brain App")
        st.write("Smart Learning & AI Platform")
        st.markdown("---")
        st.write("Choose a mode:")
        mode = st.radio("Select:", ["Home", "Predict", "About"])

    # Main Area
    st.title("Welcome to the Brain App 💡")
    st.markdown("### Learn. Create. Predict. Grow 🚀")

    if mode == "Home":
        st.markdown("""
        This app helps students and professionals use AI tools for smarter learning and predictions.  
        Use this app to analyze data, make predictions, or explore new ideas.
        """)
        st.image("https://cdn.pixabay.com/photo/2017/01/31/13/14/artificial-intelligence-2027495_1280.png", use_container_width=True)
        st.markdown("---")
        st.success("✨ Tip: Customize this area for your own content (courses, tools, etc.)")

    elif mode == "Predict":
        st.subheader("🔮 Predict Something Smart")
        name = st.text_input("Enter your name:")
        value = st.number_input("Enter a value:", min_value=0.0, max_value=10000.0, value=100.0)
        if st.button("Predict Now"):
            st.success(f"Hey {name}, your prediction result is: **{value * 2:.2f}** 🎯")

    elif mode == "About":
        st.header("About This App 🧩")
        st.write("""
        The **Brain App** is built using **Streamlit** — a modern Python framework for building data web apps easily.

        **Features:**
        - Beautiful background design
        - Fast performance
        - AI-ready structure
        - Easy customization for ML projects or educational tools
        """)
        st.info("You can add your ML model, course system, or student dashboard here.")

# Run the app
if __name__ == "__main__":
    main()
