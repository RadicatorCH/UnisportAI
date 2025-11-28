"""
Analytics and visualization functions for UnisportAI
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

# ML Feature columns (same as in ml_knn_recommender.py)
ML_FEATURE_COLUMNS = [
    'balance', 'flexibility', 'coordination', 'relaxation', 
    'strength', 'endurance', 'longevity', 'intensity',
    'setting_team', 'setting_fun', 'setting_duo', 
    'setting_solo', 'setting_competitive'
]

# User-friendly names for features
FEATURE_LABELS = {
    'balance': 'Balance',
    'flexibility': 'Flexibility',
    'coordination': 'Coordination',
    'relaxation': 'Relaxation',
    'strength': 'Strength',
    'endurance': 'Endurance',
    'longevity': 'Longevity',
    'intensity': 'Intensity',
    'setting_team': 'Team',
    'setting_fun': 'Fun',
    'setting_duo': 'Duo',
    'setting_solo': 'Solo',
    'setting_competitive': 'Competitive'
}


def get_ml_training_data():
    """Fetch ML training data from Supabase"""
    from data.supabase_client import get_supabase_client
    
    try:
        conn = get_supabase_client()
        result = conn.table("ml_training_data").select("*").execute()
        return pd.DataFrame(result.data) if result.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading ML training data: {e}")
        return pd.DataFrame()


def create_sport_radar_chart(sport_name: str, ml_data: pd.DataFrame, comparison_sports: Optional[List[str]] = None) -> go.Figure:
    """
    Creates an interactive radar chart showing ML features for a sport
    
    Args:
        sport_name: Name of the sport to visualize
        ml_data: DataFrame with ML training data
        comparison_sports: Optional list of sports to compare
        
    Returns:
        Plotly Figure object
    """
    # Get the sport data
    sport_data = ml_data[ml_data['Angebot'] == sport_name]
    
    if sport_data.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data found for {sport_name}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create radar chart
    fig = go.Figure()
    
    # Add main sport
    values = [sport_data[col].values[0] for col in ML_FEATURE_COLUMNS]
    labels = [FEATURE_LABELS[col] for col in ML_FEATURE_COLUMNS]
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        name=sport_name,
        line=dict(color='#FF4B4B', width=3),
        fillcolor='rgba(255, 75, 75, 0.2)'
    ))
    
    # Add comparison sports if provided
    if comparison_sports:
        colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']
        for i, comp_sport in enumerate(comparison_sports[:5]):  # Max 5 comparisons
            comp_data = ml_data[ml_data['Angebot'] == comp_sport]
            if not comp_data.empty:
                comp_values = [comp_data[col].values[0] for col in ML_FEATURE_COLUMNS]
                fig.add_trace(go.Scatterpolar(
                    r=comp_values,
                    theta=labels,
                    fill='toself',
                    name=comp_sport,
                    line=dict(color=colors[i % len(colors)], width=2),
                    fillcolor=f'rgba{tuple(list(px.colors.hex_to_rgb(colors[i % len(colors)])) + [0.1])}'
                ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                ticktext=['0%', '25%', '50%', '75%', '100%']
            )
        ),
        showlegend=True,
        title=dict(
            text=f"Sport Feature Profile: {sport_name}",
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#262730')
        ),
        height=600,
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    return fig


def create_rating_distribution_chart(offers_data: List[Dict]) -> go.Figure:
    """
    Creates a histogram showing distribution of sport ratings
    
    Args:
        offers_data: List of sport offers with ratings
        
    Returns:
        Plotly Figure object
    """
    # Extract ratings
    ratings = []
    for offer in offers_data:
        if offer.get('avg_rating') and offer.get('rating_count', 0) > 0:
            ratings.append(offer['avg_rating'])
    
    if not ratings:
        fig = go.Figure()
        fig.add_annotation(
            text="No rating data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create histogram
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ratings,
        nbinsx=20,
        marker=dict(
            color='#FF4B4B',
            line=dict(color='white', width=1)
        ),
        hovertemplate='Rating: %{x:.1f}<br>Count: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribution of Sport Ratings",
        xaxis_title="Average Rating",
        yaxis_title="Number of Sports",
        showlegend=False,
        height=400,
        bargap=0.1
    )
    
    return fig


def create_top_rated_sports_chart(offers_data: List[Dict], top_n: int = 10) -> go.Figure:
    """
    Creates a bar chart of top rated sports
    
    Args:
        offers_data: List of sport offers with ratings
        top_n: Number of top sports to show
        
    Returns:
        Plotly Figure object
    """
    # Filter sports with ratings
    rated_sports = [
        {
            'name': offer['name'],
            'rating': offer['avg_rating'],
            'count': offer.get('rating_count', 0)
        }
        for offer in offers_data
        if offer.get('avg_rating') and offer.get('rating_count', 0) >= 3  # Min 3 ratings
    ]
    
    if not rated_sports:
        fig = go.Figure()
        fig.add_annotation(
            text="No sports with sufficient ratings",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Sort by rating and take top N
    rated_sports.sort(key=lambda x: x['rating'], reverse=True)
    top_sports = rated_sports[:top_n]
    
    # Create bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s['rating'] for s in top_sports],
        y=[s['name'] for s in top_sports],
        orientation='h',
        marker=dict(
            color=[s['rating'] for s in top_sports],
            colorscale='RdYlGn',
            cmin=1,
            cmax=5,
            showscale=True,
            colorbar=dict(title="Rating")
        ),
        text=[f"⭐ {s['rating']:.1f} ({s['count']} reviews)" for s in top_sports],
        textposition='outside',
        hovertemplate='%{y}<br>Rating: %{x:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Rated Sports (min. 3 reviews)",
        xaxis_title="Average Rating",
        yaxis_title="Sport",
        height=max(400, top_n * 40),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[0, 5.5])
    )
    
    return fig


def create_feature_importance_chart(ml_data: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart showing feature variance across all sports
    
    Args:
        ml_data: DataFrame with ML training data
        
    Returns:
        Plotly Figure object
    """
    if ml_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No ML data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Calculate variance for each feature
    variances = {}
    for col in ML_FEATURE_COLUMNS:
        if col in ml_data.columns:
            variances[FEATURE_LABELS[col]] = ml_data[col].var()
    
    # Sort by variance
    sorted_features = sorted(variances.items(), key=lambda x: x[1], reverse=True)
    
    # Create bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f[1] for f in sorted_features],
        y=[f[0] for f in sorted_features],
        orientation='h',
        marker=dict(
            color=[f[1] for f in sorted_features],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Variance")
        ),
        hovertemplate='%{y}<br>Variance: %{x:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Feature Variance Across All Sports<br><sub>Higher variance = more discriminative feature</sub>",
        xaxis_title="Variance",
        yaxis_title="Feature",
        height=500,
        yaxis=dict(autorange="reversed")
    )
    
    return fig


def create_intensity_distribution_pie(offers_data: List[Dict]) -> go.Figure:
    """
    Creates a pie chart showing distribution of intensity levels
    
    Args:
        offers_data: List of sport offers
        
    Returns:
        Plotly Figure object
    """
    # Count intensity levels
    intensity_counts = defaultdict(int)
    for offer in offers_data:
        intensity = offer.get('intensity', '').capitalize()
        if intensity:
            intensity_counts[intensity] += 1
    
    if not intensity_counts:
        fig = go.Figure()
        fig.add_annotation(
            text="No intensity data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create pie chart
    labels = list(intensity_counts.keys())
    values = list(intensity_counts.values())
    
    colors = {
        'Low': '#2ecc71',
        'Medium': '#f39c12',
        'High': '#e74c3c'
    }
    pie_colors = [colors.get(label, '#95a5a6') for label in labels]
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=pie_colors),
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        textinfo='label+percent',
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Sport Intensity Distribution",
        height=400
    )
    
    return fig


def create_setting_distribution_chart(offers_data: List[Dict]) -> go.Figure:
    """
    Creates a stacked bar chart showing setting distribution
    
    Args:
        offers_data: List of sport offers
        
    Returns:
        Plotly Figure object
    """
    # Count settings
    setting_counts = defaultdict(int)
    for offer in offers_data:
        settings = offer.get('setting', [])
        if settings:
            for setting in settings:
                if setting:
                    setting_counts[setting.capitalize()] += 1
    
    if not setting_counts:
        fig = go.Figure()
        fig.add_annotation(
            text="No setting data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Sort by count
    sorted_settings = sorted(setting_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Create bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s[0] for s in sorted_settings],
        y=[s[1] for s in sorted_settings],
        marker=dict(
            color='#3498db',
            line=dict(color='white', width=1)
        ),
        hovertemplate='%{x}<br>Count: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Sport Settings Distribution",
        xaxis_title="Setting",
        yaxis_title="Number of Sports",
        height=400,
        showlegend=False
    )
    
    return fig
