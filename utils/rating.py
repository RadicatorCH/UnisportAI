"""Rating widgets for sport offers and trainers.

This module provides Streamlit UI helpers to render rating widgets for
offers and trainers, read existing user ratings and submit updates via
the database layer (utils.db). Everything is kept in one file to
demonstrate a clear UI → business logic → database flow.

WHAT IS THIS MODULE FOR?
-------------------------
This module creates the UI components (widgets) that allow users to rate
sports and trainers. It handles:
- Displaying existing ratings
- Providing input controls (sliders, text areas)
- Submitting new or updated ratings
- Showing success/error messages

STREAMLIT CONCEPT - Widgets:
---------------------------
In Streamlit, "widgets" are interactive UI elements like:
- st.slider() - for selecting a number
- st.text_area() - for entering text
- st.button() - for triggering actions
- st.expander() - for collapsible sections

This module creates complete rating widgets by combining these basic
Streamlit components.

ARCHITECTURE:
------------
These functions are UI-only - they don't directly access the database.
Instead, they call functions from utils.db.py via helpers in this module,
keeping UI code separate from business logic.

EXAMPLE USAGE:
-------------
```python
# In your Streamlit app:
render_sportangebot_rating_widget("yoga-basics")
render_trainer_rating_widget("John Smith")
```

This will display expandable sections where users can rate and comment.
"""
import streamlit as st
from utils.auth import get_user_sub
from utils.db import (
    get_user_sport_rating,
    get_user_trainer_rating,
    get_average_rating_for_offer,
    get_average_rating_for_trainer,
    submit_rating as db_submit_rating
)

def submit_sportangebot_rating(sportangebot_href, rating, comment=""):
    """
    Save or update a user's rating for a sport offer.
    
    Allows users to rate sports (1-5 stars) and optionally leave a comment.
    The rating is saved to the database and can be displayed to other users
    as an average rating.
    
    How ratings work:
    - Each user can rate each sport once
    - If they rate again, it updates their existing rating
    - Ratings are aggregated to show average ratings to all users
    - Comments are optional and stored with the rating
    
    Example:
    ```python
    # User rates a sport:
    if submit_sportangebot_rating("yoga-basics", 5, "Great class!"):
        st.success("Rating saved!")
    else:
        st.error("Failed to save rating")
    ```
    
    How it works:
    1. Get the current user's ID
    2. Validate rating is between 1 and 5
    3. Call database function to save/update rating
    4. Return True if successful
    
    Args:
        sportangebot_href: Unique identifier for the sport offer
        rating: Rating value (must be 1, 2, 3, 4, or 5)
        comment: Optional text comment about the sport
    
    Returns:
        True if rating was saved successfully, False otherwise
    
    Note:
        This uses the unified submit_rating function from db.py which handles
        both creating new ratings and updating existing ones automatically.
        The rating range is validated here (UI layer) so that the database layer
        can stay agnostic about UI wording.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    try:
        # Basic validation
        is_int = isinstance(rating, int)
        is_too_low = rating < 1
        is_too_high = rating > 5
        if not is_int or is_too_low or is_too_high:
            st.error("Ungültige Bewertung (1-5)")
            return False
        
        result = db_submit_rating(user_sub, "sport", sportangebot_href, rating, comment)
        return result
    except Exception as e:
        error_message = str(e)
        st.error(f"Fehler beim Speichern der Bewertung: {error_message}")
        return False

def submit_trainer_rating(trainer_name, rating, comment=""):
    """
    Save or update a user's rating for a trainer.
    
    Similar to submit_sportangebot_rating, but for trainers instead of sports.
    Users can rate individual trainers (instructors) who teach the courses.
    
    Example:
    ```python
    # User rates a trainer:
    if submit_trainer_rating("John Smith", 4, "Very knowledgeable"):
        st.success("Trainer rating saved!")
    ```
    
    Args:
        trainer_name: The trainer's display name (used as identifier)
        rating: Rating value (must be 1, 2, 3, 4, or 5)
        comment: Optional text comment about the trainer
    
    Returns:
        True if rating was saved successfully, False otherwise
    
    Note:
        Trainers are identified by name, not by a unique ID. Make sure trainer
        names are consistent in the database. The DB schema uses trainer names
        as identifiers, which is a trade-off between easy UI and potential duplicates.
    """
    user_sub = get_user_sub()
    if not user_sub:
        return False
    
    try:
        # Basic validation
        is_int = isinstance(rating, int)
        is_too_low = rating < 1
        is_too_high = rating > 5
        if not is_int or is_too_low or is_too_high:
            st.error("Ungültige Bewertung (1-5)")
            return False
        
        result = db_submit_rating(user_sub, "trainer", trainer_name, rating, comment)
        return result
    except Exception as e:
        error_message = str(e)
        st.error(f"Fehler beim Speichern der Bewertung: {error_message}")
        return False

def render_sportangebot_rating_widget(offer_href):
    """
    Create and display a complete rating widget for a sport offer.
    
    Creates a Streamlit UI component that allows users to:
    1. See their existing rating (if they've rated before)
    2. Select a new rating (1-5 stars using a slider)
    3. Add an optional comment
    4. Save the rating
    
    How it works:
    1. Check if user is logged in (no rating if not logged in)
    2. Load existing rating from database (if user has rated before)
    3. Display an expandable section (st.expander) with:
       - Current rating display (if exists)
       - Rating slider (1-5)
       - Comment text area
       - Save button
    4. When user clicks save, call submit_sportangebot_rating()
    5. Show success message and refresh page
    
    Streamlit concepts used:
    - st.expander(): Creates a collapsible section (click to expand/collapse)
    - st.slider(): Lets user select a number (1-5 for rating)
    - st.text_area(): Multi-line text input for comments
    - st.button(): Triggers an action when clicked
    - st.rerun(): Refreshes the page to show updated data
    
    Example:
    ```python
    # Display rating widget for a sport:
    render_sportangebot_rating_widget("yoga-basics")
    
    # This creates a UI that looks like:
    # ⭐ Bewerten Sie dieses Sportangebot [expandable]
    #   [If user has rated before: shows current rating]
    #   Rating: [slider 1 5]
    #   Comment: [text area]
    #   [Save Rating button]
    ```
    
    Args:
        offer_href: Unique identifier for the sport offer (e.g., "yoga-basics")
    
    Returns:
        None: This function doesn't return anything - it directly modifies
            the Streamlit UI by rendering widgets
    
    Note:
        The widget only appears if the user is logged in. If not logged in,
        the function returns early and nothing is displayed.
    """
    from utils.auth import is_logged_in
    if not is_logged_in():
        return None
    
    user_sub = get_user_sub()
    if not user_sub:
        return None
    
    try:
        # Get existing rating
        existing_rating = get_user_sport_rating(user_sub, offer_href)
        
        with st.expander("⭐ Bewerten Sie dieses Sportangebot"):
            # Rating stars
            if existing_rating:
                current_rating = existing_rating.get('rating', 3)
                current_comment = existing_rating.get('comment', '')
                # Build star string
                stars = '⭐' * current_rating
                rating_text = f"Ihre aktuelle Bewertung: {stars} ({current_rating}/5)"
                st.info(rating_text)
            else:
                current_rating = 3
                current_comment = ''
            
            slider_key = f"rating_slider_{offer_href}"
            rating = st.slider("Bewertung", 1, 5, current_rating, help="1 = Schlecht, 5 = Ausgezeichnet", key=slider_key)
            
            comment_key = f"rating_comment_{offer_href}"
            comment = st.text_area("Kommentar (optional)", value=current_comment, placeholder="Teilen Sie Ihre Erfahrungen mit...", key=comment_key)
            
            save_key = f"save_rating_{offer_href}"
            if st.button("Bewertung speichern", key=save_key):
                success = submit_sportangebot_rating(offer_href, rating, comment)
                if success:
                    st.success("✅ Bewertung wurde gespeichert!")
                    st.rerun()
                else:
                    st.error("Fehler beim Speichern der Bewertung")
    except Exception as e:
        error_message = str(e)
        st.error(f"Fehler: {error_message}")
    
    return None

def render_trainer_rating_widget(trainer_name):
    """
    Create and display a complete rating widget for a trainer.
    
    Similar to render_sportangebot_rating_widget, but for rating trainers
    (instructors) instead of sports. The functionality is identical:
    - Show existing rating
    - Allow selecting new rating (1-5)
    - Allow adding comment
    - Save rating
    
    Example:
    ```python
    # Display rating widget for a trainer:
    render_trainer_rating_widget("John Smith")
    ```
    
    Args:
        trainer_name: The trainer's display name (used as identifier)
    
    Returns:
        None: This function doesn't return anything - it directly modifies
            the Streamlit UI by rendering widgets
    
    Note:
        Trainers are identified by name, so make sure trainer names are
        consistent in your database.
    """
    from utils.auth import is_logged_in
    if not is_logged_in():
        return None
    
    user_sub = get_user_sub()
    if not user_sub:
        return None
    
    try:
        # Get existing rating
        existing_rating = get_user_trainer_rating(user_sub, trainer_name)
        
        expander_title = f"⭐ Bewerten Sie Trainer: {trainer_name}"
        with st.expander(expander_title):
            # Rating stars
            if existing_rating:
                current_rating = existing_rating.get('rating', 3)
                current_comment = existing_rating.get('comment', '')
                # Build star string
                stars = '⭐' * current_rating
                rating_text = f"Ihre aktuelle Bewertung: {stars} ({current_rating}/5)"
                st.info(rating_text)
            else:
                current_rating = 3
                current_comment = ''
            
            slider_key = f"trainer_rating_{trainer_name}"
            rating = st.slider("Bewertung", 1, 5, current_rating, help="1 = Schlecht, 5 = Ausgezeichnet", key=slider_key)
            
            comment_key = f"trainer_comment_{trainer_name}"
            comment = st.text_area("Kommentar (optional)", value=current_comment, placeholder="Teilen Sie Ihre Erfahrungen mit...", key=comment_key)
            
            save_key = f"save_trainer_rating_{trainer_name}"
            if st.button("Bewertung speichern", key=save_key):
                success = submit_trainer_rating(trainer_name, rating, comment)
                if success:
                    st.success("✅ Bewertung wurde gespeichert!")
                    st.rerun()
                else:
                    st.error("Fehler beim Speichern der Bewertung")
    except Exception as e:
        error_message = str(e)
        st.error(f"Fehler: {error_message}")
    
    return None
# Parts of this codebase were developed with the assistance of AI-based tools (Cursor and Github Copilot)
# All outputs generated by such systems were reviewed, validated, and modified by the author.
