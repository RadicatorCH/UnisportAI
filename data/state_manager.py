import streamlit as st
from typing import Any, List


def _map_weekdays_db_to_ui(weekday_codes: List[str]) -> List[str]:
    """Maps weekday_type enum codes to UI strings used in filters.py/shared_sidebar.py"""
    code_to_en = {
        'mon': 'Monday',
        'tue': 'Tuesday',
        'wed': 'Wednesday',
        'thu': 'Thursday',
        'fri': 'Friday',
        'sat': 'Saturday',
        'sun': 'Sunday',
    }
    return [code_to_en.get(code, code) for code in (weekday_codes or [])]


def _ensure_preferences_loaded():
    """Loads user preferences from DB once into session_state for filter defaults."""
    if st.session_state.get("_prefs_loaded", False):
        return

    try:
        # Load user profile
        from data.auth import get_user_sub
        from data.supabase_client import get_user_from_db, get_offers_with_stats
        from data.user_management import get_user_favorites

        user_sub = get_user_sub()
        if not user_sub:
            st.session_state["_prefs_loaded"] = True
            return

        profile = get_user_from_db(user_sub)
        if not profile:
            st.session_state["_prefs_loaded"] = True
            return

        # Map preferred columns to sidebar filter keys
        preferred_intensities = profile.get('preferred_intensities') or []
        preferred_focus = profile.get('preferred_focus') or []
        preferred_settings = profile.get('preferred_settings') or []
        favorite_location_names = profile.get('favorite_location_names') or []
        preferred_weekdays_codes = profile.get('preferred_weekdays') or []

        # Write defaults only if not already set in session
        if 'intensity' not in st.session_state:
            st.session_state['intensity'] = preferred_intensities
        if 'focus' not in st.session_state:
            st.session_state['focus'] = preferred_focus
        if 'setting' not in st.session_state:
            st.session_state['setting'] = preferred_settings
        if 'location' not in st.session_state:
            st.session_state['location'] = favorite_location_names
        if 'weekday' not in st.session_state:
            st.session_state['weekday'] = _map_weekdays_db_to_ui(preferred_weekdays_codes)

        # Preload favorite sports into 'offers' by names (sidebar expects names)
        if 'offers' not in st.session_state:
            try:
                favorite_hrefs = get_user_favorites()  # list of hrefs
                if favorite_hrefs:
                    offers = get_offers_with_stats() or []
                    href_to_name = {o.get('href'): o.get('name') for o in offers}
                    favorite_names = [href_to_name[h] for h in favorite_hrefs if h in href_to_name]
                    if favorite_names:
                        st.session_state['offers'] = favorite_names
            except Exception:
                pass

        st.session_state["_prefs_loaded"] = True
    except Exception:
        # Fail silent; UI will use its own defaults
        st.session_state["_prefs_loaded"] = True


def get_filter_state(key: str, default: Any) -> Any:
    """Returns filter value from session_state, preloading user prefs once."""
    _ensure_preferences_loaded()
    return st.session_state.get(key, default)


def set_filter_state(key: str, value: Any):
    """Sets a filter value into session_state."""
    st.session_state[key] = value


def init_multiple_offers_state(default_hrefs: List[str], state_key: str):
    """Initializes state for multiple offers selection, if missing."""
    if state_key not in st.session_state:
        st.session_state[state_key] = list(default_hrefs or [])


