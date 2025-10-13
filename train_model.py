# train_model.py - Run this once to create model.pkl
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random

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
            score_noise = np.random.normal(loc=0, scale=0.5)
        else:
            score_noise = np.random.normal(loc=0, scale=8)

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

# Generate data
df = create_real_world_dataset()

# Label Encoding
encoders = {}
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water", "sleep_early", "exercise_daily", "wakeup_early"]

for col in categorical_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

# Feature Scaling
numeric_columns = ['hours', 'distraction_count']
scaler = StandardScaler()
df_scaled = df.copy()
df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])

# Prepare features and target
X = df_scaled.drop(columns=['top_percentile'])
y = df_scaled['top_percentile']

# Train model
model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    reg_lambda=1.0,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X, y)

# Save everything to pickle file
model_data = {
    'model': model,
    'encoders': encoders,
    'scaler': scaler,
    'df': df,
    'categorical_columns': categorical_columns,
    'numeric_columns': numeric_columns,
    'feature_columns': X.columns.tolist()
}

with open('model.pkl', 'wb') as f:
    pickle.dump(model_data, f)

print("Model saved as model.pkl successfully!")
print(f"Model R2 Score: {model.score(X, y):.4f}")
