import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

# ===== REAL WORLD DATA CREATION =====
def create_real_world_dataset():
    N = 500
    data = []
    for _ in range(N):
        hours = np.clip(np.random.normal(5.5, 2.5), 0.5, 10.0)
        distraction_count = int(np.clip(np.random.normal(6, 3.5), 0, 15))

        avoid_sugar = random.choice(['Yes', 'No'])
        avoid_junk_food = random.choice(['Yes', 'No'])
        drink_5L_water = random.choice(['Yes', 'No'])
        exercise_daily = random.choice(['Yes', 'No'])
        sleep_early = random.choice(['Yes', 'No'])
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


df = create_real_world_dataset()
categorical_columns = ["avoid_sugar", "avoid_junk_food", "drink_5L_water", "sleep_early", "exercise_daily", "wakeup_early"]
numeric_columns = ['hours', 'distraction_count']

# Encoding + scaling
encoders = {col: LabelEncoder().fit(df[col]) for col in categorical_columns}
for col, le in encoders.items():
    df[col] = le.transform(df[col])

scaler = StandardScaler()
df[numeric_columns] = scaler.fit_transform(df[numeric_columns])

X = df.drop(columns=['top_percentile'])
y = df['top_percentile']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=5, random_state=42)
model.fit(X_train, y_train)


def predict(inputs):
    inputs_df = pd.DataFrame([inputs])
    inputs_df[numeric_columns] = scaler.transform(inputs_df[numeric_columns])
    for col in categorical_columns:
        inputs_df[col] = encoders[col].transform(inputs_df[col])
    pred = model.predict(inputs_df)[0]
    return np.clip(pred, 1, 100)
