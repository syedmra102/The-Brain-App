import streamlit as st

# =========================
# 🌈 CUSTOM STYLING
# =========================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    /* Full Background - Sharp Mountain */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
        color: #f0f0f0;
    }

    /* Keep everything visible over background */
    .stApp > * {
        position: relative;
        z-index: 1;
    }

    /* Headings */
    h1, h2, h3 {
        color: #ffffff !important;
        text-align: center;
        text-shadow: 0 2px 10px rgba(0,0,0,0.4);
        letter-spacing: 1px;
    }

    /* Glass Containers (mild transparency) */
    .glass-box {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 30px 40px;
        backdrop-filter: blur(10px);
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
        background: rgba(20, 30, 40, 0.8);
        backdrop-filter: blur(10px);
    }
    section[data-testid="stSidebar"] * {
        color: #fff !important;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #0077ff, #00c6ff);
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
        background: linear-gradient(135deg, #00c6ff, #0077ff);
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(0,0,0,0.5);
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput input {
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        color: #000;
        border: none;
        padding: 10px;
        font-weight: 500;
    }

    /* Text */
    p, li, span, label {
        color: #ffffff !important;
        font-size: 16px !important;
    }

    /* Footer Hide */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =========================
# 🚀 MAIN APP
# =========================
def main():
    st.set_page_config(page_title="Brain App 🌄", layout="wide")
    inject_css()

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/10307/10307982.png", width=100)
        st.title("🧠 Brain App")
        st.markdown("**Your Focus Zone** ⛰️")
        st.markdown("---")
        mode = st.radio("Go to:", ["🏔 Home", "📊 Predict", "👨‍🏫 Teachers", "🌍 About"])

    # --- Home Page ---
    if mode == "🏔 Home":
        st.markdown("<h1>Welcome to The Brain App 🌄</h1>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-box">
        <h2>✨ The Calm Place to Learn</h2>
        <p><b>Brain App</b> brings together <b>YouTube + WhatsApp</b> into one calm, focused platform for learning.  
        Teachers can create their own tuition centers, upload daily teaching statuses,  
        and students can explore and learn — without distractions.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-box">
        <h3>🌟 Why Students Love Brain App</h3>
        <ul>
            <li>🧘‍♂️ Distraction-free learning</li>
            <li>🏔 Sharp, aesthetic mountain theme</li>
            <li>🎥 Real teacher content and insights</li>
            <li>💰 Teachers earn, students grow</li>
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
        <p>Open your own tuition center, share your real teaching journey,  
        and inspire learners around the world.</p>
        <ul>
            <li>🌍 Global reach</li>
            <li>💵 80% income share</li>
            <li>📈 AI-powered growth</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Join as Teacher 💼"):
            st.info("✅ Application submitted successfully!")

    # --- About Page ---
    elif mode == "🌍 About":
        st.markdown("""
        <div class="glass-box">
        <h2>🌄 About Brain App</h2>
        <p>Brain App is built for students and teachers who want peace, focus,  
        and productivity — without distraction.  
        Developed using <b>Python + Streamlit</b> with love and calm aesthetics.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
