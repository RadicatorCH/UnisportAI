import streamlit as st
from data.supabase_client import kurse

st.markdown("# Main page 🎈")
st.sidebar.markdown("# Main page 🎈")

st.title('Unisport Planner')

kurse = kurse()
