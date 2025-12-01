"""
================================================================================
UNISPORTAI STREAMLIT APPLICATION
================================================================================

PURPOSE:
This is a simplified, heavily documented version of the UnisportAI application,
designed as a clear reference implementation for a university project setting.

WHAT THIS APP DOES:
- Displays sports courses and activities from Unisport HSG
- Allows filtering and searching through activities
- Provides AI-powered recommendations using Machine Learning
- Enables user authentication and social features
- Shows course dates, ratings, and user profiles

CONCEPTS DEMONSTRATED:
1. Page configuration and layout
2. Session state management
3. Multi-tab navigation
4. Sidebar filters and widgets
5. Database integration (Supabase)
6. Caching strategies (@st.cache_resource, @st.cache_data)
7. User authentication
8. Interactive visualizations (Plotly)

HOW TO READ THIS FILE:
- Use the comments to understand WHY each pattern is used
- Follow the data flow from database client to UI components
- Observe how session state and caching keep the UI responsive

ORIGINAL FILE: streamlit_app.py
THIS VERSION: Structured and commented for clarity in an academic project
================================================================================
"""

# =============================================================================
# PART 1: IMPORTS & CONFIGURATION
# =============================================================================
# PURPOSE: Import necessary libraries and configure the Streamlit app

# Core Streamlit library - the foundation of our app
import streamlit as st

# Plotly for interactive charts and visualizations
import plotly.graph_objects as go

# joblib for loading saved machine learning models
import joblib

# numpy for numerical operations (used in ML)
import numpy as np

# Path for file system operations
from pathlib import Path

# datetime for handling dates and times
from datetime import datetime, time

# Type hints for better code documentation
from typing import Optional, List, Dict, Any

# scikit-learn components for machine learning
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# Timezone handling for correct time display
from zoneinfo import ZoneInfo

# Our custom authentication functions
from auth import (
    is_logged_in, 
    sync_user_to_supabase, 
    check_token_expiry, 
    handle_logout,
    get_user_sub
)

# Database connection and query functions
from db import get_supabase_client

# =============================================================================
# DATABASE CONNECTION HELPER
# =============================================================================
# PURPOSE: Test database connection and provide helpful error messages
# PATTERN: Handle external service dependencies explicitly and early

def test_database_connection():
    """
    Test if Supabase database connection is available.
    
    PURPOSE:
        Provide clear feedback about database status and fail fast when
        required configuration is missing.
    PATTERN:
        Validate external services before using them in the main UI flow.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        client = get_supabase_client()
        # Try a simple query to verify connection works
        client.table("etl_runs").select("ran_at").limit(1).execute()
        return True, "✅ Database connection successful"
    except Exception as e:
        error_msg = str(e)
        if "URL not provided" in error_msg or "key not provided" in error_msg:
            return False, """
❌ **Supabase credentials missing**

This application needs database credentials to work correctly.

**How to fix this:**
1. Create/check `.streamlit/secrets.toml` in your project root
2. Add your Supabase credentials:
   
   [connections.supabase]
   url = "your-supabase-url"
   key = "your-supabase-key"

3. Restart the Streamlit app

Design note: configuring external services explicitly avoids hard-to-debug
runtime errors later in the request flow.
"""
        else:
            return False, f"❌ **Database connection failed:** {error_msg}"

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
# PURPOSE: Set up the app's basic appearance and behavior
# IMPORTANT: This MUST be the first Streamlit command in your script
# COMMON MISTAKE: Calling st.write() before st.set_page_config() causes errors

st.set_page_config(
    page_title="UnisportAI",           # Browser tab title
    page_icon="🎯",                     # Browser tab icon (emoji or image URL)
    layout="wide",                      # "wide" uses full screen width, "centered" is narrower
    initial_sidebar_state="expanded"    # Sidebar visible by default
)

# =============================================================================
# PART 2: ML INTEGRATION COMPONENTS (UNCHANGED FROM ORIGINAL)
# =============================================================================
# PURPOSE: Machine Learning recommendation system using K-Nearest Neighbors
# ADVANCED TOPIC: This section uses scikit-learn for AI-powered recommendations
# FOR BEGINNERS: You don't need to understand every detail here yet
# KEY CONCEPT: We load a pre-trained model and use it to find similar sports

# Feature order (13 features)
ML_FEATURE_COLUMNS = [
    'balance', 'flexibility', 'coordination', 'relaxation',
    'strength', 'endurance', 'longevity',
    'intensity',
    'setting_team', 'setting_fun', 'setting_duo',
    'setting_solo', 'setting_competitive'
]

ML_MODEL_PATH = Path(__file__).resolve().parent / "ml" / "models" / "knn_recommender.joblib"

@st.cache_resource
def load_knn_model():
    """Load the trained KNN model with caching.
    
    Uses @st.cache_resource to load the model once and reuse it across all
    sessions and reruns. ML models (NearestNeighbors, StandardScaler) are
    unserializable objects that should be cached with cache_resource.
    
    Returns:
        dict: Model artifacts (knn_model, scaler, sports_df) or None if not found
    """
    if not ML_MODEL_PATH.exists():
        st.warning(f"⚠️ KNN model not found at {ML_MODEL_PATH}. Run train.py first.")
        return None
    
    try:
        data = joblib.load(ML_MODEL_PATH)
        return {
            'knn_model': data['knn_model'],
            'scaler': data['scaler'],
            'sports_df': data['sports_df']
        }
    except Exception as e:
        st.error(f"Error loading KNN model: {e}")
        return None

def build_user_preferences_from_filters(selected_focus, selected_intensity, selected_setting):
    """
    Build user preference vector from sidebar filter selections
    
    Args:
        selected_focus: List of selected focus values (e.g., ['strength', 'endurance'])
        selected_intensity: List of selected intensity values (e.g., ['high'])
        selected_setting: List of selected setting values (e.g., ['solo'])
    
    Returns:
        Dict with 13 feature values (0.0 or 1.0)
    """
    preferences = {}
    
    # Normalize inputs to lowercase for matching
    focus_lower = [f.lower() for f in selected_focus] if selected_focus else []
    setting_lower = [s.lower() for s in selected_setting] if selected_setting else []
    
    # Focus features (7 binary)
    focus_features = ['balance', 'flexibility', 'coordination', 'relaxation', 
                     'strength', 'endurance', 'longevity']
    for feature in focus_features:
        preferences[feature] = 1.0 if feature in focus_lower else 0.0
    
    # Intensity (1 continuous) - average if multiple selected
    if selected_intensity:
        intensity_map = {'low': 0.33, 'moderate': 0.67, 'high': 1.0}
        intensity_values = [intensity_map.get(i.lower(), 0.67) for i in selected_intensity]
        preferences['intensity'] = sum(intensity_values) / len(intensity_values)
    else:
        preferences['intensity'] = 0.0
    
    # Setting features (5 binary)
    setting_features = ['team', 'fun', 'duo', 'solo', 'competitive']
    for feature in setting_features:
        preferences[f'setting_{feature}'] = 1.0 if feature in setting_lower else 0.0
    
    return preferences

def get_ml_recommendations(selected_focus, selected_intensity, selected_setting, 
                          min_match_score=75, max_results=10, exclude_sports=None):
    """
    Get ML-based sport recommendations using KNN
    
    Args:
        selected_focus: List of selected focus filters
        selected_intensity: List of selected intensity filters
        selected_setting: List of selected setting filters
        min_match_score: Minimum match percentage (0-100)
        max_results: Maximum number of recommendations
        exclude_sports: List of sport names to exclude (e.g., already shown in main results)
    
    Returns:
        List of dicts: [{'sport': name, 'match_score': percentage, 'item': offer_dict}, ...]
    """
    # Load model
    model_data = load_knn_model()
    if model_data is None:
        return []
    
    knn_model = model_data['knn_model']
    scaler = model_data['scaler']
    sports_df = model_data['sports_df']
    
    # Build user preferences from filters
    user_prefs = build_user_preferences_from_filters(
        selected_focus, selected_intensity, selected_setting
    )
    
    # Build feature vector
    user_vector = np.array([user_prefs.get(col, 0.0) for col in ML_FEATURE_COLUMNS])
    user_vector = user_vector.reshape(1, -1)
    
    # Scale
    user_vector_scaled = scaler.transform(user_vector)
    
    # Get all sports as neighbors (we'll filter by threshold later)
    n_sports = len(sports_df)
    distances, indices = knn_model.kneighbors(user_vector_scaled, n_neighbors=n_sports)
    
    # Build recommendations
    recommendations = []
    exclude_sports = exclude_sports or []
    
    for distance, idx in zip(distances[0], indices[0]):
        sport_name = sports_df.iloc[idx]['Angebot']
        
        # Skip if in exclude list
        if sport_name in exclude_sports:
            continue
        
        # Convert distance to similarity score (0-100%)
        match_score = (1 - distance) * 100
        
        # Only include if above threshold
        if match_score >= min_match_score:
            recommendations.append({
                'sport': sport_name,
                'match_score': round(match_score, 1),
                'item': sports_df.iloc[idx].to_dict()
            })
        
        # Stop if we have enough
        if len(recommendations) >= max_results:
            break
    
    return recommendations

# =============================================================================
# PART 3: FILTER UTILITIES
# =============================================================================
# PURPOSE: Functions to filter sports activities and events based on user criteria
# STREAMLIT CONCEPT: These utilities work with session state filters
# FOR BEGINNERS: Notice how we break down complex filtering into clear steps

def check_event_matches_filters(event, sport_filter, weekday_filter,
                                date_start, date_end, time_start, time_end,
                                location_filter, hide_cancelled):
    """
    Check if a single event matches all the provided filters.
    
    PURPOSE: Instead of one complex condition, we check filters one by one
    BENEFIT: Easier to debug and understand what's being filtered out
    
    Args:
        event: Dictionary containing event data
        sport_filter: List of sport names to include (or None/empty for all)
        weekday_filter: List of weekdays to include (or None/empty for all)
        date_start: Start date for filtering (or None for no start limit)
        date_end: End date for filtering (or None for no end limit)
        time_start: Start time for filtering (or None for no start limit)
        time_end: End time for filtering (or None for no end limit)
        location_filter: List of locations to include (or None/empty for all)
        hide_cancelled: Boolean, if True exclude cancelled events
    
    Returns:
        Boolean: True if event matches all filters, False otherwise
    """
    # STEP 1: Check sport filter
    # If user selected specific sports, only show those
    if sport_filter and len(sport_filter) > 0:
        event_sport = event.get('sport_name', '')
        if event_sport not in sport_filter:
            return False  # This event doesn't match, exclude it
    
    # STEP 2: Check if event is cancelled
    # If user wants to hide cancelled events, exclude them
    if hide_cancelled and event.get('canceled'):
        return False
    
    # STEP 3: Parse the event's start time
    # Convert ISO format string to datetime object for comparison
    start_time = event.get('start_time')
    if isinstance(start_time, str):
        # Replace 'Z' with '+00:00' for proper timezone handling
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    else:
        start_dt = start_time
    
    # STEP 4: Check weekday filter
    # strftime('%A') gives us day name like 'Monday', 'Tuesday', etc.
    if weekday_filter and len(weekday_filter) > 0:
        event_weekday = start_dt.strftime('%A')
        if event_weekday not in weekday_filter:
            return False
    
    # STEP 5: Check date range filter
    event_date = start_dt.date()
    
    # Check if event is before start date
    if date_start and event_date < date_start:
        return False
    
    # Check if event is after end date
    if date_end and event_date > date_end:
        return False
    
    # STEP 6: Check time range filter
    if time_start or time_end:
        event_time = start_dt.time()
        
        # Check if event starts before allowed time
        if time_start and event_time < time_start:
            return False
        
        # Check if event starts after allowed time
        if time_end and event_time > time_end:
            return False
    
    # STEP 7: Check location filter
    if location_filter and len(location_filter) > 0:
        event_location = event.get('location_name', '')
        if event_location not in location_filter:
            return False
    
    # If we made it here, event passed all filters!
    return True


def filter_offers(offers, show_upcoming_only=True, search_text="", 
                 intensity=None, focus=None, setting=None):
    """
    Filter sports offers (activities) based on various criteria.
    
    PURPOSE: Show users only the activities that match their preferences
    PATTERN: Filter data step-by-step for clarity
    
    Args:
        offers: List of offer dictionaries
        show_upcoming_only: If True, only show offers with future events
        search_text: Text to search in activity names
        intensity: List of intensity levels to include (e.g., ['low', 'high'])
        focus: List of focus areas to include (e.g., ['strength', 'endurance'])
        setting: List of settings to include (e.g., ['solo', 'team'])
    
    Returns:
        List of filtered offers
    """
def filter_offers(offers, show_upcoming_only=True, search_text="", 
                 intensity=None, focus=None, setting=None, 
                 min_match_score=0, max_results=20):
    """
    Filter sports offers (activities) based on various criteria.
    
    PURPOSE: Show users activities that match their preferences
    PATTERN: Hard filters (must match) + ML scoring (when no hard filters)
    
    LOGIC:
        - If intensity/focus/setting filters are selected: strict 100% match filtering
        - If no filters selected: show all with ML scoring for ranking
    
    Args:
        offers: List of offer dictionaries
        show_upcoming_only: If True, only show offers with future events
        search_text: Text to search in activity names
        intensity: List of intensity levels (strict filter)
        focus: List of focus areas (strict filter)
        setting: List of settings (strict filter)
        min_match_score: Minimum match percentage (0-100) - only used when no hard filters
        max_results: Maximum number of results to return
    
    Returns:
        List of filtered offers with added 'match_score'
    """
    # STEP 1: Start with only offers that have meaningful tags/features
    filtered = []
    for offer in offers:
        # Check if offer has meaningful tags (valid data check)
        has_focus = offer.get('focus') and len([f for f in offer.get('focus', []) if f and f.strip()])
        has_setting = offer.get('setting') and len([s for s in offer.get('setting', []) if s and s.strip()])
        has_intensity = offer.get('intensity') and offer.get('intensity').strip()
        
        if not (has_focus or has_setting or has_intensity):
            continue
            
        # Upcoming filter (hard filter)
        if show_upcoming_only and offer.get('future_events_count', 0) == 0:
            continue
            
        # Search filter (hard filter)
        if search_text and search_text.lower() not in offer.get('name', '').lower():
            continue
            
        filtered.append(offer)
    
    # STEP 2: Apply strict filters for intensity/focus/setting
    # If ANY of these are selected, we do 100% match filtering
    has_hard_filters = bool(intensity or focus or setting)
    
    if has_hard_filters:
        # Strict filtering mode - must match ALL selected criteria
        strict_filtered = []
        
        for offer in filtered:
            matches = True
            
            # Intensity filter (must match if selected)
            if intensity:
                if offer.get('intensity') not in intensity:
                    matches = False
            
            # Focus filter (must have ANY of the selected focus areas)
            if focus and matches:
                if not (offer.get('focus') and any(f in offer.get('focus', []) for f in focus)):
                    matches = False
            
            # Setting filter (must have ANY of the selected settings)
            if setting and matches:
                if not (offer.get('setting') and any(s in offer.get('setting', []) for s in setting)):
                    matches = False
            
            if matches:
                offer['match_score'] = 100.0  # Perfect match
                strict_filtered.append(offer)
        
        return strict_filtered[:max_results]
    
    else:
        # No hard filters - use ML scoring for ranking
        # Assign default score and return
        for offer in filtered:
            offer['match_score'] = 100.0
        return filtered[:max_results]


def filter_events(events, sport_filter=None, weekday_filter=None,
                 date_start=None, date_end=None, time_start=None, time_end=None,
                 location_filter=None, hide_cancelled=True):
    """
    Filter a list of events using our check_event_matches_filters function.
    
    PURPOSE: Apply all filters to a list of events
    PATTERN: Loop through each event and check if it passes filters
    
    Args:
        events: List of event dictionaries
        Various filter parameters (see check_event_matches_filters for details)
    
    Returns:
        List of filtered events
    """
    filtered = []
    
    # Check each event one by one
    for event in events:
        # Use our helper function to check if event matches
        if check_event_matches_filters(
            event, sport_filter, weekday_filter,
            date_start, date_end, time_start, time_end,
            location_filter, hide_cancelled
        ):
            filtered.append(event)
    
    return filtered

# =============================================================================
# PART 4: SIDEBAR COMPONENTS (UNIFIED VERSION)
# =============================================================================
# PURPOSE: Create a consistent sidebar that works across all tabs
# SIMPLIFICATION: Original had complex context-dependent logic, this is unified
# STREAMLIT CONCEPT: st.sidebar creates a sidebar, session_state persists data
# FOR BEGINNERS: Session state is KEY - it remembers user selections between reruns

def create_user_info_card_html(user_name, user_email):
    """
    Create HTML for the user info card display.
    
    PURPOSE: Show current logged-in user information
    STREAMLIT CONCEPT: st.markdown with unsafe_allow_html=True lets us use custom HTML/CSS
    FOR BEGINNERS: You can style Streamlit apps with HTML, but use it sparingly
    
    Args:
        user_name: User's display name
        user_email: User's email address
    
    Returns:
        HTML string for rendering
    """
    return f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="color: white; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
            👤 Signed in as
        </div>
        <div style="color: white; font-size: 16px; font-weight: 700; margin-bottom: 4px;">
            {user_name}
        </div>
        <div style="color: rgba(255,255,255,0.8); font-size: 13px;">
            {user_email}
        </div>
    </div>
    """


def render_unified_sidebar(sports_data=None, events=None):
    """
    Render a unified sidebar with all filters.
    
    PURPOSE:
        Provide a single, reusable sidebar that works consistently across
        all tabs, so filter state is managed in exactly one place.
    STREAMLIT CONCEPT:
        Session state stores filter values, widgets update them, and all
        tabs read from the same shared state.
    
    PATTERN:
        1. Show user info (login/profile)
        2. Load data if not provided
        3. Render activity filters (if sports_data available)
        4. Render course filters (if events available)
        5. Store all selections in session_state
    
    Args:
        sports_data: List of sports offers (optional, will load if None)
        events: List of events (optional, will load if None)
    """
    with st.sidebar:
        # =================================================================
        # USER INFO SECTION (Always shown first)
        # =================================================================
        # DESIGN NOTE: User info lives directly in the sidebar instead of
        # a nested helper to avoid nested sidebar contexts and duplicate keys.
        
        if not is_logged_in():
            # === NOT LOGGED IN: Show login UI ===
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <div style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 12px;">
                    🎯 UnisportAI
                </div>
                <div style="color: rgba(255,255,255,0.9); font-size: 14px; margin-bottom: 16px;">
                    Sign in to access all features
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Login button using Streamlit's authentication
            st.button(
                "🔵 Sign in with Google",
                key="sidebar_login",
                use_container_width=True,
                type="primary",
                on_click=st.login,
                args=["google"]
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            # === LOGGED IN: Show user profile card ===
            try:
                user_name = st.user.name if hasattr(st, 'user') and st.user else "User"
                user_email = st.user.email if hasattr(st, 'user') and st.user else ""
                user_picture = st.user.picture if hasattr(st, 'user') and st.user and hasattr(st.user, 'picture') else None
            except Exception:
                user_name = "User"
                user_email = ""
                user_picture = None
            
            # Display user card with profile picture (ohne zusätzlichen violetten Balken)
            with st.container():
                # Use columns for picture and info
                col_pic, col_info = st.columns([1, 3])
                
                with col_pic:
                    if user_picture and str(user_picture).startswith('http'):
                        st.image(user_picture, width=60)
                    else:
                        # Create initials avatar
                        initials = ''.join([word[0].upper() for word in user_name.split()[:2]])
                        st.markdown(f"""
                        <div style="width: 60px; height: 60px; border-radius: 50%; 
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    display: flex; align-items: center; justify-content: center;
                                    color: white; font-size: 20px; font-weight: bold;
                                    border: 3px solid white;">
                            {initials}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col_info:
                    st.markdown(f"""
                    <div style="color: #333; font-size: 12px; font-weight: 600; margin-bottom: 4px;">
                        👤 Signed in as
                    </div>
                    <div style="color: #333; font-size: 14px; font-weight: 700; margin-bottom: 2px;">
                        {user_name}
                    </div>
                    <div style="color: #666; font-size: 11px;">
                        {user_email}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Separator after user section
        st.markdown("---")
        # =================================================================
        # QUICK SEARCH (Always visible)
        # =================================================================
        # This simple search box is always shown at the top
        search_text = st.text_input(
            "🔎 Quick Search",
            value=st.session_state.get('search_text', ''),
            placeholder="Search activities...",
            key="unified_search_text",
            help="Search by activity name, location, or trainer"
        )
        # IMPORTANT: Store in session_state so other tabs can access it
        st.session_state['search_text'] = search_text
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =================================================================
        # LOAD DATA (immer laden, ohne Error Handling)
        # =================================================================
        from db import get_offers_complete, get_events

        if sports_data is None:
            sports_data = st.session_state.get('sports_data')
        if sports_data is None:
            sports_data = get_offers_complete()
            st.session_state['sports_data'] = sports_data

        if events is None:
            events = st.session_state.get('events_data')
        if events is None:
            events = get_events()
            st.session_state['events_data'] = events

        # Fallbacks, damit die Filter immer gerendert werden können
        sports_data = sports_data or []
        events = events or []
        
        # =================================================================
        # ACTIVITY FILTERS (immer anzeigen)
        # =================================================================
        with st.expander("🎯 Activity Type", expanded=True):
                # Extract unique intensity values from all sports
                intensities = sorted(set([
                    item.get('intensity') 
                    for item in sports_data 
                    if item.get('intensity')
                ]))
                
                # Extract all unique focus areas
                all_focuses = set()
                for item in sports_data:
                    if item.get('focus'):
                        all_focuses.update(item.get('focus'))
                focuses = sorted(list(all_focuses))
                
                # Extract all unique settings
                all_settings = set()
                for item in sports_data:
                    if item.get('setting'):
                        all_settings.update(item.get('setting'))
                settings = sorted(list(all_settings))
                
                # --- Intensity Filter ---
                if intensities:
                    selected_intensity = st.multiselect(
                        "💪 Intensity",
                        options=intensities,
                        default=st.session_state.get('intensity', []),
                        key="unified_intensity",
                        help="Filter by exercise intensity level"
                    )
                    st.session_state['intensity'] = selected_intensity
                
                # --- Focus Filter ---
                if focuses:
                    selected_focus = st.multiselect(
                        "🎯 Focus",
                        options=focuses,
                        default=st.session_state.get('focus', []),
                        key="unified_focus",
                        help="Filter by training focus area"
                    )
                    st.session_state['focus'] = selected_focus
                
                # --- Setting Filter ---
                if settings:
                    selected_setting = st.multiselect(
                        "🏠 Setting",
                        options=settings,
                        default=st.session_state.get('setting', []),
                        key="unified_setting",
                        help="Indoor or outdoor activities"
                    )
                    st.session_state['setting'] = selected_setting
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- Show Upcoming Only Checkbox ---
                show_upcoming = st.checkbox(
                    "📅 Show upcoming only",
                    value=st.session_state.get('show_upcoming_only', True),
                    key="unified_show_upcoming"
                )
        
        # =================================================================
        # COURSE FILTERS (immer anzeigen)
        # =================================================================
        # --- Location & Weekday Filters (TOP) ---
        with st.expander("📍 Location & Day", expanded=False):
            # Location filter
            locations = sorted(set([
                e.get('location_name', '') 
                for e in events 
                if e.get('location_name')
            ]))
            
            selected_locations = st.multiselect(
                "📍 Location",
                options=locations,
                default=st.session_state.get('location', []),
                key="unified_location",
                help="Filter by location/venue"
            )
            st.session_state['location'] = selected_locations
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Weekday filter with German translations
            weekdays_german = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag', 
                'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }
            weekday_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                              'Friday', 'Saturday', 'Sunday']
            
            selected_weekdays = st.multiselect(
                "📆 Weekday",
                options=weekday_options,
                default=st.session_state.get('weekday', []),
                format_func=lambda x: weekdays_german.get(x, x),
                key="unified_weekday",
                help="Filter by day of the week"
            )
            st.session_state['weekday'] = selected_weekdays
        
        # --- Sport Filter ---
        with st.expander("🏃 Sport & Status", expanded=True):
            # Get all unique sport names from events
            sport_names = sorted(set([
                e.get('sport_name', '') 
                for e in events 
                if e.get('sport_name')
            ]))
            
            # Check for pre-selected sports from Sports Overview tab
            default_sports = []
            selected_offer = st.session_state.get('selected_offer')
            if selected_offer:
                selected_name = selected_offer.get('name', '')
                if selected_name and selected_name in sport_names:
                    default_sports = [selected_name]
            
            selected_sports = st.multiselect(
                "Sport",
                options=sport_names,
                default=st.session_state.get('offers', default_sports),
                key="unified_sport"
            )
            st.session_state['offers'] = selected_sports
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Hide Cancelled Checkbox ---
            hide_cancelled = st.checkbox(
                "🚫 Hide cancelled courses",
                value=st.session_state.get('hide_cancelled', True),
                key="unified_hide_cancelled"
            )
            st.session_state['hide_cancelled'] = hide_cancelled
        
        # --- Date & Time Filters ---
        with st.expander("📅 Date & Time", expanded=False):
            st.markdown("**Date Range**")
            
            # Date range inputs (two columns)
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "From",
                    value=st.session_state.get('date_start', None),
                    key="unified_start_date"
                )
                st.session_state['date_start'] = start_date
            
            with col2:
                end_date = st.date_input(
                    "To",
                    value=st.session_state.get('date_end', None),
                    key="unified_end_date"
                )
                st.session_state['date_end'] = end_date
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Time Range**")
            
            # Time range inputs (two columns)
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input(
                    "From",
                    value=st.session_state.get('start_time', None),
                    key="unified_start_time"
                )
                # Only store if not default midnight
                if start_time != time(0, 0):
                    st.session_state['start_time'] = start_time
                else:
                    st.session_state['start_time'] = None
            
            with col2:
                end_time = st.time_input(
                    "To",
                    value=st.session_state.get('end_time', None),
                    key="unified_end_time"
                )
                # Only store if not default midnight
                if end_time != time(0, 0):
                    st.session_state['end_time'] = end_time
                else:
                    st.session_state['end_time'] = None
        
        # =================================================================
        # AI SETTINGS (immer anzeigen)
        # =================================================================
        with st.expander("🤖 AI Settings", expanded=False):
            min_match_score = st.slider(
                "Minimum Match Score",
                min_value=0,
                max_value=100,
                value=st.session_state.get('min_match_score', 0),
                step=5,
                key="unified_min_match",
                help="Show activities that match at least this percentage of your preferences"
            )
            st.session_state['min_match_score'] = min_match_score
            
            max_results = st.number_input(
                "Max Results",
                min_value=5,
                max_value=50,
                value=st.session_state.get('max_results', 20),
                step=5,
                key="unified_max_results"
            )
            st.session_state['max_results'] = max_results


def get_data_timestamp():
    """
    Get the timestamp of the last data update from database.
    
    PURPOSE: Show users when data was last refreshed
    STREAMLIT CONCEPT: Query database to get ETL run timestamp
    FOR BEGINNERS: This shows how to query a simple table
    
    Returns:
        Formatted date/time string (Swiss format)
    """
    try:
        client = get_supabase_client()
        last_run = None
        
        if client is not None:
            # Query the etl_runs table to get the most recent run
            resp = (
                client
                .table("etl_runs")
                .select("ran_at")
                .order("ran_at", desc=True)
                .limit(1)
                .execute()
            )
            if resp.data:
                last_run = resp.data[0].get("ran_at")
        
        if not last_run:
            return "unknown"
        
        # Convert to Swiss timezone and format
        dt = datetime.fromisoformat(str(last_run).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt_swiss = dt.astimezone(ZoneInfo("Europe/Zurich"))
        return dt_swiss.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return "unknown"

# =============================================================================
# PART 5: MAIN APP - AUTHENTICATION & DATABASE CHECK
# =============================================================================
# PURPOSE: Handle user authentication and verify database connection
# STREAMLIT CONCEPT: Code at module level runs on every page load
# FOR BEGINNERS: This section runs BEFORE the tabs
# 
# NOTE: User info section is now part of unified sidebar (no separate call needed)

# =============================================================================
# DATABASE CONNECTION CHECK
# =============================================================================
# DESIGN NOTE:
#     External dependencies are validated early so configuration issues are
#     surfaced before any complex UI logic is executed.
db_ok, db_message = test_database_connection()

if not db_ok:
    # Show database error prominently at the top
    st.error("⚠️ Database Not Connected")
    with st.expander("📚 How to fix this", expanded=True):
        st.markdown(db_message)
        st.markdown("""
        ### Why does this matter?
        
        This app uses **Supabase** (a PostgreSQL database) to store:
        - Sports activities and courses
        - User profiles and preferences  
        - Ratings and social connections
        - ETL run timestamps
        
        **Without the database, the app can't load data.**
        
        ### How to proceed:
        - Verify the configuration in `.streamlit/secrets.toml`
        - Check your Supabase project status
        - Review the connection details shown in the error message above
        
        As a fallback, you can still study the code structure and UI patterns
        even when live data is not available.
        """)
    
    st.info("💡 The app will continue, but database-dependent features will not be available.")

# =============================================================================
# AUTHENTICATION CHECK
# =============================================================================
# If user is logged in, sync with database and check token
if is_logged_in():
    check_token_expiry()  # Make sure authentication hasn't expired
    try:
        sync_user_to_supabase()  # Sync user data to our database
    except Exception as e:
        # Only show warning if database is supposed to be working
        if db_ok:
            st.warning(f"Error syncing user: {e}")

# =============================================================================
# RENDER UNIFIED SIDEBAR (ONCE FOR ALL TABS)
# =============================================================================
# IMPORTANT:
#     The sidebar must be rendered once at module level, not separately
#     inside each tab. Re-rendering it per tab would create duplicate
#     widget keys and scattered state.
#
# PATTERN:
#     - Call render_unified_sidebar() once here, before defining tabs.
#     - Keep user info and all filters in this single sidebar.
#     - Read the resulting values from st.session_state inside the tabs.

render_unified_sidebar()

# =============================================================================
# CREATE TABS
# =============================================================================
# STREAMLIT CONCEPT:
#     st.tabs() creates a tabbed interface; each tab is a context manager
#     entered with a ``with`` block.
#
# LIMITATION:
#     st.tabs() does not support programmatic tab switching. When a user
#     clicks a button, we cannot directly activate another tab.
#
# PRACTICAL WORKAROUND:
#     - Store the selected offer in st.session_state when "View Details"
#       is clicked.
#     - The details tab reads that value and shows the corresponding data.
#     - The user then manually switches to the "📅 Course Dates" tab.

tab_overview, tab_details, tab_athletes, tab_profile, tab_about = st.tabs([
    "🎯 Sports Overview",
    "📅 Course Dates",
    "👥 Athletes & Friends",
    "⚙️ My Profile",
    "ℹ️ About"
])

# =============================================================================
# PART 6: TAB 1 - SPORTS OVERVIEW
# =============================================================================
# PURPOSE:
#     Show all sports activities with filters and ML recommendations.
# STREAMLIT CONCEPT:
#     Use containers, columns, buttons and expanders to build a structured
#     “list view” over the filtered offers.

with tab_overview:
    # Import database functions
    from db import get_offers_complete, get_events
    
    # =========================================================================
    # LOAD DATA
    # =========================================================================
    # Get all sports offers from database (includes event counts and trainers)
    # BEST PRACTICE: Load data once at the top, not repeatedly in loops
    # ERROR HANDLING: Gracefully handle database connection issues
    try:
        offers_data = get_offers_complete()
    except Exception as e:
        st.error("❌ **Database Connection Error**")
        st.info("""
        This error occurs when the database is not reachable.
        
        **How to investigate:**
        1. Check that `.streamlit/secrets.toml` has valid Supabase credentials.
        2. Verify that your Supabase project is active.
        3. Confirm that your internet connection is working.
        
        You can still explore the code structure even if live data is not available.
        """)
        st.stop()
    
    # Store in session state so other tabs can use it.
    # This makes the data available globally without re-querying the database.
    st.session_state['sports_data'] = offers_data
    
    # =========================================================================
    # GET FILTER VALUES FROM SESSION STATE
    # =========================================================================
    # WHY SESSION STATE IS ESSENTIAL (even with unified sidebar):
    # 
    # 1. Streamlit reruns the ENTIRE script on every interaction
    # 2. Widget values are ephemeral - they reset without session_state
    # 3. When switching tabs, all widgets are recreated from scratch
    # 4. We need to SHARE filter values between sidebar and tab content
    # 5. Without session_state, filters would reset every time you interact
    # 
    # EXAMPLE: User selects "strength" focus → clicks tab → without session_state,
    # the filter would disappear! Session state PERSISTS the value.
    # 
    # PATTERN: Get values with .get() and provide defaults
    search_text = st.session_state.get('search_text', '')
    selected_intensity = st.session_state.get('intensity', [])
    selected_focus = st.session_state.get('focus', [])
    selected_setting = st.session_state.get('setting', [])
    show_upcoming_only = st.session_state.get('show_upcoming_only', True)
    
    # Additional filters for event filtering (if user drills down)
    selected_offers_filter = st.session_state.get('offers', [])
    selected_weekdays = st.session_state.get('weekday', [])
    date_start = st.session_state.get('date_start', None)
    date_end = st.session_state.get('date_end', None)
    time_start_filter = st.session_state.get('start_time', None)
    time_end_filter = st.session_state.get('end_time', None)
    selected_locations = st.session_state.get('location', [])
    hide_cancelled = st.session_state.get('hide_cancelled', True)
    
    # =========================================================================
    # APPLY FILTERS TO OFFERS
    # =========================================================================
    # Use our filter_offers function to get matching activities
    offers = filter_offers(
        offers_data,
        show_upcoming_only=show_upcoming_only,
        search_text=search_text,
        intensity=selected_intensity if selected_intensity else None,
        focus=selected_focus if selected_focus else None,
        setting=selected_setting if selected_setting else None,
        min_match_score=st.session_state.get('min_match_score', 0),
        max_results=st.session_state.get('max_results', 20)
    )
    
    # =========================================================================
    # PAGE HEADER
    # =========================================================================
    st.title("🎯 Sports Overview")
    st.write("Discover and book your perfect sports activities")
    
    # Show toast notification if user just clicked "View Details"
    if st.session_state.get('show_details_hint'):
        st.toast("✅ Activity selected! Click the 📅 Course Dates tab to view full details.", icon="👉")
        # Clear the flag so hint doesn't persist
        del st.session_state['show_details_hint']
    
    # =========================================================================
    # DISPLAY MATCHING ACTIVITIES
    # =========================================================================
    if offers:
        st.subheader(f"📋 Matching Activities ({len(offers)})")
        
        # Loop through each matching offer
        for offer in offers:
            # STREAMLIT CONCEPT: st.container(border=True) creates a card-like visual
            with st.container(border=True):
                # Create two columns: content (wide) and action button (narrow)
                col_content, col_action = st.columns([4, 1])
                
                # LEFT COLUMN: Activity information
                with col_content:
                    # Activity name with icon
                    icon = offer.get('icon', '🏃')
                    name = offer.get('name', 'Activity')
                    
                    # Match score badge
                    match_score = offer.get('match_score', 0)
                    if match_score >= 90:
                        score_badge = f" <span style='background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;'>{match_score:.0f}% Match</span>"
                    elif match_score >= 70:
                        score_badge = f" <span style='background-color: #fef9c3; color: #854d0e; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;'>{match_score:.0f}% Match</span>"
                    else:
                        score_badge = f" <span style='background-color: #f3f4f6; color: #374151; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;'>{match_score:.0f}% Match</span>"
                    
                    st.markdown(f"### {icon} {name} {score_badge}", unsafe_allow_html=True)
                    
                    # Build metadata row (intensity, focus, setting, events)
                    metadata_parts = []
                    
                    # Intensity badge with color
                    intensity_value = offer.get('intensity') or ''
                    intensity = intensity_value.capitalize() if intensity_value else ''
                    if intensity:
                        # Map intensity to colored emoji
                        color_map = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
                        color_emoji = color_map.get(intensity, '⚪')
                        metadata_parts.append(f"{color_emoji} {intensity}")
                    
                    # Focus areas (show first 2, indicate if more)
                    if offer.get('focus'):
                        # Get focus list and capitalize, filter empty strings
                        focus_list = [f.capitalize() for f in offer['focus'][:2] if f]
                        # If more than 2 focus areas, show count
                        if len(offer['focus']) > 2:
                            focus_list.append(f"+{len(offer['focus']) - 2}")
                        metadata_parts.append(f"🎯 {', '.join(focus_list)}")
                    
                    # Settings (indoor/outdoor, etc.)
                    if offer.get('setting'):
                        setting_list = [s.capitalize() for s in offer['setting'][:2] if s]
                        metadata_parts.append(f"🏠 {', '.join(setting_list)}")
                    
                    # Load and filter events to get accurate count after all filters
                    events = get_events(offer_href=offer['href'])
                    
                    # Filter for future events only
                    today = datetime.now().date()
                    upcoming_events = []
                    for e in events:
                        event_date = datetime.fromisoformat(
                            str(e.get('start_time')).replace('Z', '+00:00')
                        ).date()
                        # Include if future and not cancelled
                        if event_date >= today and not e.get('canceled'):
                            upcoming_events.append(e)
                    
                    # Apply detail filters if any are set
                    if (selected_offers_filter or selected_weekdays or date_start or 
                        date_end or time_start_filter or time_end_filter or selected_locations):
                        upcoming_events = filter_events(
                            upcoming_events,
                            sport_filter=selected_offers_filter or None,
                            weekday_filter=selected_weekdays or None,
                            date_start=date_start,
                            date_end=date_end,
                            time_start=time_start_filter,
                            time_end=time_end_filter,
                            location_filter=selected_locations or None,
                            hide_cancelled=hide_cancelled
                        )
                    
                    # Use filtered count instead of static future_events_count
                    filtered_count = len(upcoming_events)
                    
                    # Event count (now using filtered count)
                    if filtered_count > 0:
                        metadata_parts.append(f"📅 {filtered_count} upcoming")
                    else:
                        metadata_parts.append("⏸️ No upcoming dates")
                    
                    # Display metadata row
                    st.caption(' • '.join(metadata_parts))
                    
                    # Additional info row (trainers and ratings)
                    info_parts = []
                    
                    # Trainers (show first 2)
                    trainers = offer.get('trainers', [])
                    if trainers:
                        trainer_names = [t.get('name', '') for t in trainers[:2]]
                        if len(trainers) > 2:
                            trainer_names.append(f"+{len(trainers)-2}")
                        info_parts.append(f"👤 {', '.join(trainer_names)}")
                    
                    # Rating
                    if offer.get('rating_count', 0) > 0:
                        rating = offer.get('avg_rating', 0)
                        stars = '⭐' * int(round(rating))
                        info_parts.append(f"{stars} {rating:.1f} ({offer['rating_count']})")
                    
                    if info_parts:
                        st.caption(' • '.join(info_parts))
                
                # RIGHT COLUMN: Action button
                with col_action:
                    st.write("")  # Spacing
                    # Button to view details
                    button_key = f"view_{offer['href']}"
                    if st.button("View Details", key=button_key, use_container_width=True, type="primary"):
                        # Store selected offer in session state so the details tab
                        # can pick it up and render the corresponding course dates.
                        st.session_state['selected_offer'] = offer
                        st.session_state['show_details_hint'] = True  # Flag to show hint
                
                # EXPANDABLE SECTION: Show upcoming dates
                if filtered_count > 0:
                    
                    with st.expander(f"📅 Show {filtered_count} upcoming date{'s' if filtered_count != 1 else ''}", expanded=False):
                        
                        # Sort by start time (events are already filtered above)
                        upcoming_events.sort(key=lambda x: x.get('start_time', ''))
                        
                        if upcoming_events:
                            # German weekday abbreviations
                            weekdays = {
                                'Monday': 'Mo', 'Tuesday': 'Di', 'Wednesday': 'Mi',
                                'Thursday': 'Do', 'Friday': 'Fr', 'Saturday': 'Sa', 'Sunday': 'So'
                            }
                            
                            # Build table data
                            events_table_data = []
                            for event in upcoming_events[:10]:  # Show max 10
                                start_dt = datetime.fromisoformat(
                                    str(event.get('start_time')).replace('Z', '+00:00')
                                )
                                
                                # Format time range
                                end_time = event.get('end_time')
                                if end_time:
                                    end_dt = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
                                    time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                                else:
                                    time_str = start_dt.strftime('%H:%M')
                                
                                # Get weekday abbreviation
                                weekday = weekdays.get(start_dt.strftime('%A'), start_dt.strftime('%A'))
                                
                                events_table_data.append({
                                    'date': start_dt.date(),
                                    'time': time(start_dt.hour, start_dt.minute),
                                    'weekday': weekday,
                                    'location': event.get('location_name', 'N/A')
                                })
                            
                            # Display as dataframe with column config
                            st.dataframe(
                                events_table_data,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "date": st.column_config.DateColumn(
                                        "Date",
                                        format="DD.MM.YYYY",
                                    ),
                                    "time": st.column_config.TimeColumn(
                                        "Time",
                                        format="HH:mm",
                                    ),
                                    "weekday": "Day",
                                    "location": "Location"
                                }
                            )
                            
                            # If more than 10 events, show button to view all
                            if len(upcoming_events) > 10:
                                if st.button(
                                    f"View all {len(upcoming_events)} dates →",
                                    key=f"all_dates_{offer['href']}",
                                    use_container_width=True
                                ):
                                    # Store offer and show hint (user must manually switch tabs)
                                    st.session_state['selected_offer'] = offer
                                    st.session_state['show_details_hint'] = True
                        else:
                            st.info("No upcoming dates match your filters")
    else:
        st.info("🔍 No activities found matching your filters.")
        st.caption("Try adjusting your search or filters in the sidebar.")
    
    # Empty state footer
    if len(offers) == 0:
        st.info("💡 **Tip:** Try clearing some filters to see more activities")

# =============================================================================
# PART 7: TAB 2 - COURSE DATES
# =============================================================================
# PURPOSE: Show detailed course dates and event information
# STREAMLIT CONCEPT: Event filtering, date/time displays, rating widgets
# FOR BEGINNERS: This shows how to display detailed, filterable event lists

with tab_details:
    # Import necessary functions
    from db import (
        get_events,
        get_user_id_by_sub,
        get_offers_complete
    )
    from rating import (
        render_sportangebot_rating_widget,
        render_trainer_rating_widget,
        get_average_rating_for_offer,
        get_average_rating_for_trainer
    )
    
    # =========================================================================
    # GET SELECTED OFFER (if coming from Overview tab)
    # =========================================================================
    # Check if the user clicked "View Details" on a specific activity.
    # Tabs cannot switch automatically, but they can share data via session_state.
    selected = st.session_state.get('selected_offer', None)
    
    # =========================================================================
    # PAGE HEADER
    # =========================================================================
    if not selected:
        # Showing all course dates
        st.title("📅 Course Dates")
        st.caption("All upcoming course dates")
    else:
        # Showing dates for specific activity
        icon = selected.get('icon', '🏃')
        name = selected.get('name', 'Sports Activity')
        st.title(f"{icon} {name}")
        st.caption("View upcoming course dates")
    
    # =========================================================================
    # ACTIVITY INFO SECTION (only for single activity view)
    # =========================================================================
    if selected:
        # Description in expandable section
        description = selected.get('description')
        if description:
            with st.expander("📖 Activity Description", expanded=False):
                st.markdown(description, unsafe_allow_html=True)
        
        # Metrics in clean columns (ohne abgeschnittene Texte)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            intensity = (selected.get('intensity') or 'N/A').capitalize()
            color_map = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
            intensity_icon = color_map.get(intensity, '⚪')
            st.caption("Intensity")
            st.markdown(f"**{intensity_icon} {intensity}**")
        
        with col2:
            # Show first 2 focus areas
            focus = ', '.join([f.capitalize() for f in selected.get('focus', [])][:2])
            if len(selected.get('focus', [])) > 2:
                focus += '...'
            st.caption("Focus")
            st.markdown(f"**{focus or 'N/A'}**")
        
        with col3:
            # Show first 2 settings
            setting = ', '.join([s.capitalize() for s in selected.get('setting', [])][:2])
            st.caption("Setting")
            st.markdown(f"**{setting or 'N/A'}**")
        
        with col4:
            # Show average rating
            rating_info = get_average_rating_for_offer(selected['href'])
            if rating_info['count'] > 0:
                stars = '⭐' * int(round(rating_info['avg']))
                st.caption("Rating")
                st.markdown(f"**{stars} {rating_info['avg']:.1f}**")
                st.caption(f"{rating_info['count']} reviews")
            else:
                st.caption("Rating")
                st.markdown("**No reviews yet**")
        
        st.divider()
    
    # =========================================================================
    # LOAD EVENTS
    # =========================================================================
    # Load events - either for specific offer or all events
    # ERROR HANDLING: Gracefully handle database connection issues
    try:
        with st.spinner('🔄 Loading course dates...'):
            if selected:
                events = get_events(offer_href=selected['href'])
            else:
                events = get_events()
    except Exception as e:
        st.error("❌ **Database Connection Error**")
        st.info("""
        Events cannot be loaded because the database connection failed.
        
        **Checklist:**
        - Verify Supabase credentials in `.streamlit/secrets.toml`
        - Make sure the Supabase project is reachable
        """)
        st.stop()
    
    if not events:
        st.info("📅 No course dates available.")
    else:
        # =====================================================================
        # NOTE: Sidebar is already rendered at module level
        # =====================================================================
        # The sidebar is created only once before the tabs; here we simply
        # read the filter values that were stored in session_state.
        # =====================================================================
        # GET FILTER STATES
        # =====================================================================
        selected_sports = st.session_state.get('offers', [])
        hide_cancelled = st.session_state.get('hide_cancelled', True)
        date_start = st.session_state.get('date_start', None)
        date_end = st.session_state.get('date_end', None)
        selected_locations = st.session_state.get('location', [])
        selected_weekdays = st.session_state.get('weekday', [])
        time_start_filter = st.session_state.get('start_time', None)
        time_end_filter = st.session_state.get('end_time', None)
        
        # =====================================================================
        # APPLY FILTERS
        # =====================================================================
        # Filter events step by step for clarity
        filtered_events = []
        
        for e in events:
            # Sport filter
            if selected_sports and e.get('sport_name', '') not in selected_sports:
                continue
            
            # Cancelled filter
            if hide_cancelled and e.get('canceled'):
                continue
            
            # Date filter
            if date_start or date_end:
                start_time = e.get('start_time')
                start_dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                event_date = start_dt.date()
                
                if date_start and event_date < date_start:
                    continue
                if date_end and event_date > date_end:
                    continue
            
            # Location filter
            if selected_locations and e.get('location_name', '') not in selected_locations:
                continue
            
            # Weekday filter
            if selected_weekdays:
                start_dt = datetime.fromisoformat(str(e.get('start_time')).replace('Z', '+00:00'))
                if start_dt.strftime('%A') not in selected_weekdays:
                    continue
            
            # Time filter
            if time_start_filter or time_end_filter:
                start_dt = datetime.fromisoformat(str(e.get('start_time')).replace('Z', '+00:00'))
                event_time = start_dt.time()
                
                if time_start_filter and event_time < time_start_filter:
                    continue
                if time_end_filter and event_time > time_end_filter:
                    continue
            
            # Event passed all filters
            filtered_events.append(e)
        
        # =====================================================================
        # DISPLAY FILTERED EVENTS
        # =====================================================================
        if not filtered_events:
            st.info("🔍 No events match the selected filters.")
        else:
            # German weekday translations for display
            weekdays_german = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag',
                'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }
            
            # Standardansicht: Tabelle (Cards-Ansicht entfernt)
            # Table View
            table_data = []
            for event in filtered_events:
                start_dt = datetime.fromisoformat(str(event.get('start_time')).replace('Z', '+00:00'))
                end_time = event.get('end_time')
                
                if end_time:
                    end_dt = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
                    time_val = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                else:
                    time_val = start_dt.strftime('%H:%M')
                
                weekday = weekdays_german.get(start_dt.strftime('%A'), start_dt.strftime('%A'))
                
                table_data.append({
                    "date": start_dt.date(),
                    "time": time_val, # Keep as string for range
                    "weekday": weekday,
                    "sport": event.get('sport_name', 'Course'),
                    "location": event.get('location_name', 'N/A'),
                    "trainers": ", ".join(event.get('trainers', [])),
                    "status": "Cancelled" if event.get('canceled') else "Active"
                })
            
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "date": st.column_config.DateColumn("Date", format="DD.MM.YYYY"),
                    "time": "Time",
                    "weekday": "Day",
                    "sport": "Sport",
                    "location": "Location",
                        "trainers": "Trainers",
                        "status": st.column_config.TextColumn(
                            "Status",
                            help="Course status",
                            validate="^(Active|Cancelled)$"
                        )
                    }
                )
            
            # ================================================================
            # RATING SECTION (only for logged-in users and single activity)
            # ================================================================
            if is_logged_in() and selected:
                # Collect all unique trainers from events
                all_trainers = set()
                for event in filtered_events:
                    trainers = event.get('trainers', [])
                    for trainer_name in trainers:
                        if trainer_name:
                            all_trainers.add(trainer_name)
                
                # Show trainer ratings
                if all_trainers:
                    st.divider()
                    st.subheader("⭐ Rate Trainers")
                    st.caption("Share your experience with trainers you know")
                    
                    for trainer_name in sorted(all_trainers):
                        rating_info = get_average_rating_for_trainer(trainer_name)
                        
                        if rating_info['count'] > 0:
                            stars = '⭐' * int(round(rating_info['avg']))
                            st.markdown(f"**{trainer_name}** {stars} {rating_info['avg']:.1f}/5 ({rating_info['count']} reviews)")
                        else:
                            st.markdown(f"**{trainer_name}** - No reviews yet")
                        
                        render_trainer_rating_widget(trainer_name)
                        st.divider()
                
                # Show activity rating
                st.subheader("⭐ Rate This Activity")
                render_sportangebot_rating_widget(selected['href'])

# =============================================================================
# PART 8: TAB 3 - ATHLETES & FRIENDS
# =============================================================================
# PURPOSE: Social features - discover athletes, send/receive friend requests
# STREAMLIT CONCEPT: Authentication gates, database queries, user interactions
# FOR BEGINNERS: This shows how to build social features in Streamlit

with tab_athletes:
    # =========================================================================
    # CHECK LOGIN STATUS
    # =========================================================================
    # This tab requires authentication - check if user is logged in
    # PATTERN: Early return pattern for authentication gates
    
    if not is_logged_in():
        # User is NOT logged in - show info message and stop
        st.title("👥 Athletes & Friends")
        st.info("🔒 **Login required** - Sign in with Google in the sidebar to connect with other athletes!")
        
        st.markdown("""
        ### Why sign in?
        - 👥 **Discover Athletes** - Find and connect with other sports enthusiasts
        - 📩 **Friend Requests** - Send and receive friend requests
        - 🤝 **Build Your Network** - Connect with your sports community
        - ⭐ **Rate & Review** - Share your experience with courses and trainers
        """)
        st.stop()  # Stop execution here - don't show rest of tab content
    
    # =========================================================================
    # IMPORT FUNCTIONS (only if logged in)
    # =========================================================================
    from db import (
        get_user_id_by_sub,
        get_public_users,
        get_friend_status,
        send_friend_request,
        accept_friend_request,
        reject_friend_request,
        unfollow_user,
        get_pending_friend_requests,
        get_user_friends,
        get_user_by_id
    )
    
    # =========================================================================
    # GET CURRENT USER ID
    # =========================================================================
    # Helper function to get current user's database ID
    def get_current_user_id():
        """
        Get the current user's database ID.
        
        PURPOSE: Convert authentication sub to database user ID
        PATTERN: Try to get existing, sync if missing
        
        Returns:
            User ID (int) or None if error
        """
        user_sub = get_user_sub()
        if not user_sub:
            return None
        
        # Try to get existing user from database
        user_id = get_user_id_by_sub(user_sub)
        
        # If user doesn't exist, try to sync
        if not user_id:
            try:
                sync_user_to_supabase()
                user_id = get_user_id_by_sub(user_sub)
            except:
                pass
        
        return user_id
    
    # Get current user's ID
    try:
        current_user_id = get_current_user_id()
        if not current_user_id:
            st.error("❌ Error loading your profile. User not found in database.")
            st.info("💡 Try logging out and logging back in.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error loading your profile: {str(e)}")
        st.stop()
    
    # =========================================================================
    # PAGE HEADER
    # =========================================================================
    st.title("👥 Athletes & Friends")
    st.caption("Connect with other athletes and build your sports community")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # =========================================================================
    # SUB-TABS FOR DIFFERENT SECTIONS
    # =========================================================================
    # STREAMLIT CONCEPT: Nested tabs for organizing related content
    tab1, tab2, tab3 = st.tabs(["🔍 Discover Athletes", "📩 Friend Requests", "👥 My Friends"])
    
    # =========================================================================
    # SUB-TAB 1: DISCOVER ATHLETES
    # =========================================================================
    with tab1:
        st.subheader("Discover Public Profiles")
        
        # Load public users from database
        with st.spinner('🔄 Loading athletes...'):
            public_users = get_public_users()
        
        if not public_users:
            st.info("📭 No public profiles available yet.")
            st.caption("Be the first to make your profile public in Settings!")
        else:
            # Filter out own profile
            public_users = [u for u in public_users if u['id'] != current_user_id]
            
            if not public_users:
                st.info("📭 No other public profiles available yet.")
                st.caption("Check back later as more athletes join the community!")
            else:
                # Display count
                st.caption(f"**{len(public_users)}** athlete{'s' if len(public_users) != 1 else ''} found")
                
                # Display each user as a card
                for user in public_users:
                    with st.container(border=True):
                        # Three columns: picture, info, action
                        col_pic, col_info, col_action = st.columns([1, 4, 2])
                        
                        with col_pic:
                            # Show profile picture or initials
                            if user.get('picture') and str(user['picture']).startswith('http'):
                                st.image(user['picture'], width=100)
                            else:
                                # Create initials avatar
                                name = user.get('name', 'U')
                                initials = ''.join([word[0].upper() for word in name.split()[:2]])
                                st.markdown(f"""
                                <div style="width: 100px; height: 100px; border-radius: 50%; 
                                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                            display: flex; align-items: center; justify-content: center;
                                            color: white; font-size: 32px; font-weight: bold;">
                                    {initials}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with col_info:
                            st.markdown(f"### {user.get('name', 'Unknown')}")
                            
                            # Bio preview (first 120 characters)
                            if user.get('bio'):
                                bio = user['bio']
                                preview = bio[:120] + "..." if len(bio) > 120 else bio
                                st.caption(preview)
                            
                            # Metadata (email and join date)
                            metadata = []
                            if user.get('email'):
                                metadata.append(f"📧 {user['email']}")
                            if user.get('created_at'):
                                join_date = user['created_at'][:10]
                                metadata.append(f"📅 Joined {join_date}")
                            
                            if metadata:
                                st.caption(' • '.join(metadata))
                        
                        with col_action:
                            st.write("")  # Spacing
                            
                            # Check friendship status
                            status = get_friend_status(current_user_id, user['id'])
                            
                            # Show different UI based on status
                            if status == "friends":
                                st.success("✓ Friends")
                                if st.button("🗑️ Unfriend", key=f"unfollow_{user['id']}", use_container_width=True):
                                    if unfollow_user(current_user_id, user['id']):
                                        st.success("✅ Unfriended")
                                        st.rerun()
                            
                            elif status == "request_sent":
                                st.info("⏳ Pending")
                            
                            elif status == "request_received":
                                st.warning("📨 Respond")
                            
                            else:
                                # No relationship - show add friend button
                                if st.button(
                                    "➕ Add Friend",
                                    key=f"request_{user['id']}",
                                    use_container_width=True,
                                    type="primary"
                                ):
                                    if send_friend_request(current_user_id, user['id']):
                                        st.success("✅ Request sent!")
                                        st.rerun()
                                    else:
                                        st.warning("Request already pending")
    
    # =========================================================================
    # SUB-TAB 2: FRIEND REQUESTS
    # =========================================================================
    with tab2:
        st.subheader("Friend Requests")
        
        # Load pending friend requests
        with st.spinner('🔄 Loading requests...'):
            requests = get_pending_friend_requests(current_user_id)
        
        if not requests:
            st.info("📭 No pending friend requests.")
            st.caption("You'll see requests here when other athletes want to connect with you.")
        else:
            st.caption(f"**{len(requests)}** pending request{'s' if len(requests) != 1 else ''}")
            
            # Display each request
            for req in requests:
                with st.container(border=True):
                    # Extract requester info (with fallback)
                    requester = req.get('requester', {})
                    if isinstance(requester, dict) and len(requester) > 0:
                        requester_name = requester.get('name', 'Unknown')
                        requester_picture = requester.get('picture')
                        requester_email = requester.get('email', '')
                    else:
                        # Fallback: query user separately
                        try:
                            requester_data = get_user_by_id(req['requester_id'])
                            if requester_data:
                                requester_name = requester_data.get('name', 'Unknown')
                                requester_picture = requester_data.get('picture')
                                requester_email = requester_data.get('email', '')
                            else:
                                requester_name = "Unknown"
                                requester_picture = None
                                requester_email = ""
                        except:
                            requester_name = "Unknown"
                            requester_picture = None
                            requester_email = ""
                    
                    # Three columns: picture, info, action
                    col_pic, col_info, col_action = st.columns([1, 4, 2])
                    
                    with col_pic:
                        if requester_picture and str(requester_picture).startswith('http'):
                            st.image(requester_picture, width=80)
                        else:
                            # Create initials avatar
                            initials = ''.join([word[0].upper() for word in requester_name.split()[:2]])
                            st.markdown(f"""
                            <div style="width: 80px; height: 80px; border-radius: 50%; 
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        display: flex; align-items: center; justify-content: center;
                                        color: white; font-size: 28px; font-weight: bold;">
                                {initials}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown(f"### {requester_name}")
                        
                        # Metadata
                        metadata = []
                        if requester_email:
                            metadata.append(f"📧 {requester_email}")
                        if req.get('created_at'):
                            request_date = req['created_at'][:10]
                            metadata.append(f"📅 Requested {request_date}")
                        
                        if metadata:
                            st.caption(' • '.join(metadata))
                    
                    with col_action:
                        st.write("")  # Spacing
                        
                        # Accept button
                        if st.button(
                            "✅ Accept",
                            key=f"accept_{req['id']}",
                            use_container_width=True,
                            type="primary"
                        ):
                            if accept_friend_request(req['id'], req['requester_id'], req['addressee_id']):
                                st.success("✅ Friend request accepted!")
                                st.rerun()
                        
                        # Decline button
                        if st.button("❌ Decline", key=f"reject_{req['id']}", use_container_width=True):
                            if reject_friend_request(req['id']):
                                st.success("Request declined")
                                st.rerun()
    
    # =========================================================================
    # SUB-TAB 3: MY FRIENDS
    # =========================================================================
    with tab3:
        st.subheader("My Friends")
        
        # Load friends list
        with st.spinner('🔄 Loading friends...'):
            friends = get_user_friends(current_user_id)
        
        if not friends:
            st.info("👋 No friends yet - start connecting with other athletes!")
            st.caption("Browse the Discover Athletes tab to send friend requests.")
        else:
            # Remove duplicates by tracking unique IDs
            seen_ids = set()
            unique_friends = []
            for friend in friends:
                friend_id = friend.get('id')
                if friend_id and friend_id not in seen_ids:
                    seen_ids.add(friend_id)
                    unique_friends.append(friend)
            
            st.caption(f"**{len(unique_friends)}** friend{'s' if len(unique_friends) != 1 else ''}")
            
            # Display each friend
            for friend in unique_friends:
                with st.container(border=True):
                    # Two columns: picture and info
                    col_pic, col_info = st.columns([1, 5])
                    
                    with col_pic:
                        if friend.get('picture') and str(friend['picture']).startswith('http'):
                            st.image(friend['picture'], width=80)
                        else:
                            # Create initials avatar
                            name = friend.get('name', 'U')
                            initials = ''.join([word[0].upper() for word in name.split()[:2]])
                            st.markdown(f"""
                            <div style="width: 80px; height: 80px; border-radius: 50%; 
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        display: flex; align-items: center; justify-content: center;
                                        color: white; font-size: 28px; font-weight: bold;">
                                {initials}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown(f"### {friend.get('name', 'Unknown')}")
                        
                        # Metadata
                        metadata = []
                        if friend.get('email'):
                            metadata.append(f"📧 {friend['email']}")
                        if friend.get('bio'):
                            bio_preview = friend['bio'][:80] + "..." if len(friend['bio']) > 80 else friend['bio']
                            metadata.append(bio_preview)
                        
                        if metadata:
                            st.caption(' • '.join(metadata))

# =============================================================================
# PART 9: TAB 4 - MY PROFILE
# =============================================================================
# PURPOSE: User profile management - view info, set preferences, control visibility
# STREAMLIT CONCEPT: Forms, state management, database updates
# FOR BEGINNERS: This shows how to build user settings pages

with tab_profile:
    # =========================================================================
    # CHECK LOGIN STATUS
    # =========================================================================
    if not is_logged_in():
        st.title("👤 My Profile")
        st.info("🔒 **Login required** - Sign in with Google in the sidebar to manage your profile!")
        
        st.markdown("""
        ### What you can do with a profile:
        - 📋 **View Your Info** - See your account details and activity
        - ⚙️ **Set Preferences** - Choose your favorite sports and activities  
        - 🌐 **Control Visibility** - Decide who can see your profile
        - 👥 **Track Social Stats** - See your friends and social connections
        - ⭐ **Rate Activities** - Share your experience with courses and trainers
        """)
        st.stop()
    
    # =========================================================================
    # IMPORTS
    # =========================================================================
    import json
    from user import (
        get_user_profile,
        get_user_favorites,
        update_user_favorites,
        update_user_preferences
    )
    from db import (
        get_offers_complete,
        update_user_settings
    )
    
    # =========================================================================
    # PAGE HEADER
    # =========================================================================
    st.title("👤 My Profile")
    st.caption("Manage your profile, preferences and settings")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # =========================================================================
    # LOAD USER PROFILE
    # =========================================================================
    profile = get_user_profile()
    if not profile:
        st.error("❌ Profile not found.")
        st.stop()
    
    # =========================================================================
    # PROFILE SUB-TABS
    # =========================================================================
    # Organize profile sections into tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Information",
        "⚙️ Preferences",
        "🌐 Visibility"
    ])
    
    # =========================================================================
    # PROFILE TAB 1: INFORMATION
    # =========================================================================
    with tab1:
        st.subheader("User Information")
        
        # User info card
        with st.container(border=True):
            col_pic, col_info = st.columns([1, 4])
            
            with col_pic:
                # Profile picture with fallback
                if profile.get('picture') and str(profile['picture']).startswith('http'):
                    st.image(profile['picture'], width=100)
                else:
                    # Create initials avatar
                    name = profile.get('name', 'U')
                    initials = ''.join([word[0].upper() for word in name.split()[:2]])
                    st.markdown(f"""
                    <div style="width: 100px; height: 100px; border-radius: 50%; 
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-size: 32px; font-weight: bold;">
                        {initials}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_info:
                    st.markdown(f"### {profile.get('name', 'N/A')}")
                    
                    # Metadata
                    metadata = []
                    if profile.get('email'):
                        metadata.append(f"📧 {profile['email']}")
                    if profile.get('created_at'):
                        metadata.append(f"📅 Member since {profile['created_at'][:10]}")
                    if profile.get('last_login'):
                        metadata.append(f"🕐 Last login {profile['last_login'][:10]}")
                    
                    if metadata:
                        st.caption(' • '.join(metadata))
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # =========================================================================
    # PROFILE TAB 2: PREFERENCES
    # =========================================================================
    with tab2:
        st.subheader("🏃 Favorite Sports")
        
        # Load sports data and current favorites
        try:
            sportangebote = get_offers_complete()
            # Create dictionary: sport name -> sport href
            sportarten_dict = {sport['name']: sport['href'] for sport in sportangebote}
            sportarten_options = sorted(list(sportarten_dict.keys()))
            
            # Load current favorites (stored as hrefs)
            current_favorite_hrefs = get_user_favorites()
            # Convert hrefs back to names for display
            current_favorite_names = [
                sport['name'] for sport in sportangebote
                if sport['href'] in current_favorite_hrefs
            ]
            
            # Multiselect for favorite sports
            favorite_sports = st.multiselect(
                "Select your favorite activities",
                options=sportarten_options,
                default=current_favorite_names,
                help="These activities will be highlighted in your overview"
            )
            
            if current_favorite_names:
                st.caption(f"Currently {len(current_favorite_names)} favorite{'s' if len(current_favorite_names) != 1 else ''} selected")
        except Exception as e:
            st.error(f"Error loading sports: {e}")
            sportarten_dict = {}
            favorite_sports = []
    
    # =========================================================================
    # PROFILE TAB 3: VISIBILITY
    # =========================================================================
    with tab3:
        st.subheader("🌐 Profile Visibility")
        
        st.info("🔍 Control who can see your profile and connect with you")
        
        # Get current visibility setting
        current_is_public = profile.get('is_public', False)
        
        # Toggle for public/private
        is_public = st.toggle(
            "Make profile public",
            value=current_is_public,
            help="Allow other users to see your profile on the Athletes page"
        )
        
        # Show status message
        if is_public:
            st.success("✅ Your profile is **public**")
            st.caption("Other users can find you, send friend requests, and see when you attend courses")
        else:
            st.warning("🔒 Your profile is **private**")
            st.caption("Only you can see your profile and activity")
        
        # Save visibility button
        if st.button("💾 Save Visibility", type="primary"):
            user_sub = get_user_sub()
            if update_user_settings(user_sub, visibility=is_public):
                st.success("✅ Visibility settings updated!")
                st.rerun()
            else:
                st.error("❌ Error updating visibility")
        
        st.divider()
        
        # Social statistics
        st.subheader("👥 Social Statistics")
        
        try:
            # Friend count is included in profile from database view
            friend_count = profile.get('friend_count', 0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Friends", friend_count)
            
            with col2:
                st.metric("Visibility", "Public" if current_is_public else "Private")
            
            if friend_count > 0:
                st.caption(f"💡 You're connected with {friend_count} athlete{'s' if friend_count != 1 else ''}")
        except Exception:
            pass
        
        st.divider()
        
        # Logout section
        st.subheader("🚪 Logout")
        st.caption("Sign out of your account")
        
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            handle_logout()

# =============================================================================
# PART 10: TAB 5 - ABOUT
# =============================================================================
# PURPOSE: Information about the app, data sources, and project team
# STREAMLIT CONCEPT: Simple information display, formatting
# FOR BEGINNERS: This shows how to create informational pages

with tab_about:
    st.title("ℹ️ About")
    st.caption("Learn more about UnisportAI and the team behind it")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # (Data status section removed on request)
    
    # =========================================================================
    # HOW IT WORKS
    # =========================================================================
    st.subheader("💡 How This App Works")
    st.markdown("""
    **What's happening behind the scenes?**
    
    1. **Automated Data Collection:** Python scripts automatically scrape Unisport websites 
       (offers, courses, dates, locations) via GitHub Actions on a regular schedule.
    
    2. **Data Storage:** All data is stored in Supabase, our hosted PostgreSQL database.
    
    3. **Real-time Display:** This Streamlit app loads data directly from Supabase and 
       displays it here in real-time.
    
    4. **Smart Features:** AI-powered recommendations using Machine Learning (KNN algorithm), 
       advanced filtering system, ratings, and social networking.
    
    **Tech Stack:**
    - **Frontend:** Streamlit (Python web framework)
    - **Database:** Supabase (PostgreSQL)
    - **ML:** scikit-learn (KNN recommender)
    - **Visualization:** Plotly (interactive charts)
    - **Authentication:** Google OAuth via Streamlit
    """)
    
    st.divider()
    
    # =========================================================================
    # PROJECT TEAM
    # =========================================================================
    st.subheader("👥 Project Team")
    
    # Team members with LinkedIn profiles
    team = [
        (
            "Tamara Nessler",
            "https://www.linkedin.com/in/tamaranessler/",
            "https://media.licdn.com/dms/image/v2/D4D03AQHoFx3FqbKv8Q/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1729070262001?e=1762387200&v=beta&t=qxTtWz-rqXh2ooOxkLCaODftWKDB-mCnB1Kf6nu4JPU",
        ),
        (
            "Till Banerjee",
            "https://www.linkedin.com/in/till-banerjee/",
            "https://media.licdn.com/dms/image/v2/D4E03AQFL1-Ud8CLN3g/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1708701675021?e=1762387200&v=beta&t=msstC8263pJyCfjiZwNzfYF3l57yHvSpIuMO77A-U0A",
        ),
        (
            "Sarah Bugg",
            "https://www.linkedin.com/in/sarah-bugg/",
            "https://media.licdn.com/dms/image/v2/D4E03AQEanhywBsKAPA/profile-displayphoto-scale_400_400/B4EZkoux6gKkAg-/0/1757324976456?e=1762387200&v=beta&t=Gicl6-C96pUuB2MUNVwbKzctjVaqaQDn39blJxdkjAo",
        ),
        (
            "Antonia Büttiker",
            "https://www.linkedin.com/in/antonia-büttiker-895713254/",
            "https://media.licdn.com/dms/image/v2/D4E03AQHZuEjmbys12Q/profile-displayphoto-shrink_400_400/B4EZVwmujrG0Ak-/0/1741350956527?e=1762387200&v=beta&t=s3ypqYDZ6Od8XU9ktFTwRNnwSHckHmFejMpnn8GdhWg",
        ),
        (
            "Luca Hagenmayer",
            "https://www.linkedin.com/in/lucahagenmayer/",
            "https://media.licdn.com/dms/image/v2/D4E03AQFGdchJCbDXFQ/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1730973343664?e=1762387200&v=beta&t=1awZw8RSI5xBKF9gFxOlFYsNDxGalTcgK3z-Ma8R0qU",
        ),
    ]
    
    # Display team in a grid (5 columns)
    cols = st.columns(5)
    for idx, (name, url, avatar) in enumerate(team):
        with cols[idx]:
            st.image(avatar, use_container_width=True)
            st.markdown(f"**[{name}]({url})**", unsafe_allow_html=True)
    
    st.divider()
    
    # =========================================================================
    # PROJECT CONTEXT
    # =========================================================================
    st.subheader("🎓 Project Background")
    st.markdown("""
    This project was created for the course **"Fundamentals and Methods of Computer Science"** 
    at the University of St.Gallen, taught by:
    - Prof. Dr. Stephan Aier
    - Dr. Bernhard Bermeitinger
    - Prof. Dr. Simon Mayer
    
    **Status:** Still in development and not yet reviewed by professors.
    
    **Feedback?** Have feature requests or found bugs? Please contact one of the team members 
    via LinkedIn (see above).
    """)

# =============================================================================
# END OF STREAMLIT APP
# =============================================================================
# KEY TAKEAWAYS FROM THIS IMPLEMENTATION:
# 1. Use session_state to persist data between reruns.
# 2. Cache expensive operations with @st.cache_resource or @st.cache_data.
# 3. Break complex logic into small, well-documented functions.
# 4. Use tabs and expanders to structure complex pages.
# 5. Check authentication before showing protected content.
# 6. Filter and display data step by step for clarity.
# 7. Provide helpful error messages and empty states.
# 8. Use st.rerun() after state changes when the UI must refresh immediately.
#
# This file is intentionally verbose so that the overall architecture,
# data flow and design decisions remain transparent to anyone reading it.
# =============================================================================


