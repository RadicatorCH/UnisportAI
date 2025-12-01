"""User management helpers.

This module provides higher-level user management utilities used by the
Streamlit UI. It builds on the lower-level Supabase client and the
authentication helper to read and update user profiles, favorites and
preferences.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from auth import get_user_sub
from db import (
    get_user_complete as db_get_user_complete,
    update_user_settings as db_update_user_settings,
    save_filter_preferences as db_save_filter_preferences,
    get_user_favorites as db_get_user_favorites,
    update_user_favorites as db_update_user_favorites,
    submit_rating as db_submit_rating
)


def get_user_profile(user_sub: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return the full user profile for the given OIDC subject.
    
    Now uses the unified get_user_complete view which includes social statistics.

    If ``user_sub`` is not supplied the function attempts to obtain the
    currently authenticated subject via ``auth.get_user_sub``.

    Args:
        user_sub (Optional[str]): OIDC subject identifier.

    Returns:
        Optional[Dict[str, Any]]: The user profile dictionary (including friend_count) 
            or ``None`` if the user cannot be resolved.
    """
    if not user_sub:
        user_sub = get_user_sub()
        if not user_sub:
            return None
    
    return db_get_user_complete(user_sub)


def update_user_preferences(preferences: Dict[str, Any]) -> bool:
    """Persist user preferences for the currently authenticated user.
    
    Now uses the unified update_user_settings function.

    Args:
        preferences (Dict[str, Any]): Preferences object to store.

    Returns:
        bool: True on success, False on failure or when no user is logged in.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    return db_update_user_settings(user_sub, preferences=preferences)


def _map_weekdays_ui_to_codes(weekdays_en: list) -> list:
    """Map English weekday names to internal weekday codes.

    Example: ``'Monday'`` -> ``'mon'``.
    """
    en_to_code = {
        'Monday': 'mon',
        'Tuesday': 'tue',
        'Wednesday': 'wed',
        'Thursday': 'thu',
        'Friday': 'fri',
        'Saturday': 'sat',
        'Sunday': 'sun',
    }
    return [en_to_code.get(w, w) for w in (weekdays_en or [])]


def save_sidebar_preferences(
    intensities: Optional[list],
    focus: Optional[list],
    settings: Optional[list],
    locations: Optional[list],
    weekdays_en: Optional[list],
) -> bool:
    """Save the current sidebar filter selections as defaults for the user.

    The preferences are stored in the users table so they are available
    the next time the user visits the application.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False

    try:
        success = db_save_filter_preferences(
            user_sub, 
            intensities, 
            focus, 
            settings, 
            locations, 
            weekdays_en
        )
        if not success:
            st.error(f"Fehler beim Speichern der Sidebar-Defaults")
        return success
    except Exception as e:
        st.error(f"Fehler beim Speichern der Sidebar-Defaults: {e}")
        return False


def get_user_favorites() -> list:
    """Return a list of the current user's favorite sport hrefs.

    Returns an empty list when no user is authenticated or when an error occurs.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return []
    
    try:
        return db_get_user_favorites(user_sub)
    except Exception as e:
        st.error(f"Fehler beim Laden der Favoriten: {e}")
        return []


def update_user_favorites(favorite_hrefs: list) -> bool:
    """Set the user's favorite sport hrefs in the database.

    Args:
        favorite_hrefs (list): List of offer href strings to save.

    Returns:
        bool: True on success, False otherwise.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    try:
        return db_update_user_favorites(user_sub, favorite_hrefs)
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren der Favoriten: {e}")
        return False


def log_user_activity(activity_type: str, details: Optional[Dict] = None):
    """Append a user activity dictionary to the session state.

    This lightweight activity logger records simple user events for
    potential display or analytics. It is stored in the application's
    session state.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return
    
    activity = {
        "user_sub": user_sub,
        "activity_type": activity_type,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Store in session state
    if 'user_activities' not in st.session_state:
        st.session_state['user_activities'] = []
    st.session_state['user_activities'].append(activity)


def submit_sportangebot_rating(sportangebot_href: str, rating: int, comment: str = "") -> bool:
    """Submit or update a user's rating for a sport offer.
    
    Now uses the unified submit_rating function.

    Performs basic validation and delegates persistence to
    ``data.supabase_client``.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    try:
        # Basic validation
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            st.error("Ungültige Bewertung (1-5)")
            return False
        
        return db_submit_rating(user_sub, "sport", sportangebot_href, rating, comment)
    except Exception as e:
        st.error(f"Fehler beim Speichern der Bewertung: {e}")
        return False

def submit_trainer_rating(trainer_name: str, rating: int, comment: str = "") -> bool:
    """Submit or update a user's rating for a trainer.
    
    Now uses the unified submit_rating function.

    Args:
        trainer_name (str): Trainer display name.
        rating (int): Integer rating between 1 and 5.
        comment (str): Optional textual comment.

    Returns:
        bool: True on success, False otherwise.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    try:
        # Basic validation
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            st.error("Ungültige Bewertung (1-5)")
            return False
        
        return db_submit_rating(user_sub, "trainer", trainer_name, rating, comment)
    except Exception as e:
        st.error(f"Fehler beim Speichern der Bewertung: {e}")
        return False

