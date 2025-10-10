import streamlit as st

# =========================
# 🌈 Inject Custom CSS Style
# =========================
def inject_css():
    st.markdown("""
    <style>
    /* === BACKGROUND IMAGE === */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1503264116251-35a269479413?auto=format&fit=crop&w=1650&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: white !important;
    }
    .stApp::before {
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.6);
        z-index: 0;
    }

    /* === EVERYTHING ABOVE OVERLAY === */
    .stApp > * { position: relative; z-index: 1; }

    /* === TITLE SECTION === */
    h1, h2, h3, h4 {
        color: #fff !important;
        text-align: center;
        font-family: 'Poppins', sans-serif;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.4);
    }

    /* === CUSTOM CONTAINERS === */
    .glass-box {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 25px 35px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin-bottom: 25px;
    }

    /* === BUTTONS === */
    div.stButton > button {
        background-color: #1DB954 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 12px;
        padding: 10px 25px;
        transition: all 0.3s ease;
        font-size: 17px;
    }
    div.stButton > button:hover {
        background-color: #18a84d !important;
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: rgba(15, 25, 35, 0.85);
        backdrop-filter: blur(10px);
    }
    section[data-testid="stSidebar"] * {
        color: #F0F0F0 !important;
    }

    /* === PARAGRAPH TEXT === */
    p, span, label {
        color: #f8f8f8 !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif;
    }

    /* === INPUT FIELDS === */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9);
        border-radius: 8px;
        color: #000;
        font-weight: 500;
        border: none;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 🚀 MAIN APP LAYOUT
# =========================
def main():
    inject_css()
    st.set_page_config(page_title="Brain App", layout="wide")

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=100)
        st.title("🧠 Brain App")
        st.markdown("### The Future of Learning")
        st.markdown("---")
        mode = st.radio("Go to:", ["🏠 Home", "📊 Predict", "👨‍🏫 Teachers", "ℹ️ About"])

    st.title("Welcome to Brain App 💡")
    st.markdown("### Learn. Connect. Predict. Grow 🚀")

    # === HOME PAGE ===
    if mode == "🏠 Home":
        st.markdown("""
        <div class="glass-box">
        <h2>🎓 A Distraction-Free Study Platform</h2>
        <p>Brain App connects <b>teachers and students</b> like never before.  
        Teachers can create their own virtual tuition center, post learning videos, and engage directly with students — just like a <b>YouTube + WhatsApp</b> hybrid but focused only on knowledge.</p>
        </div>
        """, unsafe_allow_html=True)

        st.image("https://cdn.pixabay.com/photo/2022/06/16/15/38/artificial-intelligence-7267636_1280.jpg", use_container_width=True)
        st.markdown("""
        <div class="glass-box">
        <h3>Why Brain App?</h3>
        <ul>
            <li>📚 Distraction-free study environment</li>
            <li>💼 Teachers earn 80% + passive income</li>
            <li>🎥 Public teaching statuses — like short demos</li>
            <li>🚀 AI-powered analytics and feedback</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # === PREDICT PAGE ===
    elif mode == "📊 Predict":
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.subheader("🔮 AI Prediction Section")
        name = st.text_input("Enter your name:")
        score = st.number_input("Enter your study hours (per week):", min_value=0, max_value=100, value=10)
        distraction = st.slider("Distraction level (0 = Focused, 10 = Easily Distracted):", 0, 10, 5)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🚀 Predict My Performance"):
            result = (score * (10 - distraction)) / 10
            st.success(f"✨ {name}, your predicted study performance score is **{result:.2f}/100**!")

    # === TEACHERS PAGE ===
    elif mode == "👨‍🏫 Teachers":
        st.markdown("""
        <div class="glass-box">
        <h2>👩‍🏫 Become a Teacher</h2>
        <p>Create your own virtual tuition center. Set your subject, price, and upload your daily teaching statuses.  
        Students can view your style and join your class instantly.</p>
        <br>
        <ul>
            <li>🧠 Create tuition store (like Amazon)</li>
            <li>💰 Earn monthly income — Brain App keeps 20%</li>
            <li>🌍 Teach students worldwide</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Apply as a Teacher"):
            st.info("👋 We’ll contact you soon with your teaching dashboard access!")

    # === ABOUT PAGE ===
    elif mode == "ℹ️ About":
        st.markdown("""
        <div class="glass-box">
        <h2>About Brain App</h2>
        <p>Brain App is a futuristic educational platform that blends the power of **YouTube + WhatsApp** into one unified study ecosystem — 
        but without distractions.  
        It’s designed for <b>teachers, students, and lifelong learners</b>.</p>
        <br>
        <h3>🌐 Built With:</h3>
        <ul>
            <li>Python + Streamlit</li>
            <li>Custom CSS (Glassmorphism + Aesthetic UI)</li>
            <li>Responsive Design for All Devices</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
