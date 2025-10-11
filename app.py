# ===== IMPORTS =====
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random
import streamlit as st

# ===== STREAMLIT PAGE CONFIG =====
st.set_page_config(
    page_title="Performance Predictor",
    page_icon="📊",
    layout="centered",
)

# ===== CUSTOM CSS =====
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E90FF;  /* Blue background */
        color: white;
    }
    .stButton>button {
        background-color: #00FF00; /* Green buttons */
        color: white;
        font-weight: bold;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===== REAL WORLD DATA COLLECTION =====
def create_real_world_dataset():
    N = 500
    data = []
    for _ in range(N):
        hours = np.clip(np.random.normal(loc=5.5, scale=2.5), 0.5, 10.0)
        distraction_count = int(np.clip(np.random.normal(loc=6, scale=3.5), 0, 15))
        avoid_sugar = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
        avoid_junk_food = random.choices(['Yes', 'No'], weights=[0.45, 0.55])[0]
        drink_5L_water = random.choices(['Yes', 'No'], weights=[0.35, 0.65])[0]
        exercise_daily = random.choices(['Yes', 'No'], weights=[0.5, 0.5])[0]
        sleep_early = random.choices(['Yes', 'No'], weights=[0.4, 0.6])[0]
        wakeup_early = 'Yes' if sleep_early == 'Yes' and random.random() < 0.7 else 'No'

        score = (hours * 15) - (distraction_count * 7)
        score += 25 if avoid_sugar == 'Yes' else -10
        score += 20 if avoid_junk_food == 'Yes' else -5
        score += 15 if drink_5L_water == 'Yes' else -5
        score += 30 if sleep_early == 'Yes' else -15
        score += 15 if exercise_daily == 'Yes' else -5
        score += 10 if wakeup_early == 'Yes' else 0

        if score > 150:
            score_noise = np.random.normal(0, 0.5)
        else:
            score_noise = np.random.normal(0, 8)

        final_score = score + score_noise
        percentile = np.clip(100 - (final_score / 2.5), 1.0, 99.9)

        data.append({
            "hours": round(hours, 1),
            "avoid_sugar": avoid_sugar,
            "avoid_junk_food": avoid_junk_food,
            "drink_5L_water": drink_5L_water,
            "sleep_early": sleep_early,
            "exercise_daily": exercise_daily,
            "wakeup_early": wakeup_early,
            "distraction_count": distraction_count,
            "top_percentile": round(percentile, 1)
        })
    
    return pd.DataFrame(data)

# ===== DATASET =====
df = create_real_world_dataset()

# ===== LABEL ENCODING =====
encoders = {}
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water",
                       "sleep_early", "exercise_daily", "wakeup_early"]
for col in categorical_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

# ===== FEATURE SCALING =====
numeric_columns = ['hours', 'distraction_count']
scaler = StandardScaler()
df_scaled = df.copy()
df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])

X = df_scaled.drop(columns=['top_percentile'])
y = df_scaled['top_percentile']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ===== MODEL TRAINING =====
model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    reg_lambda=1.0,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X_train, y_train)

# ===== STREAMLIT INTERACTIVE INPUTS =====
st.title("📊 Performance Predictor Dashboard")

st.subheader("Enter your details:")

hours = st.number_input("Daily Study Hours (0.5 - 12)", min_value=0.5, max_value=12.0, value=5.5)
distractions = st.number_input("Number of Distractions (0 - 15)", min_value=0, max_value=15, value=5)

habit_inputs = {}
for col in categorical_columns:
    friendly_name = col.replace('_', ' ').title()
    habit_inputs[col] = st.selectbox(f"{friendly_name}", ["Yes", "No"])

# ===== PREDICTION =====
if st.button("Predict Performance"):
    input_data = pd.DataFrame([{
        'hours': hours,
        'distraction_count': distractions,
        **{col: encoders[col].transform([val])[0] for col, val in habit_inputs.items()}
    }])
    input_data[numeric_columns] = scaler.transform(input_data[numeric_columns])
    input_data = input_data[X.columns]
    prediction = model.predict(input_data)[0]
    prediction = max(1, min(100, prediction))

    st.success(f"🎯 Your Overall Performance: Top {prediction:.1f}%")

    # ===== FEATURE BREAKDOWN CHART =====
    feature_percentiles = {}
    hours_percentile = (df['hours'] <= hours).mean() * 100
    feature_percentiles['Study Hours'] = max(1, 100 - hours_percentile)
    dist_percentile = (df['distraction_count'] >= distractions).mean() * 100
    feature_percentiles['Distraction Control'] = max(1, 100 - dist_percentile)
    
    habit_mapping = {
        'avoid_sugar': 'Sugar Avoidance',
        'avoid_junk_food': 'Junk Food Avoidance', 
        'drink_5L_water': 'Water Intake',
        'sleep_early': 'Sleep Schedule',
        'exercise_daily': 'Exercise Routine',
        'wakeup_early': 'Wake-up Time'
    }
    for col, friendly_name in habit_mapping.items():
        val = encoders[col].transform([habit_inputs[col]])[0]
        if val == 1:
            habit_percentile = (df[col] == 1).mean() * 100
            feature_percentiles[friendly_name] = max(1, 100 - habit_percentile)
        else:
            habit_percentile = (df[col] == 0).mean() * 100
            feature_percentiles[friendly_name] = max(1, habit_percentile)

    # Plot chart
    plt.figure(figsize=(12, 8))
    features = list(feature_percentiles.keys())
    percentiles = list(feature_percentiles.values())
    bars = plt.bar(features, percentiles, color='blue', edgecolor='darkblue')
    plt.bar_label(bars, labels=[f'Top {p:.1f}%' for p in percentiles], label_type='edge', padding=2, fontweight='bold', fontsize=8, color='white')
    plt.xlabel('Performance Features', fontweight='bold', fontsize=12)
    plt.title(f'PERFORMANCE BREAKDOWN ANALYSIS (Top {prediction:.1f}%)', fontweight='bold', fontsize=14)
    plt.ylabel('Performance Percentile', fontweight='bold', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 100)
    st.pyplot(plt)
