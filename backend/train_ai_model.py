# train_ai_model.py
import numpy as np
import xgboost as xgb
import joblib

N = 5000
distances = np.random.uniform(0.1, 20, N)
relative_speed = np.random.uniform(0, 8, N)
size_sat = np.random.uniform(5, 20, N)
size_debris = np.random.uniform(0.1, 5, N)
history = np.random.randint(0, 10, N)
tle_noise = np.random.uniform(0, 1, N)

risk = (20-distances)*3 + relative_speed*5 + size_debris*4 + history*2 + tle_noise*10
risk_score = np.clip(risk/np.max(risk)*100,0,100)
risk_class = (risk_score>70).astype(int)

X = np.column_stack([distances, relative_speed, size_sat, size_debris, history, tle_noise])
y = risk_class

model = xgb.XGBClassifier(max_depth=3, n_estimators=20, learning_rate=0.1)
model.fit(X,y)

joblib.dump(model, "collision_ai_model.pkl")
print("AI Model Saved!")
