"""
Test script for the ML model
Tests the saved model with various scenarios and provides detailed evaluation metrics
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
import os

# Model path
MODEL_PATH = 'ml_model.joblib'

# Feature columns (must match training)
FEATURED_COLUMNS = [
    'endurance', 
    'relaxation',
    'intensity',
    'setting_gruppe_fun', 
    'setting_gruppe_competitive',
    'setting_gruppe_teamsport',
    'setting_ort_indoor',
    'setting_ort_outdoor',
    'standort_campus_off_campus',
    'standort_campus_on_campus'
]


def load_model():
    """Load the trained model"""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        return None
    
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✅ Model loaded successfully from {MODEL_PATH}")
        return model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None


def create_test_samples():
    """Create synthetic test samples for different sport types"""
    test_samples = []
    
    # Sample 1: High endurance outdoor running
    test_samples.append({
        'name': 'Outdoor Running',
        'features': {
            'endurance': 0.9,
            'relaxation': 0.2,
            'intensity': 0.8,
            'setting_gruppe_fun': 0.0,
            'setting_gruppe_competitive': 0.5,
            'setting_gruppe_teamsport': 0.0,
            'setting_ort_indoor': 0.0,
            'setting_ort_outdoor': 1.0,
            'standort_campus_off_campus': 0.5,
            'standort_campus_on_campus': 0.5
        }
    })
    
    # Sample 2: Relaxation yoga indoor
    test_samples.append({
        'name': 'Yoga',
        'features': {
            'endurance': 0.3,
            'relaxation': 0.9,
            'intensity': 0.3,
            'setting_gruppe_fun': 0.5,
            'setting_gruppe_competitive': 0.0,
            'setting_gruppe_teamsport': 0.0,
            'setting_ort_indoor': 1.0,
            'setting_ort_outdoor': 0.0,
            'standort_campus_off_campus': 0.0,
            'standort_campus_on_campus': 1.0
        }
    })
    
    # Sample 3: Team sport competitive
    test_samples.append({
        'name': 'Football/Soccer',
        'features': {
            'endurance': 0.7,
            'relaxation': 0.1,
            'intensity': 0.7,
            'setting_gruppe_fun': 0.5,
            'setting_gruppe_competitive': 0.8,
            'setting_gruppe_teamsport': 1.0,
            'setting_ort_indoor': 0.0,
            'setting_ort_outdoor': 1.0,
            'standort_campus_off_campus': 0.3,
            'standort_campus_on_campus': 0.7
        }
    })
    
    # Sample 4: Indoor gym training
    test_samples.append({
        'name': 'Gym Training',
        'features': {
            'endurance': 0.5,
            'relaxation': 0.2,
            'intensity': 0.8,
            'setting_gruppe_fun': 0.3,
            'setting_gruppe_competitive': 0.5,
            'setting_gruppe_teamsport': 0.0,
            'setting_ort_indoor': 1.0,
            'setting_ort_outdoor': 0.0,
            'standort_campus_off_campus': 0.0,
            'standort_campus_on_campus': 1.0
        }
    })
    
    # Sample 5: Fun group activity
    test_samples.append({
        'name': 'Dance Class',
        'features': {
            'endurance': 0.6,
            'relaxation': 0.4,
            'intensity': 0.6,
            'setting_gruppe_fun': 1.0,
            'setting_gruppe_competitive': 0.0,
            'setting_gruppe_teamsport': 0.5,
            'setting_ort_indoor': 1.0,
            'setting_ort_outdoor': 0.0,
            'standort_campus_off_campus': 0.5,
            'standort_campus_on_campus': 0.5
        }
    })
    
    return test_samples


def predict_samples(model, test_samples):
    """Make predictions on test samples"""
    print("\n" + "="*70)
    print("INDIVIDUAL SAMPLE PREDICTIONS")
    print("="*70)
    
    for sample in test_samples:
        # Create DataFrame with correct column order
        X = pd.DataFrame([sample['features']])[FEATURED_COLUMNS]
        
        # Make prediction
        prediction = model.predict(X)[0]
        
        # Get prediction probabilities if available
        try:
            probabilities = model.predict_proba(X)[0]
            # Get top 3 predictions
            top_indices = np.argsort(probabilities)[-3:][::-1]
            top_probs = probabilities[top_indices]
            top_classes = model.classes_[top_indices]
            
            print(f"\n📊 {sample['name']}")
            print(f"   Primary Prediction: {prediction}")
            print(f"   Top 3 predictions:")
            for cls, prob in zip(top_classes, top_probs):
                print(f"      - {cls}: {prob*100:.1f}%")
        except:
            print(f"\n📊 {sample['name']}")
            print(f"   Prediction: {prediction}")


def test_with_data_file():
    """Test with actual data file if available"""
    data_file = 'Sportangebot_ML_ready.xlsx'
    
    if not os.path.exists(data_file):
        print(f"\n⚠️  Data file not found: {data_file}")
        print("   Skipping evaluation on real data.")
        return None
    
    try:
        print(f"\n{'='*70}")
        print("EVALUATION ON ACTUAL DATA")
        print("="*70)
        
        # Load data
        data = pd.read_excel(data_file)
        print(f"✅ Loaded data: {data.shape[0]} samples, {data.shape[1]} features")
        
        # Check if target column exists
        if 'Angebot' not in data.columns:
            print("❌ Target column 'Angebot' not found in data")
            return None
        
        # Check if all feature columns exist
        missing_cols = [col for col in FEATURED_COLUMNS if col not in data.columns]
        if missing_cols:
            print(f"❌ Missing feature columns: {missing_cols}")
            return None
        
        # Prepare data
        X = data[FEATURED_COLUMNS].copy()
        y = data['Angebot'].copy()
        
        # Load model
        model = load_model()
        if model is None:
            return None
        
        # Make predictions
        y_pred = model.predict(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        
        print(f"\n📈 Overall Accuracy: {accuracy*100:.2f}%")
        
        # Try to calculate additional metrics
        try:
            f1 = f1_score(y, y_pred, average='weighted')
            precision = precision_score(y, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y, y_pred, average='weighted', zero_division=0)
            
            print(f"   F1 Score (weighted): {f1*100:.2f}%")
            print(f"   Precision (weighted): {precision*100:.2f}%")
            print(f"   Recall (weighted): {recall*100:.2f}%")
        except:
            pass
        
        # Classification report
        print(f"\n📋 Detailed Classification Report:")
        print("-" * 70)
        report = classification_report(y, y_pred, zero_division=0)
        print(report)
        
        # Show some example predictions vs actual
        print(f"\n🔍 Sample Predictions vs Actual (first 10):")
        print("-" * 70)
        for i in range(min(10, len(y))):
            match = "✓" if y.iloc[i] == y_pred[i] else "✗"
            print(f"   {match} Actual: {y.iloc[i]:30s} | Predicted: {y_pred[i]}")
        
        return {
            'accuracy': accuracy,
            'predictions': y_pred,
            'actual': y
        }
        
    except Exception as e:
        print(f"❌ Error testing with data file: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function"""
    print("="*70)
    print("ML MODEL TESTING")
    print("="*70)
    
    # Load model
    model = load_model()
    if model is None:
        return
    
    # Display model info
    print(f"\n📦 Model Type: {type(model).__name__}")
    try:
        if hasattr(model, 'named_steps'):
            print(f"   Pipeline Steps: {list(model.named_steps.keys())}")
        if hasattr(model, 'classes_'):
            print(f"   Number of Classes: {len(model.classes_)}")
            print(f"   Classes: {list(model.classes_)[:10]}...")  # Show first 10
    except:
        pass
    
    # Test with synthetic samples
    test_samples = create_test_samples()
    predict_samples(model, test_samples)
    
    # Test with actual data if available
    test_with_data_file()
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
