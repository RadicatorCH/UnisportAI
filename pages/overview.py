"""pages.overview

Streamlit page that lists available sports offers (activities) and their
upcoming events. This overview includes filtering UI provided by the
sidebar, per-offer metadata (trainers, ratings, upcoming event counts),
and an ML-based recommendations section.

The module reads application state and offer/event data from the
``data.state_manager`` and ``data.supabase_client`` modules.
"""

import streamlit as st
from datetime import datetime
from data.supabase_client import get_offers_with_stats, count_upcoming_events_per_offer, get_trainers_for_all_offers, get_events_for_offer, get_events_by_offer_mapping
from data.filters import filter_offers, filter_offers_by_events, filter_events
from data.state_manager import get_filter_state, set_filter_state, set_sports_data, set_selected_offer, get_sports_data
from data.shared_sidebar import render_filters_sidebar, render_ml_recommendations_section
from data.auth import is_logged_in

# Check authentication
if not is_logged_in():
    st.error("❌ Bitte melden Sie sich an.")
    st.stop()

# Get all sports data from database and enrich with computed fields
from data.supabase_client import get_offers_with_stats
offers_data = get_offers_with_stats()

# Enrich offers with event counts
event_counts = count_upcoming_events_per_offer()
trainers_map = get_trainers_for_all_offers()

for offer in offers_data:
    href = offer.get('href')
    # Add quick metadata used by the UI: number of upcoming events and
    # trainer list. This avoids repeated DB calls during rendering.
    offer['future_events_count'] = event_counts.get(href, 0)
    offer['trainers'] = trainers_map.get(href, [])

# Store in state
set_sports_data(offers_data)

# Render sidebar with filters (sets state used by the page)
render_filters_sidebar(sports_data=offers_data, events=None)

# Get filter values from state
search_text = get_filter_state('search_text', '')
selected_intensity = get_filter_state('intensity', [])
selected_focus = get_filter_state('focus', [])
selected_setting = get_filter_state('setting', [])
show_upcoming_only = get_filter_state('show_upcoming_only', True)

# Get additional filter state for event filtering
selected_offers_filter = get_filter_state('offers', [])
selected_weekdays = get_filter_state('weekday', [])
date_start = get_filter_state('date_start', None)
date_end = get_filter_state('date_end', None)
time_start_filter = get_filter_state('start_time', None)
time_end_filter = get_filter_state('end_time', None)
selected_locations = get_filter_state('location', [])
hide_cancelled = get_filter_state('hide_cancelled', True)

# Apply filters to offers_data according to saved sidebar state
offers = filter_offers(
    offers_data,
    show_upcoming_only=show_upcoming_only,
    search_text=search_text,
    intensity=selected_intensity if selected_intensity else None,
    focus=selected_focus if selected_focus else None,
    setting=selected_setting if selected_setting else None
)

# Main content area
st.title("🎯 Sports Overview")
st.write("Discover and book your perfect sports activities")

# Show logic-based filter results
if offers:
    st.subheader(f"📋 Matching Activities ({len(offers)})")
    # Display activities in a clean card layout
    if not offers:
        st.info("🔍 No activities match your filters. Try adjusting your search criteria.")
        st.stop()

    for offer in offers:
        with st.container():
            # Card container
            col_content, col_action = st.columns([4, 1])
            
            with col_content:
                # Header with icon and name
                st.markdown(f"### {offer.get('icon', '🏃')} {offer.get('name', 'Activity')}")
                
                # Metadata row
                metadata = []
                
                # Intensity badge
                intensity_value = offer.get('intensity') or ''
                intensity = intensity_value.capitalize() if intensity_value else ''
                if intensity:
                    color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(intensity, '⚪')
                    metadata.append(f"{color} {intensity}")
                
                # Focus areas
                if offer.get('focus'):
                    focus_list = [f.capitalize() if f else '' for f in offer['focus'][:2] if f]
                    if len(offer['focus']) > 2:
                        focus_list.append(f"+{len(offer['focus']) - 2}")
                    metadata.append(f"🎯 {', '.join(focus_list)}")
                
                # Setting
                if offer.get('setting'):
                    setting_str = ', '.join([s.capitalize() if s else '' for s in offer['setting'][:2] if s])
                    metadata.append(f"🏠 {setting_str}")
                
                # Events count
                events_count = offer.get('future_events_count', 0)
                if events_count > 0:
                    metadata.append(f"📅 {events_count} upcoming")
                else:
                    metadata.append("⏸️ No upcoming dates")
                
                st.caption(' • '.join(metadata))
                
                # Additional info row
                info_row = []
                
                # Trainers
                trainers = offer.get('trainers', [])
                if trainers:
                    trainer_names = [t.get('name', '') for t in trainers[:2]]
                    if len(trainers) > 2:
                        trainer_names.append(f"+{len(trainers)-2}")
                    info_row.append(f"👤 {', '.join(trainer_names)}")
                
                # Rating
                if offer.get('rating_count', 0) > 0:
                    rating = offer.get('avg_rating', 0)
                    stars = '⭐' * int(round(rating))
                    info_row.append(f"{stars} {rating:.1f} ({offer['rating_count']})")
                
                if info_row:
                    st.caption(' • '.join(info_row))
            
            with col_action:
                st.write("")  # Spacing
                if st.button("View Details", key=f"view_{offer['href']}", use_container_width=True, type="primary"):
                    set_selected_offer(offer)
                    st.switch_page("pages/details.py")
            
            # Expandable upcoming dates section
            if events_count > 0:
                with st.expander(f"📅 Show {min(events_count, 10)} upcoming dates", expanded=False):
                    events = get_events_for_offer(offer['href'])
                    
                    # Filter for future events only
                    today = datetime.now().date()
                    upcoming_events = [
                        e for e in events
                        if (datetime.fromisoformat(str(e.get('start_time')).replace('Z', '+00:00')).date() >= today
                            and not e.get('canceled'))
                    ]
                    
                    # Apply detail filters if any are set
                    if selected_offers_filter or selected_weekdays or date_start or date_end or time_start_filter or time_end_filter or selected_locations:
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
                    
                    upcoming_events.sort(key=lambda x: x.get('start_time', ''))
                    
                    if upcoming_events:
                        # Display in clean table format
                        weekdays = {'Monday': 'Mo', 'Tuesday': 'Di', 'Wednesday': 'Mi', 
                                   'Thursday': 'Do', 'Friday': 'Fr', 'Saturday': 'Sa', 'Sunday': 'So'}
                        
                        events_data = []
                        for event in upcoming_events[:10]:
                            start_dt = datetime.fromisoformat(str(event.get('start_time')).replace('Z', '+00:00'))
                            end_time = event.get('end_time')
                            
                            if end_time:
                                end_dt = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
                                time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                            else:
                                time_str = start_dt.strftime('%H:%M')
                            
                            weekday = weekdays.get(start_dt.strftime('%A'), start_dt.strftime('%A'))
                            
                            events_data.append({
                                'Date': f"{weekday}, {start_dt.strftime('%d.%m.%Y')}",
                                'Time': time_str,
                                'Location': event.get('location_name', 'N/A')
                            })
                        
                        st.dataframe(events_data, use_container_width=True, hide_index=True)
                        
                        if len(upcoming_events) > 10:
                            if st.button(f"View all {len(upcoming_events)} dates →", 
                                       key=f"all_{offer['href']}", 
                                       use_container_width=True):
                                set_selected_offer(offer)
                                st.switch_page("pages/details.py")
                    else:
                        st.info("No upcoming dates match your filters")
else:
    st.info("No activities match your selected filters.")

# ML-based recommendations section: uses the ML integration to suggest
# offers based on the user's state and current filtered results.
st.markdown("---")
st.subheader("🤖 AI-Powered Recommendations")

from data.ml_integration import get_ml_recommendations

# Get current filter state for AI recommendations
selected_focus_ai = get_filter_state('focus', [])
selected_intensity_ai = get_filter_state('intensity', [])
selected_setting_ai = get_filter_state('setting', [])

# Check if user has selected any filters
has_filters = bool(selected_focus_ai or selected_intensity_ai or selected_setting_ai)

if not has_filters:
    st.info("💡 **Select some filters in the sidebar to get AI-powered sport recommendations!**")
    st.write("The AI will analyze your preferences and suggest sports that match your interests.")
else:
    # User controls for ML recommendations
    with st.expander("🎛️ AI Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            min_match = st.slider(
                "Minimum Match %",
                min_value=50,
                max_value=100,
                value=75,
                step=5,
                help="Only show sports with at least this match percentage"
            )
        
        with col2:
            max_results = st.slider(
                "Max Results",
                min_value=3,
                max_value=20,
                value=8,
                step=1,
                help="Maximum number of AI recommendations"
            )
    
    # Get sports to exclude (already shown in main results)
    exclude_names = [offer.get('name', '') for offer in offers]
    
    # Get ML recommendations
    with st.spinner("🤖 AI is analyzing your preferences..."):
        ml_recommendations = get_ml_recommendations(
            selected_focus=selected_focus_ai,
            selected_intensity=selected_intensity_ai,
            selected_setting=selected_setting_ai,
            min_match_score=min_match,
            max_results=max_results,
            exclude_sports=exclude_names
        )
    
    # Display results
    if ml_recommendations:
        st.success(f"✨ Found {len(ml_recommendations)} AI recommendations based on your preferences!")
        
        # Display recommendations in a nice grid
        cols = st.columns(2)
        for i, rec in enumerate(ml_recommendations):
            with cols[i % 2]:
                with st.container():
                    # Header with sport name and match score
                    col_name, col_score = st.columns([3, 1])
                    with col_name:
                        st.markdown(f"**🏃 {rec['sport']}**")
                    with col_score:
                        score = rec['match_score']
                        if score >= 90:
                            st.markdown(f"🟢 **{score}%**")
                        elif score >= 75:
                            st.markdown(f"🟡 **{score}%**")
                        else:
                            st.markdown(f"🟠 **{score}%**")
                    
                    # Try to find matching offer for "View Details" button
                    matching_offer = None
                    for offer in offers_data:
                        if offer.get('name', '').lower() == rec['sport'].lower():
                            matching_offer = offer
                            break
                    
                    if matching_offer:
                        if st.button("View Details", key=f"ai_view_{rec['sport']}", use_container_width=True, type="secondary"):
                            set_selected_offer(matching_offer)
                            st.switch_page("pages/details.py")
                    else:
                        st.caption("💭 AI suggestion - details may not be available")
                    
                    st.divider()
    else:
        st.info(f"🤖 No sports found with ≥{min_match}% match. Try lowering the threshold or adjusting your filters.")

# Empty state footer
if len(offers) == 0:
    st.info("💡 **Tip:** Try clearing some filters to see more activities")

