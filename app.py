import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from model import predict

# PAGE CONFIG
st.set_page_config(page_title="Brain Predictor", page_icon="🧠", layout="wide")

# ====== CUSTOM THEME ======
st.markdown("""
    <style>
    .stApp {
        background-color: #0B3D91;
        color: white;
    }
    .stButton>button {
        background-color: #00C851;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 16px;
        font-weight: bold;
    }
    .stSidebar {
        background-color: #062863;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ====== SIDEBAR NAVIGATION ======
st.sidebar.title("🧠 Brain Dashboard")
page = st.sidebar.radio("Navigation", ["🏠 Home", "📊 Predictor", "ℹ️ About"])

# ====== PAGE 1: HOME ======
if page == "🏠 Home":
    st.title("Welcome to Brain Predictor 🧠")
    st.markdown("""
        Predict your **learning performance percentile**  
        based on your **study habits and lifestyle choices**.
    """)
    st.image("https://images.unsplash.com/photo-1501785888041-af3ef285b470", use_container_width=True)
    st.info("Go to the **Predictor** tab to try it out!")

# ====== PAGE 2: PREDICTOR ======
elif page == "📊 Predictor":
    st.title("📊 Performance Predictor")

    # --- User Inputs ---
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("📘 Study Hours (per day)", 0.5, 12.0, 6.0)
        distraction_count = st.slider("📱 Daily Distractions", 0, 15, 5)
    with col2:
        avoid_sugar = st.selectbox("🍬 Avoid Sugar?", ["Yes", "No"])
        avoid_junk_food = st.selectbox("🍔 Avoid Junk Food?", ["Yes", "No"])
        drink_5L_water = st.selectbox("💧 Drink Enough Water?", ["Yes", "No"])
        sleep_early = st.selectbox("🌙 Sleep Early?", ["Yes", "No"])
        exercise_daily = st.selectbox("💪 Exercise Daily?", ["Yes", "No"])
        wakeup_early = st.selectbox("⏰ Wake Up Early?", ["Yes", "No"])

    if st.button("🔮 Predict My Performance"):
        inputs = {
            "hours": hours,
            "distraction_count": distraction_count,
            "avoid_sugar": avoid_sugar,
            "avoid_junk_food": avoid_junk_food,
            "drink_5L_water": drink_5L_water,
            "sleep_early": sleep_early,
            "exercise_daily": exercise_daily,
            "wakeup_early": wakeup_early
        }

        result = predict(inputs)
        st.success(f"🏆 Your Predicted Top Percentile: **{result:.1f}%**")

        # Visualization
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(["Your Performance"], [result], color="#00BFFF")
        ax.set_ylim(0, 100)
        ax.set_ylabel("Percentile")
        ax.set_title("Predicted Performance Level", fontsize=14, fontweight='bold')
        ax.bar_label(bars, labels=[f"Top {result:.1f} %"], label_type='edge', fontsize=10, color='white')
        ax.set_facecolor("#0B3D91")
        fig.patch.set_facecolor("#0B3D91")
        st.pyplot(fig)

# ====== PAGE 3: ABOUT ======
elif page == "ℹ️ About":
    st.title("ℹ️ About This App")
    st.markdown("""
    **Brain Predictor** uses a Machine Learning model (XGBoost)  
    to analyze how your habits affect your study performance percentile.

    **Technologies Used:**
    - 🧠 XGBoost  
    - 📘 Scikit-Learn  
    - 🧮 Numpy / Pandas  
    - 🎨 Streamlit

    **Created by:** Syed Imran Shah 🚀
    """)
