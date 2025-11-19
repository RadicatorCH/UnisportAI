"""
QUICK START: Making Predictions with the Model
================================================

Copy and run this minimal example to get started quickly!
"""

import pandas as pd
import joblib

# Step 1: Load the model
model = joblib.load('ml_model.joblib')

# Step 2: Prepare your input (10 features required)
your_input = {
    'endurance': 0.7,                   # How much endurance? (0.0 = low, 1.0 = high)
    'relaxation': 0.3,                  # How relaxing? (0.0 = not relaxing, 1.0 = very relaxing)
    'intensity': 0.8,                   # How intense? (0.0 = low, 1.0 = high)
    'setting_gruppe_fun': 1.0,          # Is it for fun? (0.0 = no, 1.0 = yes)
    'setting_gruppe_competitive': 0.5,  # Is it competitive? (0.0 = no, 1.0 = yes)
    'setting_gruppe_teamsport': 1.0,    # Is it a team sport? (0.0 = no, 1.0 = yes)
    'setting_ort_indoor': 0.0,          # Is it indoors? (0.0 = no, 1.0 = yes)
    'setting_ort_outdoor': 1.0,         # Is it outdoors? (0.0 = no, 1.0 = yes)
    'standort_campus_off_campus': 0.5,  # Off campus? (0.0 = no, 1.0 = yes)
    'standort_campus_on_campus': 0.5    # On campus? (0.0 = no, 1.0 = yes)
}

# Step 3: Convert to DataFrame (REQUIRED!)
X = pd.DataFrame([your_input])

# Step 4: Get prediction
prediction = model.predict(X)[0]

print(f"Predicted Sport: {prediction}")

# Optional: Get top 3 recommendations with confidence scores
probabilities = model.predict_proba(X)[0]
top_3_idx = probabilities.argsort()[-3:][::-1]

print("\nTop 3 Recommendations:")
for i, idx in enumerate(top_3_idx, 1):
    sport = model.classes_[idx]
    confidence = probabilities[idx] * 100
    print(f"{i}. {sport} ({confidence:.1f}%)")
