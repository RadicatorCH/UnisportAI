import streamlit as st
from data.user_management import render_user_profile_page
from data.auth import is_logged_in

# Check authentication
if not is_logged_in():
    st.error("❌ Bitte melden Sie sich an.")
    st.stop()

# Zeige User Profile Page
render_user_profile_page()

