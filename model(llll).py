# model.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import random

# ===== REAL WORLD DATA CREATION =====
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

        score_noise = np.random.normal(0, 0.5 if score > 150 else 8)
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


# ===== TRAIN MODEL =====
df = create_real_world_dataset()
encoders = {}
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water",
                       "sleep_early", "exercise_daily", "wakeup_early"]

for col in categorical_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

numeric_columns = ['hours', 'distraction_count']
scaler = StandardScaler()
df_scaled = df.copy()
df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])

X = df_scaled.drop(columns=['top_percentile'])
y = df_scaled['top_percentile']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = XGBRegressor(n_estimators=1000, learning_rate=0.05, max_depth=5,
                     reg_lambda=1.0, subsample=0.8, colsample_bytree=0.8, random_state=42)
model.fit(X_train, y_train)

def predict(inputs):
    input_df = pd.DataFrame([inputs])
    input_df[numeric_columns] = scaler.transform(input_df[numeric_columns])
    input_df = input_df[X.columns]
    return max(1, min(100, model.predict(input_df)[0]))
