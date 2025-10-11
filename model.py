import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

def create_real_world_dataset():
    data = []
    for _ in range(500):
        hours = np.clip(np.random.normal(5.5, 2.5), 0.5, 10)
        distractions = int(np.clip(np.random.normal(6, 3.5), 0, 15))
        avoid_sugar = random.choice(['Yes', 'No'])
        avoid_junk_food = random.choice(['Yes', 'No'])
        drink_5L_water = random.choice(['Yes', 'No'])
        sleep_early = random.choice(['Yes', 'No'])
        exercise_daily = random.choice(['Yes', 'No'])
        wakeup_early = random.choice(['Yes', 'No'])
        score = (hours * 15) - (distractions * 7)
        score += 25 if avoid_sugar == 'Yes' else -10
        score += 20 if avoid_junk_food == 'Yes' else -5
        score += 15 if drink_5L_water == 'Yes' else -5
        score += 30 if sleep_early == 'Yes' else -15
        score += 15 if exercise_daily == 'Yes' else -5
        score += 10 if wakeup_early == 'Yes' else 0
        percentile = np.clip(100 - (score / 2.5), 1, 100)
        data.append({
            "hours": hours,
            "distraction_count": distractions,
            "avoid_sugar": avoid_sugar,
            "avoid_junk_food": avoid_junk_food,
            "drink_5L_water": drink_5L_water,
            "sleep_early": sleep_early,
            "exercise_daily": exercise_daily,
            "wakeup_early": wakeup_early,
            "top_percentile": percentile
        })
    return pd.DataFrame(data)

df = create_real_world_dataset()
categorical_columns = ["avoid_sugar","avoid_junk_food","drink_5L_water","sleep_early","exercise_daily","wakeup_early"]
numeric_columns = ["hours","distraction_count"]

encoders = {col: LabelEncoder().fit(df[col]) for col in categorical_columns}
for col, le in encoders.items():
    df[col] = le.transform(df[col])

scaler = StandardScaler()
df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
X = df.drop(columns=["top_percentile"])
y = df["top_percentile"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=5, random_state=42)
model.fit(X_train, y_train)

def predict(inputs):
    df_input = pd.DataFrame([inputs])
    df_input[numeric_columns] = scaler.transform(df_input[numeric_columns])
    for col in categorical_columns:
        df_input[col] = encoders[col].transform(df_input[col])
    return model.predict(df_input)[0]
