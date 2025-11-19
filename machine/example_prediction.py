"""
Example: How to use the ML model for predictions

This script shows exactly what input format is required to get predictions from the model.
"""

import pandas as pd
import joblib

# Load the trained model
model = joblib.load('ml_model.joblib')

print("="*70)
print("HOW TO USE THE MODEL FOR PREDICTIONS")
print("="*70)

# ============================================================================
# REQUIRED INPUT FORMAT
# ============================================================================
print("\n1. REQUIRED FEATURES (in exact order):")
print("-" * 70)

required_features = [
    'endurance',                        # 0.0 - 1.0 (0 = low, 1 = high)
    'relaxation',                       # 0.0 - 1.0 (0 = low, 1 = high)
    'intensity',                        # 0.0 - 1.0 (0 = low, 1 = high)
    'setting_gruppe_fun',               # 0.0 or 1.0 (binary)
    'setting_gruppe_competitive',       # 0.0 or 1.0 (binary)
    'setting_gruppe_teamsport',         # 0.0 or 1.0 (binary)
    'setting_ort_indoor',               # 0.0 or 1.0 (binary)
    'setting_ort_outdoor',              # 0.0 or 1.0 (binary)
    'standort_campus_off_campus',       # 0.0 or 1.0 (binary)
    'standort_campus_on_campus'         # 0.0 or 1.0 (binary)
]

for i, feature in enumerate(required_features, 1):
    print(f"   {i:2d}. {feature}")

# ============================================================================
# EXAMPLE 1: Single Prediction
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 1: SINGLE PREDICTION")
print("="*70)

# Create input as a dictionary
user_input = {
    'endurance': 0.8,                   # High endurance activity
    'relaxation': 0.2,                  # Low relaxation
    'intensity': 0.9,                   # High intensity
    'setting_gruppe_fun': 0.0,          # Not fun-focused
    'setting_gruppe_competitive': 1.0,  # Competitive
    'setting_gruppe_teamsport': 0.0,    # Not a team sport
    'setting_ort_indoor': 1.0,          # Indoor
    'setting_ort_outdoor': 0.0,         # Not outdoor
    'standort_campus_off_campus': 0.0,  # Not off-campus
    'standort_campus_on_campus': 1.0    # On campus
}

# Convert to DataFrame (IMPORTANT: must be a DataFrame, not a dict)
X = pd.DataFrame([user_input])

print("\nInput values:")
for key, value in user_input.items():
    print(f"   {key:30s} = {value}")

# Make prediction
prediction = model.predict(X)[0]
print(f"\n✅ Predicted Sport: {prediction}")

# Get prediction probabilities
probabilities = model.predict_proba(X)[0]
top_5_indices = probabilities.argsort()[-5:][::-1]
top_5_probs = probabilities[top_5_indices]
top_5_classes = model.classes_[top_5_indices]

print("\nTop 5 Predictions:")
for i, (sport, prob) in enumerate(zip(top_5_classes, top_5_probs), 1):
    print(f"   {i}. {sport:45s} ({prob*100:5.1f}%)")

# ============================================================================
# EXAMPLE 2: Multiple Predictions at Once
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 2: MULTIPLE PREDICTIONS")
print("="*70)

# Create multiple inputs
multiple_inputs = [
    {
        'endurance': 0.3,
        'relaxation': 0.9,
        'intensity': 0.2,
        'setting_gruppe_fun': 1.0,
        'setting_gruppe_competitive': 0.0,
        'setting_gruppe_teamsport': 0.0,
        'setting_ort_indoor': 1.0,
        'setting_ort_outdoor': 0.0,
        'standort_campus_off_campus': 0.0,
        'standort_campus_on_campus': 1.0
    },
    {
        'endurance': 0.7,
        'relaxation': 0.1,
        'intensity': 0.8,
        'setting_gruppe_fun': 0.5,
        'setting_gruppe_competitive': 1.0,
        'setting_gruppe_teamsport': 1.0,
        'setting_ort_indoor': 0.0,
        'setting_ort_outdoor': 1.0,
        'standort_campus_off_campus': 0.5,
        'standort_campus_on_campus': 0.5
    }
]

# Convert to DataFrame
X_multiple = pd.DataFrame(multiple_inputs)

# Make predictions
predictions = model.predict(X_multiple)

print("\nPredictions for multiple inputs:")
for i, pred in enumerate(predictions, 1):
    print(f"   Input {i}: {pred}")

# ============================================================================
# EXAMPLE 3: Using Column Order (Alternative Method)
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 3: USING LIST/ARRAY INPUT")
print("="*70)

# You can also provide input as a list/array, but you MUST maintain the exact order
input_values = [
    0.6,    # endurance
    0.5,    # relaxation
    0.7,    # intensity
    1.0,    # setting_gruppe_fun
    0.0,    # setting_gruppe_competitive
    0.5,    # setting_gruppe_teamsport
    1.0,    # setting_ort_indoor
    0.0,    # setting_ort_outdoor
    0.0,    # standort_campus_off_campus
    1.0     # standort_campus_on_campus
]

# Create DataFrame with column names
X_array = pd.DataFrame([input_values], columns=required_features)

prediction = model.predict(X_array)[0]
print(f"\n✅ Predicted Sport: {prediction}")

# ============================================================================
# IMPORTANT NOTES
# ============================================================================
print("\n" + "="*70)
print("IMPORTANT NOTES")
print("="*70)
print("""
1. Input MUST be a pandas DataFrame, not a dictionary or list
2. All 10 features must be provided
3. Feature order must match the training data
4. Numeric values should be between 0.0 and 1.0
5. Binary features should be either 0.0 or 1.0
6. Missing values will be imputed by the model's preprocessor

Value Ranges:
- endurance, relaxation, intensity: 0.0 (low) to 1.0 (high)
- setting_gruppe_*: Binary flags (0.0 or 1.0)
- setting_ort_*: Binary flags (0.0 or 1.0)  
- standort_campus_*: Binary flags (0.0 or 1.0)
""")

print("="*70)
print("READY TO USE!")
print("="*70)
