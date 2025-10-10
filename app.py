import streamlit as st

# =========================
# 🌈 CUSTOM STYLING
# =========================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    /* Full Background – Sharp, Not Blurred */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1508264165352-258859e62245?auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
        color: #002244;
    }

    /* Glass Containers (slightly transparent but crisp) */
    .glass-box {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 20px;
        padding: 30px 40px;
        box-shadow: 0 4px 30px rgba(0, 50, 150, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.4);
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
        text-shadow: 0 2px 10px rgba(255,255,255,0.7);
        letter-spacing: 0.8px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.85);
        border-right: 2px solid rgba(0, 100, 200, 0.2);
        backdrop-filter: none !important;
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
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #00C6FF, #007BFF);
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(0,0,0,0.3);
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput input {
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        color: #002244;
        border: 1px solid #B0E0FF;
        padding: 10px;
        font-weight: 500;
    }

    /* Text */
    p, li, span, label {
        color: #002244 !important;
        font-size: 16px !important;
    }

    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# =========================
# 🚀 MAIN APP
# =========================
def main():
    st.set_page_config(page_title="Brain App 🏔️", layout="wide")
    inject_css()

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=100)
        st.title("🧠 Brain App")
        st.markdown("**Your Focus Zone** ❄️")
        st.markdown("---")
        mode = st.radio("Navigate:", ["🏔 Home", "📊 Predict", "👨‍🏫 Teachers", "🌍 About"])

    # --- Home Page ---
    if mode == "🏔 Home":
        st.markdown("<h1>Welcome to The Brain App 🏔️</h1>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-box">
        <h2>❄️ Sharp Mind in a Calm World</h2>
        <p><b>Brain App</b> transforms your focus, discipline, and productivity through
        a clean, calm, white-ice environment.  
        Build your skills, track your growth, and evolve your mindset daily.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-box">
        <h3>🌟 Why People Love Brain App</h3>
        <ul>
            <li>🏔️ Crystal-clear white mountain visuals (no blur)</li>
            <li>🧠 Real skill-based challenges</li>
            <li>💡 Minimal and modern design</li>
            <li>📱 Fully mobile responsive</li>
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
        <p>Start your online tuition, share your expertise,
        and empower students worldwide with focused learning sessions.</p>
        <ul>
            <li>🌍 Reach global learners</li>
            <li>💵 Keep 80% of your income</li>
            <li>📈 Get analytics of student progress</li>
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
        <p><b>Brain App</b> is designed for dreamers and doers who want clarity,
        calmness, and success — all in one place.  
        Built with <b>Python + Streamlit</b>, it merges design, focus, and mindset
        to create the ultimate learning experience.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
