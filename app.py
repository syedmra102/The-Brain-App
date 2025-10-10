import streamlit as st

# =========================
# 🌈 CUSTOM STYLING
# =========================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    /* Full Background - Blue/White Mountains */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
        color: #002244;
    }

    /* Glass Containers */
    .glass-box {
        background: rgba(255, 255, 255, 0.45);
        border-radius: 20px;
        padding: 30px 40px;
        backdrop-filter: blur(20px);
        box-shadow: 0 4px 30px rgba(0, 100, 200, 0.15);
        transition: all 0.3s ease;
        margin-bottom: 25px;
    }

    .glass-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 100, 200, 0.25);
    }

    /* Headings */
    h1, h2, h3 {
        color: #003366 !important;
        text-align: center;
        text-shadow: 0 2px 10px rgba(255,255,255,0.5);
        letter-spacing: 0.8px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(230, 245, 255, 0.9);
        backdrop-filter: blur(15px);
    }
    section[data-testid="stSidebar"] * {
        color: #003366 !important;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #007BFF, #00C6FF);
        border: none;
        color: white !important;
        border-radius: 15px;
        padding: 10px 30px;
        font-size: 17px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #00C6FF, #007BFF);
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(0,0,0,0.4);
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput input {
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        color: #002244;
        border: 1px solid #B0E0FF;
        padding: 10px;
        font-weight: 500;
    }

    /* Text */
    p, li, span, label {
        color: #003366 !important;
        font-size: 16px !important;
    }

    /* Hide footer */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =========================
# 🚀 MAIN APP
# =========================
def main():
    st.set_page_config(page_title="Brain App 🌨️", layout="wide")
    inject_css()

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=100)
        st.title("🧠 Brain App")
        st.markdown("**Your Focus Zone** ❄️")
        st.markdown("---")
        mode = st.radio("Go to:", ["🏔 Home", "📊 Predict", "👨‍🏫 Teachers", "🌍 About"])

    # --- Home Page ---
    if mode == "🏔 Home":
        st.markdown("<h1>Welcome to The Brain App 🌨️</h1>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-box">
        <h2>❄️ Calm Blue Productivity</h2>
        <p><b>Brain App</b> merges focus, technology, and clarity.  
        Learn from real teachers, explore daily insights,  
        and study in a peaceful blue-white environment that clears your mind.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-box">
        <h3>🌟 Why Students Love Brain App</h3>
        <ul>
            <li>🌤️ Peaceful white-blue aesthetic</li>
            <li>🧠 Real teacher-led content</li>
            <li>📱 Works perfectly on mobile</li>
            <li>💼 Teachers earn, students grow</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # --- Predict Page ---
    elif mode == "📊 Predict":
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.subheader("🔮 Predict Your Success Rate")
        name = st.text_input("Enter your name:")
        hours = st.number_input("Study hours per day:", 0, 24, 6)
        focus = st.slider("Focus level (0–10):", 0, 10, 7)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Predict 🌟"):
            result = (hours * focus) * 1.5
            st.success(f"{name}, your predicted success rate is **{min(result, 100):.1f}%**!")

    # --- Teachers Page ---
    elif mode == "👨‍🏫 Teachers":
        st.markdown("""
        <div class="glass-box">
        <h2>👩‍🏫 Become a Brain Teacher</h2>
        <p>Start your own online tuition center, share your knowledge,  
        and earn through your expertise while helping students globally.</p>
        <ul>
            <li>🌍 Global reach</li>
            <li>💵 80% income share</li>
            <li>📈 AI-powered analytics</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Join as Teacher 💼"):
            st.info("✅ Application submitted successfully!")

    # --- About Page ---
    elif mode == "🌍 About":
        st.markdown("""
        <div class="glass-box">
        <h2>🌨️ About Brain App</h2>
        <p>Brain App is designed to create a <b>peaceful learning experience</b>.  
        Built using <b>Python + Streamlit</b>, it combines technology and focus  
        with a calm blue-white environment that enhances productivity.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
