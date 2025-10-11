import streamlit as st
import matplotlib.pyplot as plt
from model import predict

st.set_page_config(page_title="Brain App", page_icon="🧠", layout="wide")

# === CUSTOM THEME ===
st.markdown("""
<style>
    .stApp {
        background-color: #0b3d91;
        color: white;
    }
    .stButton>button {
        background-color: #28a745;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 16px;
    }
    .stSidebar {
        background-color: #062863;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🧠 Brain App Dashboard")
page = st.sidebar.radio("Navigation", ["🏠 Home", "📊 Dashboard", "ℹ️ About"])

if page == "🏠 Home":
    st.title("Welcome to Brain App")
    st.write("✨ Predict your **learning performance percentile** based on your habits.")
    st.image("https://images.unsplash.com/photo-1616401784845-180882ba9b1b", use_container_width=True)
    st.write("---")
    st.write("Navigate to the **Dashboard** to use the AI predictor.")

elif page == "📊 Dashboard":
    st.title("📊 Performance Predictor")
    st.write("Fill in the details below:")

    hours = st.slider("📘 Study Hours (per day)", 0.5, 12.0, 6.0)
    distraction_count = st.slider("📱 Distractions per day", 0, 15, 5)

    habits = {}
    for habit in ["avoid_sugar", "avoid_junk_food", "drink_5L_water", "sleep_early", "exercise_daily", "wakeup_early"]:
        habits[habit] = st.selectbox(f"{habit.replace('_', ' ').title()}", ["Yes", "No"])

    if st.button("🔮 Predict Performance"):
        inputs = {"hours": hours, "distraction_count": distraction_count, **habits}
        result = predict(inputs)
        st.success(f"🏆 Your Predicted Top Percentile: **{result:.1f}%**")

        # Simple bar chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(["Overall"], [result], color="#00BFFF")
        ax.set_ylim(0, 100)
        ax.set_ylabel("Top Percentile")
        ax.set_title("Performance Prediction")
        st.pyplot(fig)

elif page == "ℹ️ About":
    st.title("ℹ️ About Brain App")
    st.write("""
    This app uses **Machine Learning (XGBoost)** to predict your learning percentile 
    based on daily habits and study patterns.
    
    🧩 Built with:
    - Streamlit
    - XGBoost
    - Scikit-Learn  
    - Matplotlib
    """)

