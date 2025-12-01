"""Authentication helpers for Streamlit using Google OIDC and Supabase.

This module provides functions to manage login, logout, and synchronization
of the authenticated user with Supabase. It follows the official Streamlit
authentication documentation.

Configuration:
    - Local development: Configure .streamlit/secrets.toml with http://localhost:8501/oauth2callback
    - Production: Configure Streamlit Cloud secrets with https://unisportai.streamlit.app/oauth2callback
"""

import streamlit as st
from datetime import datetime, timezone


def is_logged_in():
    """Return True when a user is currently authenticated in Streamlit.
    
    Uses the persistent st.user.is_logged_in attribute as documented.
    """
    return st.user.is_logged_in


def clear_user_session():
    """Clear application session state related to the current user.

    This helper removes filter state, cached sports data and any stored
    user activities. It is intended to run during logout to ensure a
    clean session for the next user.
    """
    # Clear filter states
    filter_keys = ['intensity', 'focus', 'setting', 'location', 'weekday', 'offers', 
                   'search_text', 'date_start', 'date_end', 'start_time', 'end_time',
                   'hide_cancelled', 'show_upcoming_only']
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear app states
    app_keys = ['selected_offer', 'sports_data', 'active_tab', 'user_id']
    for key in app_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any cached data
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()
    if hasattr(st, 'cache_resource'):
        st.cache_resource.clear()


def handle_logout():
    """Perform logout with cleanup and rerun the Streamlit app.

    This function clears user state, calls ``st.logout()`` and triggers
    a rerun so the UI returns to an unauthenticated state.
    """
    clear_user_session()
    st.logout()
    st.rerun()




def get_user_sub():
    """Return the OIDC ``sub`` claim for the authenticated user.

    Returns ``None`` when no user is logged in.
    """
    if is_logged_in():
        return st.user.sub
    return None


def get_user_email():
    """Return the authenticated user's email address or ``None``.
    """
    if is_logged_in():
        return st.user.email
    return None


def check_token_expiry():
    """Check whether the user's token has expired and force logout if needed.

    Note: Streamlit's identity cookie expires after 30 days automatically.
    This function checks the identity provider's token expiration (if available)
    and manually calls st.logout() when the token expires, as recommended in
    the official Streamlit documentation.
    
    If the token is expired, triggers the logout workflow.
    Silently returns when no user is logged in or no expiration info is available.
    """
    if not is_logged_in():
        return

    try:
        # Check if the identity provider returned expiration information
        if hasattr(st.user, 'expires_at') and st.user.expires_at:
            if datetime.now(timezone.utc) > st.user.expires_at:
                st.warning("Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.")
                handle_logout()
    except Exception as e:
        st.error(f"Fehler beim Prüfen der Token-Gültigkeit: {e}")




def get_user_info_dict():
    """Return a dictionary with basic user information from Streamlit.

    Returns ``None`` when no user is authenticated.
    """
    if not is_logged_in():
        return None

    return {
        'sub': st.user.sub,
        'email': st.user.email,
        'name': st.user.name,
        'given_name': getattr(st.user, 'given_name', None),
        'family_name': getattr(st.user, 'family_name', None),
        'picture': getattr(st.user, 'picture', None),
        'is_logged_in': True
    }


def sync_user_to_supabase():
    """Synchronize the authenticated user record into Supabase.

    This creates or updates a user row in the ``users`` table using the
    information available from the Streamlit user object.
    """
    from db import create_or_update_user
    
    user_info = get_user_info_dict()
    if not user_info:
        return
    
    try:
        user_data = {
            "sub": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name", user_info.get("email")),
            "picture": user_info.get("picture"),
            "last_login": datetime.now().isoformat()
        }
        
        create_or_update_user(user_data)
    except Exception as e:
        st.warning(f"⚠️ Fehler beim Synchronisieren des Benutzers: {e}")

