import streamlit as st
import pandas as pd
import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@st.cache_resource
def load_ml_model():
    """Load the trained ML model (cached)"""
    try:
        # Try multiple paths for compatibility
        possible_paths = [
            Path(__file__).parent.parent / "machine" / "ml_model.joblib",
            Path("machine/ml_model.joblib"),
            Path("./machine/ml_model.joblib"),
            Path(__file__).resolve().parent.parent / "machine" / "ml_model.joblib"
        ]
        
        model = None
        for model_path in possible_paths:
            if model_path.exists():
                model = joblib.load(model_path)
                logger.info(f"ML model loaded successfully from {model_path}")
                return model
        
        # If no path worked, raise error
        raise FileNotFoundError(f"Could not find ml_model.joblib in any of: {[str(p) for p in possible_paths]}")
        
    except Exception as e:
        logger.error(f"Error loading ML model: {e}")
        st.error(f"Failed to load ML model: {e}")
        return None

def get_sport_recommendations(user_preferences: dict, top_n: int = 10):
    """
    Get sport recommendations based on user preferences
    
    Args:
        user_preferences: Dictionary with 13 features (correct names from training)
        top_n: Number of recommendations to return
    
    Returns:
        List of dicts: [{'sport': name, 'confidence': score}, ...]
    """
    model = load_ml_model()
    if model is None:
        return []
    
    try:
        # Correct feature order from training
        feature_order = [
            'balance', 'flexibility', 'coordination', 'relaxation', 
            'strength', 'endurance', 'longevity', 'intensity',
            'setting_team', 'setting_fun', 'setting_duo',
            'setting_solo', 'setting_competitive'
        ]
        
        # Create DataFrame with correct feature order
        X = pd.DataFrame([user_preferences])[feature_order]
        
        # Get predictions
        probabilities = model.predict_proba(X)[0]
        
        # Get top N predictions
        top_indices = probabilities.argsort()[-top_n:][::-1]
        
        recommendations = []
        for idx in top_indices:
            sport = model.classes_[idx]
            confidence = probabilities[idx] * 100
            recommendations.append({
                'sport': sport,
                'confidence': confidence
            })
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        st.error(f"Error getting recommendations: {e}")
        return []

def validate_user_preferences(preferences: dict) -> bool:
    """Validate that all required features are present"""
    required_features = [
        'balance', 'flexibility', 'coordination', 'relaxation', 
        'strength', 'endurance', 'longevity', 'intensity',
        'setting_team', 'setting_fun', 'setting_duo',
        'setting_solo', 'setting_competitive'
    ]
    
    for feature in required_features:
        if feature not in preferences:
            logger.warning(f"Missing feature: {feature}")
            return False
        if not isinstance(preferences[feature], (int, float)):
            logger.warning(f"Invalid type for {feature}: {type(preferences[feature])}")
            return False
        if not (0 <= preferences[feature] <= 1):
            logger.warning(f"Value out of range for {feature}: {preferences[feature]}")
            return False
    
    return True

def get_recommendations_from_sidebar():
    """
    Generate ML recommendations using existing sidebar filters.
    Maps the current sidebar filter state to ML model features.
    """
    from data.state_manager import get_filter_state
    
    # Get current sidebar filter values
    intensity = get_filter_state('intensity', [])
    focus = get_filter_state('focus', [])
    setting = get_filter_state('setting', [])
    
    # DEBUG: Show what we got from sidebar
    st.write("🔍 **Debug - Sidebar Filters:**")
    st.write(f"- Intensity: {intensity}")
    st.write(f"- Focus: {focus}")
    st.write(f"- Setting: {setting}")
    
    # Map to ML features (13 required features with CORRECT names)
    user_prefs = {
        # Fitness goals (0-1 scale based on focus filter)
        'balance': 1.0 if any('balance' in str(f).lower() for f in focus) else 0.3,
        'flexibility': 1.0 if any('flexibility' in str(f).lower() or 'flexibilität' in str(f).lower() for f in focus) else 0.3,
        'coordination': 1.0 if any('coordination' in str(f).lower() or 'koordination' in str(f).lower() for f in focus) else 0.3,
        'relaxation': 1.0 if any('relaxation' in str(f).lower() or 'entspannung' in str(f).lower() for f in focus) or any('low' in str(i).lower() for i in intensity) else 0.3,
        'strength': 1.0 if any('strength' in str(f).lower() or 'kraft' in str(f).lower() for f in focus) else 0.3,
        'endurance': 1.0 if any('endurance' in str(f).lower() or 'ausdauer' in str(f).lower() for f in focus) else 0.3,
        'longevity': 0.5,  # Default value
        
        # Intensity (based on intensity filter)
        'intensity': 0.8 if any('high' in str(i).lower() or 'hoch' in str(i).lower() for i in intensity) else (0.5 if any('medium' in str(i).lower() or 'mittel' in str(i).lower() for i in intensity) else 0.2),
        
        # Settings (NO _gruppe prefix!)
        'setting_team': 1.0 if any('team' in str(s).lower() for s in setting) else 0.0,
        'setting_fun': 0.5,  # Default value
        'setting_duo': 0.0,  # Not in current filters
        'setting_solo': 1.0 if any('solo' in str(s).lower() for s in setting) else 0.0,
        'setting_competitive': 1.0 if any('competitive' in str(s).lower() or 'wettkampf' in str(s).lower() for s in setting) else 0.5,
    }
    
    # DEBUG: Show ML input
    st.write("🤖 **Debug - ML Input (active features):**")
    for key, value in user_prefs.items():
        if value > 0.3:  # Show non-default values
            st.write(f"- {key}: {value}")
    
    # Validate and get recommendations
    if validate_user_preferences(user_prefs):
        recommendations = get_sport_recommendations(user_prefs, top_n=10)
        
        # DEBUG: Show top recommendations
        if recommendations:
            st.write("📊 **Debug - Top 3 Recommendations:**")
            for i, rec in enumerate(recommendations[:3], 1):
                st.write(f"{i}. {rec['sport']} ({rec['confidence']:.1f}%)")
        
        return recommendations
    else:
        st.error("❌ Invalid preferences - check debug output above")
        return []
