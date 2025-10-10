import streamlit as st

# =========================
# 🌈 CUSTOM CSS — AESTHETIC MOUNTAIN THEME
# =========================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    /* Background Image with Overlay */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
        color: #f0f0f0;
    }

    .stApp::before {
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        z-index: 0;
    }

    /* Everything above overlay */
    .stApp > * { position: relative; z-index: 1; }

    /* Headings */
    h1, h2, h3 {
        color: #fff !important;
        text-align: center;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        letter-spacing: 1px;
    }

    /* Glassy Container */
    .glass-box {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px 40px;
        backdrop-filter: blur(15px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        margin-bottom: 25px;
    }

    .glass-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(20, 30, 40, 0.9);
        backdrop-filter: blur(10px);
    }

    section[data-testid="stSidebar"] * {
        color: #f0f0f0 !important;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #0F9D58, #34A853);
        border: none;
        color: white !important;
        border-radius: 15px;
        padding: 10px 30px;
        font-size: 17px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 3px 8px rgba(0,0,0,0.4);
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #34A853, #0F9D58);
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(0,0,0,0.5);
    }

    /* Text & Paragraphs */
    p, li, span, label {
        color: #eaeaea !important;
        font-size: 16px !important;
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        color: #000;
        border: none;
        padding: 10px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================
# 🚀 MAIN APP LAYOUT
# =========================
def main():
    inject_css()
    st.set_page_config(page_title="Brain App 🌄", layout="wide")

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=100)
        st.title("🧠 Brain App")
        st.markdown("**A Calm Place to Learn & Grow** 🌄")
        st.markdown("---")
        mode = st.radio("Go to:", ["🏔 Home", "📊 Predict", "👨‍🏫 Teachers", "🌍 About"])

    # Home Page
    if mode == "🏔 Home":
        st.markdown("<h1>Welcome to The Brain App 🌄</h1>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-box">
        <h2>✨ Calm Learning in a Mountain Ambience</h2>
        <p>Brain App combines <b>YouTube + WhatsApp</b> in a distraction-free learning zone.  
        Teachers create tuition centers, share real teaching moments, and students explore genuine education.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.image("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1650&q=80", use_container_width=True)
        
        st.markdown("""
        <div class="glass-box">
        <h3>🌟 Why Choose Brain App?</h3>
        <ul>
            <li>🧠 Focused learning, no distractions</li>
            <li>🏔 Calm, clean, and aesthetic environment</li>
            <li>🎥 Teachers post teaching statuses (daily)</li>
            <li>💰 Platform earns 20% from tuition income</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Predict Page
    elif mode == "📊 Predict":
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.subheader("🔮 Predict Your Performance")
        name = st.text_input("Enter your name:")
        hours = st.number_input("Study hours per day:", 0, 24, 6)
        focus = st.slider("Focus Level (0-10):", 0, 10, 7)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Predict Result 🌟"):
            result = (hours * focus) * 1.5
            st.success(f"{name}, your predicted success rate is **{min(result, 100):.1f}%**!")

    # Teachers Page
    elif mode == "👨‍🏫 Teachers":
        st.markdown("""
        <div class="glass-box">
        <h2>👩‍🏫 Become a Brain Teacher</h2>
        <p>Create your own tuition center in minutes. Set subjects, post your teaching demos, and start earning!</p>
        <ul>
            <li>🌍 Global reach</li>
            <li>💵 80% teacher revenue</li>
            <li>📈 Grow with our AI-powered tools</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Join Now 💼"):
            st.info("✅ Application received! We'll reach out soon.")

    # About Page
    elif mode == "🌍 About":
        st.markdown("""
        <div class="glass-box">
        <h2>🌄 About Brain App</h2>
        <p>Built with love in Python & Streamlit, Brain App is a next-generation learning platform merging clarity, design, and focus.  
        We help students and teachers grow — without distraction.</p>
        <br>
        <p>🌿 Designed to calm your mind and accelerate your growth.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
