"""
Authentifizierungsmodul für Streamlit mit Google OIDC und Supabase
"""

import streamlit as st
from datetime import datetime, timezone
import json


def is_logged_in():
    """Safely check if user is logged in"""
    try:
        return hasattr(st.user, 'is_logged_in') and st.user.is_logged_in
    except AttributeError:
        return False


def clear_user_session():
    """Clears all user-related session state on logout"""
    # Clear filter states
    filter_keys = ['intensity', 'focus', 'setting', 'location', 'weekday', 'offers', 
                   'search_text', 'date_start', 'date_end', 'start_time', 'end_time',
                   'hide_cancelled', 'show_upcoming_only']
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear navigation states
    nav_keys = ['state_selected_offer', 'state_nav_offer_hrefs', 'state_nav_offer_name',
                'state_page2_multiple_offers', 'state_selected_offers_multiselect',
                'state_sports_data', 'state_nav_date']
    for key in nav_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear user activity states
    activity_keys = ['user_activities', 'user_id', '_prefs_loaded']
    for key in activity_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any cached data
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()
    if hasattr(st, 'cache_resource'):
        st.cache_resource.clear()


def handle_logout():
    """Handles the logout process with proper cleanup"""
    clear_user_session()
    st.logout()
    st.rerun()


def check_auth():
    """Prüft die Authentifizierung und leitet zur Login-Seite um wenn nicht eingeloggt"""
    if not is_logged_in():
        show_login_page()
        st.stop()
    return True


def show_login_page():
    """Zeigt die Login-Seite mit Google OAuth"""
    
    # Beautiful header with university images
    st.markdown(
        """
        <div style="position: relative; height: 280px; border-radius: 10px; overflow: hidden; margin-bottom: 2rem;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 4px; height: 100%;">
            <div style="background-image:url('https://www.unisg.ch/fileadmin/_processed_/5/c/csm_HSG_Bibliothek_1_182bdcd9cf.jpg'); background-size:cover; background-position:center;"></div>
            <div style="background-image:url('https://www.unisg.ch/fileadmin/_processed_/e/f/csm_HSG_Hauptgebaeude_2_e959f946be.jpg'); background-size:cover; background-position:center;"></div>
            <div style="background-image:url('https://www.unisg.ch/fileadmin/_processed_/d/2/csm_HSG_SQUARE_1_43e4002cea.jpg'); background-size:cover; background-position:center;"></div>
            <div style="background-image:url('https://www.unisg.ch/fileadmin/_processed_/3/c/csm_HSG_SQUARE_2_2426171a5d.jpg'); background-size:cover; background-position:center;"></div>
          </div>
          <div style="position:absolute; bottom:12px; left:12px; 
                      background: rgba(0,0,0,0.65); color:#fff; padding:12px 18px; border-radius: 8px; 
                      font-weight: 700; font-size: 24px; backdrop-filter: blur(4px);">
            🎯 UnisportAI
          </div>
          <div style="position:absolute; bottom:12px; right:12px; 
                      background: rgba(0,0,0,0.55); color:#fff; padding:6px 12px; border-radius: 6px; 
                      font-size: 12px; backdrop-filter: blur(4px);">
            © Universität St.Gallen (HSG)
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Main title with modern styling
    st.title("🎯 Welcome to UnisportAI")
    st.caption("Discover and manage sports activities at the University of St.Gallen")
    
    st.divider()
    
    # Feature highlights in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏃 What We Offer")
        st.markdown("""
        - **📅 Complete Overview** - All courses and dates in one place
        - **⭐ Rating System** - Review courses and trainers
        - **❤️ Personal Favorites** - Save your preferred activities
        """)
    
    with col2:
        st.markdown("### ✨ Smart Features")
        st.markdown("""
        - **🔍 Advanced Filters** - Find exactly what you need
        - **📆 Calendar Integration** - Sync with your calendar
        - **👥 Social Connection** - Connect with other athletes
        """)
    
    st.divider()
    
    # Login section with clean card design
    st.markdown("### 🔐 Get Started")
    st.caption("Sign in with your Google account - no password needed!")
    
    # Login button with prominent styling
    login_button = st.button(
        "🔵 Sign in with Google",
        on_click=st.login, 
        args=["google"], 
        use_container_width=True, 
        type="primary",
        key="google_login_button"
    )
    
    st.divider()
    
    # Security and privacy info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("🔒 Your data is processed securely and used only for this application")
    
    with col2:
        if st.button("📄 Privacy Policy", use_container_width=True):
            st.info("View our privacy policy for details on data handling")
    
    # Debug information (only if needed)
    if st.secrets.get("auth", {}).get("google", {}).get("client_id") == "YOUR_GOOGLE_CLIENT_ID_HERE":
        with st.expander("⚠️ Developer Setup Required", expanded=False):
            st.warning("**Google OAuth Configuration Needed**")
            st.markdown("""
            1. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/)
            2. Add these redirect URIs:
               - Local: `http://localhost:8501/oauth2callback`
               - Production: `https://unisportai.streamlit.app/oauth2callback`
            3. Update `.streamlit/secrets.toml` with your credentials
            """)


def get_user_sub():
    """Gibt die eindeutige Benutzer-ID zurück (sub-Claim aus OIDC Token)"""
    if is_logged_in():
        return st.user.sub
    return None


def get_user_email():
    """Gibt die E-Mail-Adresse des eingeloggten Benutzers zurück"""
    if is_logged_in():
        return st.user.email
    return None


def check_token_expiry():
    """Prüft ob der Token abgelaufen ist und leitet zum Logout um"""
    if not is_logged_in():
        return
    
    # Prüfe ob exp-Claim vorhanden und abgelaufen
    try:
        # Extrahiere expires_at aus user object falls verfügbar
        if hasattr(st.user, 'expires_at') and st.user.expires_at:
            if datetime.now(timezone.utc) > st.user.expires_at:
                st.warning("Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.")
                handle_logout()
    except Exception as e:
        st.error(f"Fehler beim Prüfen des Tokens: {e}")


def render_user_menu():
    """Rendert das Benutzermenü in der Sidebar"""
    if is_logged_in():
        # Add spacing to push user menu to bottom
        st.sidebar.markdown("<br>" * 3, unsafe_allow_html=True)
        
        with st.sidebar:
            # User info section with card-like design
            st.markdown(
                f"""
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
                        {st.user.name}
                    </div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 13px;">
                        {st.user.email}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Action buttons with icons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Profile", use_container_width=True, key="profile_btn"):
                    st.switch_page("pages/profile.py")
            
            with col2:
                if st.button("🚪 Logout", use_container_width=True, key="logout_btn", type="secondary"):
                    handle_logout()


def get_user_info_dict():
    """Gibt die vollständigen Benutzerinformationen als Dictionary zurück"""
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
    """Syncs the current authenticated user to Supabase"""
    from data.supabase_client import create_or_update_user
    
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