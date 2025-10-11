import streamlit as st
import matplotlib.pyplot as plt
from model import predict, categorical_columns
import pandas as pd

# ===== Streamlit Styling =====
st.set_page_config(page_title="Brain App - AI Learning", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-color: #e8f5ff;
            color: white;
            font-family: 'Poppins', sans-serif;
        }
        h1, h2, h3, h4 {
            color: white;
            text-shadow: 0px 0px 8px #00bfff;
        }
        .stButton button {
            background-color: #00ff9d;
            color: black;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ===== Sidebar Navigation =====
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📊 Dashboard", "ℹ️ About"])

# ===== HOME PAGE =====
if page == "🏠 Home":
    st.title("🧠 Brain App - AI Performance Predictor")
    st.subheader("Welcome to your AI-based Performance Analyzer!")

    st.write("""
    This tool uses a trained **XGBoost Machine Learning model** to predict your performance percentile 
    based on your habits, study hours, and distractions.
    """)

# ===== DASHBOARD =====
elif page == "📊 Dashboard":
    st.title("📊 Performance Predictor Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        hours = st.number_input("Study Hours per Day", 0.5, 12.0, 5.0)
        distractions = st.number_input("Distraction Count", 0, 15, 3)
    with col2:
        inputs = {}
        for col in categorical_columns:
            inputs[col] = st.selectbox(col.replace("_", " ").title(), ["Yes", "No"])
    
    inputs["hours"] = hours
    inputs["distraction_count"] = distractions

    if st.button("🔮 Predict My Performance"):
        percentile = predict(inputs)
        st.success(f"🎯 You are in the Top **{percentile:.1f}%** of performers!")

        # ===== Bar Chart =====
        st.subheader("Feature Breakdown")
        features = ["Study Hours", "Distraction Control", "Habits Impact"]
        values = [100 - percentile, percentile, (percentile + 20) % 100]

        fig, ax = plt.subplots()
        ax.bar(features, values, color="#00bfff", edgecolor="white")
        ax.set_title("Performance Breakdown", color="white", fontsize=14)
        ax.set_ylabel("Percentile", color="white")
        ax.tick_params(colors="white")
        st.pyplot(fig)

# ===== ABOUT PAGE =====
elif page == "ℹ️ About":
    st.title("ℹ️ About Brain App")
    st.write("""
    **Brain App** is an AI-driven platform that helps learners understand their performance patterns.  
    It uses **XGBoost Regression** and real-world simulated data to predict percentile ranking 
    based on behavioral habits and learning consistency.
    """)

    st.info("Made with 💙 by Syed Imran Shah (Future Tech Entrepreneur)")
