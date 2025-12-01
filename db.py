"""Supabase data access layer for UnisportAI.

This module centralizes all database access operations used by the Streamlit
application and higher-level service modules.

It exposes **thin, well-defined primitives** for:
- loading sports offers and events (views: ``vw_offers_complete``, ``vw_termine_full``)
- reading and updating user profiles and preferences (tables/views: ``users``, ``vw_user_social_stats``)
- managing favorites, social graph (friends / requests) and event registrations
- storing and querying ratings (``sportangebote_user_ratings``, ``trainer_user_ratings``)
- loading ML training data for the recommendation model (``ml_training_data``)

Most read functions use ``st.cache_data`` or ``st.cache_resource`` to reduce
repeated network calls and improve UI responsiveness. Application code
(``streamlit_app.py`` and service modules) should **only talk to
Supabase through this module**.

Implementation notes:
- Functions must avoid side effects beyond database reads/writes.
- Keep this layer free of UI logic; any Streamlit UI belongs in ``streamlit_app.py``
  or service modules.
- Caching decorators are tuned for typical UI patterns (short TTLs) and can be
  adjusted if usage patterns change.
"""

import streamlit as st
import json
from datetime import datetime
from collections import defaultdict
from typing import Optional, Dict, List, Any
from st_supabase_connection import SupabaseConnection
import logging

# Setup logging
logger = logging.getLogger(__name__)

@st.cache_resource
def supaconn():
    """Return a cached Supabase connection for all DB calls.

    Uses ``@st.cache_resource`` so that a single connection object is reused
    across all function calls and page reruns. This avoids creating a new
    database connection on every user interaction.

    The connection configuration is automatically read from
    ``st.secrets['connections']['supabase']``.

    Used by:
        - every function in this module that needs to talk to Supabase
        - service modules indirectly through the high-level helpers here
    """
    conn = st.connection("supabase", type=SupabaseConnection)
    return conn

def _parse_trainers_json(trainers_data):
    """Converts trainer data from JSON to Python list"""
    if isinstance(trainers_data, str):
        try:
            return json.loads(trainers_data)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse trainers JSON: {trainers_data}")
            return []
    return trainers_data if trainers_data else []

def _convert_event_fields(event):
    """Converts trainer data from view into expected format.
    
    The database view returns trainers as JSON, but the UI expects
    separate lists of names and ratings. This helper transforms the data.
    """
    # Parse JSON string to Python list of trainer dicts
    trainers = _parse_trainers_json(event.get('trainers', []))
    
    # Extract separate lists for names and ratings (UI requirement)
    event['trainers'] = [t['name'] for t in trainers if 'name' in t]
    event['trainer_ratings'] = [t.get('rating', 'N/A') for t in trainers]
    
    # Normalize field names (view uses 'kurs_details', UI expects 'details')
    if 'kurs_details' in event:
        event['details'] = event['kurs_details']
    
    return event

# === Sports Offers & Events ===

# === User Management ===

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a minimal public user profile by internal user UUID.

    Returns name, picture, email, bio and created_at for display purposes.

    Used by:
        - profile and social views in ``streamlit_app.py`` when resolving
          a user ID to display metadata.
    """
    try:
        conn = supaconn()
        result = conn.table("users").select("name, picture, email, bio, created_at").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None

def create_or_update_user(user_data: dict):
    """Create or update a user row in ``users`` based on OIDC ``sub``.

    This function implements "upsert" logic: if a user with the same ``sub``
    already exists, we update the record with latest profile information
    (e.g. name, picture, last_login). Otherwise we create a new record.

    Used by:
        - ``auth.sync_user_to_supabase`` during login to keep
          the application database in sync with Streamlit's user object.
    """
    try:
        conn = supaconn()
        
        user_sub = user_data.get('sub')
        if not user_sub:
            logger.warning("Attempted to create/update user without sub")
            return None
        
        # Check if user already exists in database
        existing = conn.table("users").select("*").eq("sub", user_sub).execute()
        
        if existing.data:
            # User exists - update with latest info (e.g. profile picture, last_login)
            result = conn.table("users").update(user_data).eq("sub", user_sub).execute()
        else:
            # New user - create fresh record
            result = conn.table("users").insert(user_data).execute()
        
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        return None

def get_user_id_by_sub(user_sub: str) -> Optional[int]:
    """Resolve the internal user UUID for a given OIDC ``sub``.

    Convenience helper used anywhere we only know the logged-in subject
    (``st.user.sub``) but need the database primary key.
    """
    try:
        conn = supaconn()
        result = conn.table("users").select("id").eq("sub", user_sub).execute()
        return result.data[0]['id'] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user ID for {user_sub}: {e}")
        return None

def save_filter_preferences(user_sub: str, intensities: list, focus: list, 
                           settings: list, locations: list, weekdays: list) -> bool:
    """Persist sidebar filter preferences on the ``users`` table.

    The function maps human-readable weekday names from the UI to enum codes
    and stores all preference lists in dedicated array columns on ``users``.

    Used by:
        - ``user.save_sidebar_preferences`` which is called from
          the Streamlit sidebar when the user chooses to save defaults.
    """
    try:
        # Map weekdays to codes
        en_to_code = {
            'Monday': 'mon', 'Tuesday': 'tue', 'Wednesday': 'wed',
            'Thursday': 'thu', 'Friday': 'fri', 'Saturday': 'sat', 'Sunday': 'sun',
        }
        weekday_codes = [en_to_code.get(w, w) for w in (weekdays or [])]
        
        conn = supaconn()
        conn.table("users").update({
            "preferred_intensities": intensities or None,
            "preferred_focus": focus or None,
            "preferred_settings": settings or None,
            "favorite_location_names": locations or None,
            "preferred_weekdays": weekday_codes,
            "updated_at": datetime.now().isoformat(),
        }).eq("sub", user_sub).execute()
        return True
    except Exception as e:
        logger.error(f"Error saving filter preferences for {user_sub}: {e}")
        return False

# === User Favorites ===

@st.cache_data(ttl=60)
def get_user_favorites(user_sub: str) -> List[str]:
    """Return all sport offer hrefs the user has marked as favorite.

    This looks up the internal user ID from ``users`` and then queries the
    ``user_favorites`` junction table. The result is a list of
    ``sportangebote.href`` values.

    Used by:
        - ``user.get_user_favorites`` for UI consumption.
    """
    try:
        conn = supaconn()
        user = conn.table("users").select("id").eq("sub", user_sub).execute()
        
        if not user.data:
            return []
        
        user_id = user.data[0]['id']
        favorites = conn.table("user_favorites").select("sportangebot_href").eq("user_id", user_id).execute()
        return [fav['sportangebot_href'] for fav in favorites.data]
    except Exception as e:
        logger.error(f"Error fetching favorites for {user_sub}: {e}")
        return []

def update_user_favorites(user_sub: str, favorite_hrefs: List[str]) -> bool:
    """Replace the complete set of a user's favorite sports.

    Implementation details:
        - resolves ``user_id`` from the given ``user_sub``
        - deletes *all* existing rows in ``user_favorites`` for this user
        - inserts a row per new favorite href (if any)

    Used by:
        - ``user.update_user_favorites`` which is triggered when
          the user updates favorites in the UI.
    """
    try:
        conn = supaconn()
        user = conn.table("users").select("id").eq("sub", user_sub).execute()
        
        if not user.data:
            return False
        
        user_id = user.data[0]['id']
        
        # Delete existing favorites
        conn.table("user_favorites").delete().eq("user_id", user_id).execute()
        
        # Insert new favorites
        if favorite_hrefs:
            favorites_data = [
                {"user_id": user_id, "sportangebot_href": href}
                for href in favorite_hrefs
            ]
            conn.table("user_favorites").insert(favorites_data).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error updating favorites for {user_sub}: {e}")
        return False

# === Ratings ===

# === Friends & Social ===

@st.cache_data(ttl=120)
def get_public_users() -> List[Dict]:
    """Return all user profiles that are marked as public.

    Used to populate the social discovery / \"Athletes\" views where only users
    with ``is_public = True`` should be visible.
    """
    try:
        conn = supaconn()
        result = conn.table("users").select(
            "id, name, email, picture, bio, created_at"
        ).eq("is_public", True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Error fetching public users: {e}")
        return []

def get_friend_status(user_id: int, other_user_id: int) -> str:
    """Return friendship status between two users.

    Possible return values:
        - ``\"friends\"``          – there is a row in ``user_friends``
        - ``\"request_sent\"``     – current user has sent a pending request
        - ``\"request_received\"`` – current user has a pending incoming request
        - ``\"none\"``             – no relation yet

    Used by:
        - profile and social components in ``streamlit_app.py`` to decide
          which action button to show (add friend / accept / remove).
    """
    try:
        conn = supaconn()
        
        # Check if already friends (single query with OR)
        friendship = conn.table("user_friends").select("*").or_(
            f"and(requester_id.eq.{user_id},addressee_id.eq.{other_user_id}),and(requester_id.eq.{other_user_id},addressee_id.eq.{user_id})"
        ).limit(1).execute()
        
        if friendship.data:
            return "friends"
        
        # Check for pending request sent
        request_sent = conn.table("friend_requests").select("id").eq(
            "requester_id", user_id
        ).eq("addressee_id", other_user_id).eq("status", "pending").limit(1).execute()
        
        if request_sent.data:
            return "request_sent"
        
        # Check for pending request received
        request_received = conn.table("friend_requests").select("id").eq(
            "requester_id", other_user_id
        ).eq("addressee_id", user_id).eq("status", "pending").limit(1).execute()
        
        if request_received.data:
            return "request_received"
        
        return "none"
    except Exception as e:
        logger.error(f"Error checking friend status: {e}")
        return "none"

def send_friend_request(requester_id: int, addressee_id: int) -> bool:
    """Create a friend request if none is pending yet.

    Enforces that there is at most one pending request from A to B at a time.
    Existing non-pending requests (accepted / rejected) are left untouched.
    """
    try:
        conn = supaconn()
        
        # Check if request already exists
        existing = conn.table("friend_requests").select("id, status").eq(
            "requester_id", requester_id
        ).eq("addressee_id", addressee_id).limit(1).execute()
        
        if existing.data:
            if existing.data[0]['status'] == 'pending':
                return False
        else:
            timestamp = datetime.now().isoformat()
            conn.table("friend_requests").insert({
                "requester_id": requester_id,
                "addressee_id": addressee_id,
                "status": "pending",
                "created_at": timestamp,
                "updated_at": timestamp
            }).execute()
            
            return True
    except Exception as e:
        logger.error(f"Error sending friend request: {e}")
        return False

def accept_friend_request(request_id: str, requester_id: int, addressee_id: int) -> bool:
    """Accepts a friend request and creates bidirectional friendship.
    
    When User A accepts User B's request, we create TWO friendship records:
    - A -> B friendship
    - B -> A friendship
    This bidirectional approach simplifies queries (no need to check both directions).
    """
    try:
        conn = supaconn()
        
        timestamp = datetime.now().isoformat()
        
        # Mark the friend request as accepted in database
        conn.table("friend_requests").update({
            "status": "accepted",
            "updated_at": timestamp
        }).eq("id", request_id).execute()
        
        # Create TWO friendship records (one in each direction)
        # This makes it easy to query "all friends" without complex OR conditions
        conn.table("user_friends").insert([
            {
                "requester_id": requester_id,
                "addressee_id": addressee_id,
                "created_at": timestamp
            },
            {
                "requester_id": addressee_id,
                "addressee_id": requester_id,
                "created_at": timestamp
            }
        ]).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error accepting friend request: {e}")
        return False

def reject_friend_request(request_id: str) -> bool:
    """Reject a friend request without creating a friendship."""
    try:
        conn = supaconn()
        conn.table("friend_requests").update({
            "status": "rejected",
            "updated_at": datetime.now().isoformat()
        }).eq("id", request_id).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error rejecting friend request: {e}")
        return False

def unfollow_user(user_id: int, friend_id: int) -> bool:
    """Remove a friendship in both directions for two users."""
    try:
        conn = supaconn()
        
        # Delete friendship in both directions with single query
        conn.table("user_friends").delete().or_(
            f"and(requester_id.eq.{user_id},addressee_id.eq.{friend_id}),and(requester_id.eq.{friend_id},addressee_id.eq.{user_id})"
        ).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error unfollowing user: {e}")
        return False

@st.cache_data(ttl=60)
def get_pending_friend_requests(user_id: int) -> List[Dict]:
    """Return all pending friend requests where the user is the addressee.

    Includes joined requester / addressee user details for convenient display
    in the UI.
    """
    try:
        conn = supaconn()
        result = conn.table("friend_requests").select(
            "*, requester:users!requester_id(*), addressee:users!addressee_id(*)"
        ).eq("addressee_id", user_id).eq("status", "pending").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Error fetching pending friend requests: {e}")
        return []

@st.cache_data(ttl=60)
def get_user_friends(user_id: int) -> List[Dict]:
    """Return a list of the user's friends with basic profile information.

    Internally joins ``user_friends`` with ``users`` and normalises the
    direction so the caller always receives the *other* user as a plain dict.
    """
    try:
        conn = supaconn()
        
        friendships = conn.table("user_friends").select(
            "*, requester:users!requester_id(*), addressee:users!addressee_id(*)"
        ).or_(f"requester_id.eq.{user_id},addressee_id.eq.{user_id}").execute()
        
        friends = []
        for friendship in friendships.data or []:
            if friendship['requester_id'] == user_id:
                friend = friendship.get('addressee')
            else:
                friend = friendship.get('requester')
            
            if friend:
                friends.append(friend)
        
        return friends
    except Exception as e:
        logger.error(f"Error fetching user friends: {e}")
        return []

# === Rating Queries ===

@st.cache_data(ttl=60)
def get_user_sport_rating(user_sub: str, sportangebot_href: str) -> Optional[Dict]:
    """Return the current user's rating record for a given sport, if any.

    Looked up by ``sub`` (to resolve ``user_id``) and ``sportangebot_href``.
    Used by the rating widgets to pre-populate sliders and comments.
    """
    try:
        conn = supaconn()
        user = conn.table("users").select("id").eq("sub", user_sub).execute()
        if not user.data:
            return None
        
        user_id = user.data[0]['id']
        existing = conn.table("sportangebote_user_ratings").select("*").eq(
            "user_id", user_id
        ).eq("sportangebot_href", sportangebot_href).execute()
        
        return existing.data[0] if existing.data else None
    except Exception as e:
        logger.error(f"Error fetching user sport rating: {e}")
        return None

@st.cache_data(ttl=60)
def get_user_trainer_rating(user_sub: str, trainer_name: str) -> Optional[Dict]:
    """Return the current user's rating record for a given trainer, if any."""
    try:
        conn = supaconn()
        user = conn.table("users").select("id").eq("sub", user_sub).execute()
        if not user.data:
            return None
        
        user_id = user.data[0]['id']
        existing = conn.table("trainer_user_ratings").select("*").eq(
            "user_id", user_id
        ).eq("trainer_name", trainer_name).execute()
        
        return existing.data[0] if existing.data else None
    except Exception as e:
        logger.error(f"Error fetching user trainer rating: {e}")
        return None

@st.cache_data(ttl=120)
def get_average_rating_for_offer(offer_href: str) -> Dict[str, float]:
    """Compute the average rating and count for a sport offer.

    Returns a dict of the shape ``{\"avg\": float, \"count\": int}``. If no
    ratings exist, the function returns ``{\"avg\": 0, \"count\": 0}``.
    """
    try:
        conn = supaconn()
        ratings = conn.table("sportangebote_user_ratings").select("rating").eq(
            "sportangebot_href", offer_href
        ).execute()
        
        if not ratings.data:
            return {"avg": 0, "count": 0}
        
        avg_rating = sum(r['rating'] for r in ratings.data) / len(ratings.data)
        return {"avg": round(avg_rating, 1), "count": len(ratings.data)}
    except Exception as e:
        logger.error(f"Error fetching average rating for offer: {e}")
        return {"avg": 0, "count": 0}

@st.cache_data(ttl=120)
def get_average_rating_for_trainer(trainer_name: str) -> Dict[str, float]:
    """Compute the average rating and count for a trainer.

    Returns a dict of the shape ``{\"avg\": float, \"count\": int}``. If no
    ratings exist, a default average of 3 with count 0 is returned.
    """
    try:
        conn = supaconn()
        ratings = conn.table("trainer_user_ratings").select("rating").eq(
            "trainer_name", trainer_name
        ).execute()
        
        if not ratings.data:
            return {"avg": 3, "count": 0}  # Default rating
        
        avg_rating = sum(r['rating'] for r in ratings.data) / len(ratings.data)
        return {"avg": round(avg_rating, 1), "count": len(ratings.data)}
    except Exception as e:
        logger.error(f"Error fetching average rating for trainer: {e}")
        return {"avg": 3, "count": 0}


# === Machine Learning Data ===

@st.cache_data(ttl=3600)  # Cache for 1 hour - training data doesn't change often
def get_ml_training_data():
    """Load ML training data for sport recommendations (Streamlit apps).

    Reads from the ``ml_training_data`` view which contains feature vectors
    for each sport. This data is consumed by the KNN recommender inside
    ``streamlit_app.py`` to find similar sports based on user preferences.

    Note:
        For CLI scripts (``ml/train.py``, ``ml/test.py``), use
        :func:`get_ml_training_data_cli` instead so they can run without
        Streamlit.

    Returns:
        List of dicts with sport features (balance, flexibility, etc.).
    """
    try:
        conn = supaconn()
        result = conn.table("ml_training_data").select("*").execute()
        
        if not result.data:
            logger.warning("No data found in ml_training_data view")
            return []
        
        logger.info(f"Loaded {len(result.data)} sports for ML training")
        return result.data
    except Exception as e:
        logger.error(f"Error fetching ML training data: {e}")
        return []


def get_ml_training_data_cli():
    """Load ML training data for CLI scripts (without Streamlit).

    This function bypasses Streamlit caching and uses a direct Supabase
    client created from ``SUPABASE_URL`` and ``SUPABASE_KEY`` in ``.env``.

    Use this in:
        - ``ml/train.py``
        - ``ml/test.py``
        - other standalone scripts that need the same feature matrix.

    Returns:
        List of dicts with sport features (balance, flexibility, etc.).
    """
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    from pathlib import Path
    
    # Load environment variables
    script_dir = Path(__file__).parent.absolute()
    env_path = script_dir.parents[1] / '.env'
    load_dotenv(dotenv_path=env_path)
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    supabase = create_client(supabase_url, supabase_key)
    response = supabase.table("ml_training_data").select("*").execute()
    
    if not response.data:
        raise ValueError("No data found in ml_training_data view")
    
    return response.data


def get_supabase_client():
    """Return the underlying Supabase connection for advanced operations.

    This is intentionally a low-level escape hatch and should only be used
    where there is no suitable helper function in this module yet.
    """
    conn = supaconn()
    return conn


# =============================================================================
# SIMPLIFIED API - New unified functions that replace multiple old functions
# =============================================================================

@st.cache_data(ttl=300)
def get_offers_complete():
    """Load *all* offer data from the ``vw_offers_complete`` view.

    The unified view contains:
        - all offer fields (name, href, icon, description, intensity, focus, setting)
        - aggregated rating statistics (``avg_rating``, ``rating_count``)
        - aggregated event statistics (``future_events_count``, ``total_events_count``,
          ``has_upcoming_events``)
        - an aggregated trainers list (JSON array with names and ratings)

    It replaces older, more granular helpers such as:
        - ``get_offers_with_stats``
        - ``count_upcoming_events_per_offer``
        - ``get_trainers_for_all_offers``

    Used by:
        - the main overview and recommendation views in ``streamlit_app.py``.

    Returns:
        List of dicts with complete offer data including aggregations.
    """
    try:
        conn = supaconn()
        result = conn.table("vw_offers_complete").select("*").order("avg_rating", desc=True).order("name").execute()
        
        # Filter out non-sports (like locker rentals) that have no sports features
        filtered_offers = []
        for offer in result.data:
            has_focus = offer.get('focus') and len([f for f in offer.get('focus', []) if f and f.strip()])
            has_setting = offer.get('setting') and len([s for s in offer.get('setting', []) if s and s.strip()])
            has_intensity = offer.get('intensity') and offer.get('intensity').strip()
            
            if has_focus or has_setting or has_intensity:
                filtered_offers.append(offer)
            else:
                logger.info(f"Filtering out offer without features: {offer.get('name', 'Unknown')}")
        
        logger.info(f"Loaded {len(filtered_offers)} offers with features from vw_offers_complete")
        return filtered_offers
    except Exception as e:
        logger.error(f"Error fetching offers from vw_offers_complete: {e}")
        st.error("Failed to load sport offers")
        return []


@st.cache_data(ttl=300)
def get_events(offer_href: Optional[str] = None):
    """Load future events from the ``vw_termine_full`` view.

    If ``offer_href`` is provided, events are filtered to that specific offer;
    otherwise all upcoming events (``start_time >= now()``) are returned.

    This replaces:
        - ``get_all_events()``
        - ``get_events_for_offer()``

    Used by:
        - the timetable/event views in ``streamlit_app.py``.

    Args:
        offer_href: Optional offer href to filter by. If ``None``, return all events.

    Returns:
        List of event dicts with full details (trainers, location, etc.).
    """
    try:
        conn = supaconn()
        now = datetime.now().isoformat()
        
        query = conn.table("vw_termine_full").select("*").gte("start_time", now).order("start_time")
        
        if offer_href:
            query = query.eq("offer_href", offer_href)
        
        events_result = query.execute()
        events = events_result.data
        
        # Convert trainer data format for UI compatibility
        return [_convert_event_fields(event) for event in events]
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        st.error("Failed to load events")
        return []


@st.cache_data(ttl=60)
def get_user_complete(user_sub: str) -> Optional[Dict[str, Any]]:
    """Load complete user profile plus social statistics.

    Data source:
        - the ``vw_user_social_stats`` view, which joins ``users`` with
          ``user_friends`` and ``friend_requests``.

    The view exposes:
        - all user fields used by the UI (id, sub, name, email, picture, bio,
          preferences, visibility, preference arrays, etc.)
        - aggregated social statistics (``friend_count``,
          ``pending_requests_count``)

    It replaces older helpers such as:
        - ``get_user_from_db()``
        - ``get_user_profile()``
        - ``get_friend_count()``

    Args:
        user_sub: User's OIDC ``sub`` claim.

    Returns:
        Dict with complete user data including social stats, or ``None`` if not found.
    """
    try:
        conn = supaconn()
        result = conn.table("vw_user_social_stats").select("*").eq("sub", user_sub).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error loading user profile for {user_sub}: {e}")
        return None


def update_user_settings(user_sub: str, bio: Optional[str] = None, 
                        preferences: Optional[Dict[str, Any]] = None,
                        visibility: Optional[bool] = None) -> bool:
    """Unified function to update user settings (bio, preferences, visibility).

    This helper writes to the ``users`` table and updates only the provided
    fields, plus an ``updated_at`` timestamp. It replaces multiple, more
    granular update functions.

    Args:
        user_sub: User's OIDC ``sub`` claim.
        bio: New bio text (if provided).
        preferences: New preferences dict (if provided, stored as JSON).
        visibility: New public visibility setting (if provided).

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    try:
        conn = supaconn()
        
        # Build update dict with only provided fields
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if bio is not None:
            update_data["bio"] = bio
        
        if preferences is not None:
            update_data["preferences"] = json.dumps(preferences)
        
        if visibility is not None:
            update_data["is_public"] = visibility
        
        conn.table("users").update(update_data).eq("sub", user_sub).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating user settings for {user_sub}: {e}")
        return False


def submit_rating(user_sub: str, target_type: str, target_id: str, 
                 rating: int, comment: str = "") -> bool:
    """Unified function to submit ratings for sports *or* trainers.

    Internally this writes to either ``sportangebote_user_ratings`` or
    ``trainer_user_ratings`` depending on ``target_type``. Existing ratings
    for the same (user, target) pair are updated in-place; otherwise a new
    row is inserted.

    Replaces:
        - ``submit_sport_rating()``
        - ``submit_trainer_rating()``

    Args:
        user_sub: User's OIDC ``sub`` claim.
        target_type: Either ``\"sport\"`` or ``\"trainer\"``.
        target_id: Sport href or trainer name (depending on ``target_type``).
        rating: Rating value (1–5).
        comment: Optional free-text comment.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    try:
        conn = supaconn()
        
        # Get user_id
        user = conn.table("users").select("id").eq("sub", user_sub).execute()
        if not user.data:
            logger.warning(f"User not found for sub {user_sub}")
            return False
        
        user_id = user.data[0]['id']
        
        # Determine table and fields based on target_type
        if target_type == "sport":
            table_name = "sportangebote_user_ratings"
            id_field = "sportangebot_href"
        elif target_type == "trainer":
            table_name = "trainer_user_ratings"
            id_field = "trainer_name"
        else:
            logger.error(f"Invalid target_type: {target_type}")
            return False
        
        # Check for existing rating
        existing = conn.table(table_name).select("*").eq(
            "user_id", user_id
        ).eq(id_field, target_id).execute()
        
        rating_data = {
            "user_id": user_id,
            id_field: target_id,
            "rating": rating,
            "comment": comment,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing.data:
            # Update existing rating
            conn.table(table_name).update(rating_data).eq(
                "user_id", user_id
            ).eq(id_field, target_id).execute()
        else:
            # Insert new rating
            rating_data["created_at"] = datetime.now().isoformat()
            conn.table(table_name).insert(rating_data).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error submitting {target_type} rating: {e}")
        return False
