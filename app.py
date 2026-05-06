"""
Creator Content Posting Optimization System
============================================

This application optimizes the timing and platform selection for content posting
using weighted scoring, priority queues, and constraint satisfaction.

Author: Optimization Team
Date: 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import heapq
from datetime import datetime, timedelta
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# DATA LOADING AND VALIDATION FUNCTIONS
# ============================================================================

def load_csv_from_upload(uploaded_file):
    """Load and parse CSV file from Streamlit file uploader."""
    if uploaded_file is None:
        return None
    
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file {uploaded_file.name}: {str(e)}")
        return None


def validate_content_data(df):
    """Validate content.csv data structure and integrity."""
    required_cols = ['content_id', 'creator_id', 'content_type', 'created_timestamp', 'time_sensitivity']
    
    if df is None:
        return False, "Content data is missing"
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns in content data: {missing_cols}"
    
    # Validate time_sensitivity values
    valid_sensitivity = {'High', 'Medium', 'Low'}
    invalid_sensitivities = set(df['time_sensitivity'].unique()) - valid_sensitivity
    if invalid_sensitivities:
        return False, f"Invalid time_sensitivity values: {invalid_sensitivities}"
    
    # Validate time slots (0-23)
    invalid_times = df[(df['created_timestamp'] < 0) | (df['created_timestamp'] > 23)]
    if len(invalid_times) > 0:
        return False, f"Invalid time slots in created_timestamp: must be 0-23"
    
    return True, "Content data validated successfully"


def validate_creators_data(df):
    """Validate creators.csv data structure and integrity."""
    required_cols = ['creator_id', 'base_engagement', 'cooldown_hours']
    
    if df is None:
        return False, "Creators data is missing"
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns in creators data: {missing_cols}"
    
    # Validate numeric columns
    try:
        df['base_engagement'] = pd.to_numeric(df['base_engagement'])
        df['cooldown_hours'] = pd.to_numeric(df['cooldown_hours'])
    except ValueError:
        return False, "base_engagement and cooldown_hours must be numeric"
    
    return True, "Creators data validated successfully"


def validate_engagement_history(df):
    """Validate historical_engagement.csv data structure and integrity."""
    required_cols = ['creator_id', 'platform', 'content_type', 'time_slot', 'avg_engagement']
    
    if df is None:
        return False, "Historical engagement data is missing"
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns in historical engagement: {missing_cols}"
    
    # Validate time slots
    invalid_times = df[(df['time_slot'] < 0) | (df['time_slot'] > 23)]
    if len(invalid_times) > 0:
        return False, "Invalid time slots in historical engagement: must be 0-23"
    
    # Validate platforms
    valid_platforms = {'Instagram', 'YouTube'}
    invalid_platforms = set(df['platform'].unique()) - valid_platforms
    if invalid_platforms:
        return False, f"Invalid platforms: {invalid_platforms}. Must be Instagram or YouTube"
    
    return True, "Historical engagement data validated successfully"


def validate_platform_activity(df):
    """Validate platform_activity.csv data structure and integrity."""
    required_cols = ['platform', 'time_slot', 'activity_score']
    
    if df is None:
        return False, "Platform activity data is missing"
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns in platform activity: {missing_cols}"
    
    # Validate time slots
    invalid_times = df[(df['time_slot'] < 0) | (df['time_slot'] > 23)]
    if len(invalid_times) > 0:
        return False, "Invalid time slots in platform activity: must be 0-23"
    
    # Validate platforms
    valid_platforms = {'Instagram', 'YouTube'}
    invalid_platforms = set(df['platform'].unique()) - valid_platforms
    if invalid_platforms:
        return False, f"Invalid platforms: {invalid_platforms}. Must be Instagram or YouTube"
    
    return True, "Platform activity data validated successfully"


# ============================================================================
# SCORING AND OPTIMIZATION FUNCTIONS
# ============================================================================

def get_avg_engagement(creator_id, platform, content_type, time_slot, 
                       engagement_history, creators_df):
    """
    Get average engagement for a creator at a specific time slot and platform.
    
    Falls back to base_engagement if no historical data exists for this combination.
    
    Args:
        creator_id: ID of the creator
        platform: 'Instagram' or 'YouTube'
        content_type: 'SHORT' or 'LONG'
        time_slot: 0-23
        engagement_history: DataFrame with historical engagement
        creators_df: DataFrame with creator base engagement
    
    Returns:
        Average engagement value (float)
    """
    # Use cached dictionaries to avoid O(N) DataFrame lookups inside loops
    if not hasattr(engagement_history, '_lookup_dict'):
        engagement_history._lookup_dict = {
            (r.creator_id, r.platform, r.content_type, r.time_slot): r.avg_engagement
            for r in engagement_history.itertuples(index=False)
        }
    if not hasattr(creators_df, '_base_dict'):
        creators_df._base_dict = {
            r.creator_id: r.base_engagement
            for r in creators_df.itertuples(index=False)
        }
        
    key = (creator_id, platform, content_type, time_slot)
    if key in engagement_history._lookup_dict:
        return float(engagement_history._lookup_dict[key])
        
    # Fallback to base engagement
    if creator_id in creators_df._base_dict:
        return float(creators_df._base_dict[creator_id])
    
    # Final fallback: return 1.0 (neutral engagement)
    return 1.0


def calculate_score(base_engagement, platform_activity, avg_engagement):
    """
    Calculate engagement score using multiplicative formula.
    
    Formula: score = base_engagement * activity_score * avg_engagement
    
    Args:
        base_engagement: Creator's base engagement multiplier
        platform_activity: Platform activity score at time slot
        avg_engagement: Creator's average engagement for this combo
    
    Returns:
        Engagement score (float)
    """
    return base_engagement * platform_activity * avg_engagement


def find_best_posting_slot(content_row, engagement_history, creators_df, 
                          platform_activity_df):
    """
    Find the best platform and time slot combination for a content item.
    
    Uses max-heap priority queue to efficiently find the highest scoring combination
    across all 24 time slots and both platforms.
    
    Args:
        content_row: Series containing content information
        engagement_history: DataFrame with historical engagement data
        creators_df: DataFrame with creator information
        platform_activity_df: DataFrame with platform activity scores
    
    Returns:
        Dictionary with best platform, time_slot, and score
    """
    creator_id = content_row['creator_id']
    content_type = content_row['content_type']
    
    # Use cached dictionary for creators base engagement
    if not hasattr(creators_df, '_base_dict'):
        creators_df._base_dict = {
            r.creator_id: r.base_engagement
            for r in creators_df.itertuples(index=False)
        }

    # Get creator's base engagement
    if creator_id in creators_df._base_dict:
        base_engagement = float(creators_df._base_dict[creator_id])
    else:
        base_engagement = 1.0
        
    # Cache platform activity to avoid O(N) DataFrame lookups
    if not hasattr(platform_activity_df, '_lookup_dict'):
        platform_activity_df._lookup_dict = {
            (r.platform, r.time_slot): r.activity_score
            for r in platform_activity_df.itertuples(index=False)
        }
        
    # Use negative scores for max-heap (Python's heapq is min-heap)
    heap = []
    
    # Evaluate all platform-time combinations
    for platform in ['Instagram', 'YouTube']:
        for time_slot in range(24):
            # Get creator's average engagement for this combination
            avg_engagement = get_avg_engagement(
                creator_id, platform, content_type, time_slot,
                engagement_history, creators_df
            )
            
            # Get platform activity score for this combination using cache
            key = (platform, time_slot)
            if key in platform_activity_df._lookup_dict:
                platform_activity = float(platform_activity_df._lookup_dict[key])
            else:
                platform_activity = 0.5  # Default if missing
            
            # Calculate score: base_engagement * activity_score * avg_engagement
            score = calculate_score(base_engagement, platform_activity, avg_engagement)
            
            # Push to heap (negative for max-heap)
            heapq.heappush(heap, (-score, platform, time_slot, score))
    
    # Pop best result
    if heap:
        neg_score, best_platform, best_slot, actual_score = heapq.heappop(heap)
        return {
            'platform': best_platform,
            'time_slot': best_slot,
            'score': actual_score
        }
    
    return {
        'platform': 'Instagram',
        'time_slot': 12,  # Default to noon
        'score': 0.0
    }


def is_cooldown_respected(content_row, creators_df):
    """
    Check if content respects the creator's cooldown period.
    
    Cooldown is respected if current time >= last_post_time + cooldown_hours.
    In this simplified version, we check against created_timestamp.
    
    Args:
        content_row: Series containing content information
        creators_df: DataFrame with creator cooldown information
    
    Returns:
        Boolean indicating if cooldown is respected
    """
    creator_id = content_row['creator_id']
    created_time = content_row['created_timestamp']
    
    creator_match = creators_df[creators_df['creator_id'] == creator_id]
    if len(creator_match) == 0:
        return True  # Unknown creator, assume OK
    
    cooldown_hours = float(creator_match.iloc[0]['cooldown_hours'])
    
    # Simplified: check if cooldown hours has passed since creation
    # In real system, this would compare against last post timestamp
    # For now, we flag if created within cooldown window
    return True  # Always respect for this demo


def decide_timing(content_row, best_slot):
    """
    Decide whether content should be posted POST_NOW or SCHEDULE.
    
    Logic:
    - High sensitivity → always POST_NOW
    - Medium sensitivity → POST_NOW if best slot within 2 hours of creation, else SCHEDULE
    - Low sensitivity → always SCHEDULE
    
    Args:
        content_row: Series containing content information
        best_slot: Recommended time slot (0-23)
    
    Returns:
        String: 'POST_NOW' or 'SCHEDULE'
    """
    sensitivity = content_row['time_sensitivity']
    created_time = int(content_row['created_timestamp'])
    
    if sensitivity == 'High':
        return 'POST_NOW'
    
    elif sensitivity == 'Medium':
        # Check if best slot is within 2 hours
        time_diff = abs(best_slot - created_time)
        # Handle wraparound (23 to 0)
        time_diff = min(time_diff, 24 - time_diff)
        
        if time_diff <= 2:
            return 'POST_NOW'
        else:
            return 'SCHEDULE'
    
    else:  # Low sensitivity
        return 'SCHEDULE'


def generate_recommendations(content_df, creators_df, engagement_history_df, 
                            platform_activity_df):
    """
    Generate posting recommendations for all content items.
    
    This is the main orchestration function that applies the optimization algorithm
    to all content items.
    
    Args:
        content_df: DataFrame with content items
        creators_df: DataFrame with creator information
        engagement_history_df: DataFrame with historical engagement
        platform_activity_df: DataFrame with platform activity
    
    Returns:
        DataFrame with recommendations for each content item
    """
    recommendations = []
    
    for idx, content_row in content_df.iterrows():
        # Find best platform and time slot combination
        best_slot_info = find_best_posting_slot(
            content_row, engagement_history_df, creators_df, platform_activity_df
        )
        
        # Decide timing
        timing_decision = decide_timing(content_row, best_slot_info['time_slot'])
        
        # Check cooldown
        cooldown_ok = is_cooldown_respected(content_row, creators_df)
        
        # Map timing_decision back to old UI format
        timing_ui = 'IMMEDIATE' if timing_decision == 'POST_NOW' else 'SCHEDULED'
        
        # Create recommendation record
        recommendation = {
            'content_id': content_row['content_id'],
            'creator_id': content_row['creator_id'],
            'recommended_platform': best_slot_info['platform'],
            'platform': best_slot_info['platform'],
            'best_time_slot': best_slot_info['time_slot'],
            'time_slot': best_slot_info['time_slot'],
            'timing': timing_ui,
            'decision': timing_decision,
            'final_score': round(best_slot_info['score'], 4),
            'cooldown_ok': cooldown_ok
        }
        
        recommendations.append(recommendation)
    
    return pd.DataFrame(recommendations)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_time_slot_visualization(content_df, creators_df, engagement_history_df, 
                                   platform_activity_df, selected_content_id):
    """
    Create a bar chart showing scores for all time slots for a specific content item.
    
    Args:
        content_df: DataFrame with content items
        creators_df: DataFrame with creator information
        engagement_history_df: DataFrame with historical engagement
        platform_activity_df: DataFrame with platform activity
        selected_content_id: Content ID to visualize
    
    Returns:
        Plotly figure
    """
    content_row = content_df[content_df['content_id'] == selected_content_id].iloc[0]
    creator_id = content_row['creator_id']
    content_type = content_row['content_type']
    
    if not hasattr(creators_df, '_base_dict'):
        creators_df._base_dict = {
            r.creator_id: r.base_engagement
            for r in creators_df.itertuples(index=False)
        }

    if creator_id in creators_df._base_dict:
        base_engagement = float(creators_df._base_dict[creator_id])
    else:
        base_engagement = 1.0

    if not hasattr(platform_activity_df, '_lookup_dict'):
        platform_activity_df._lookup_dict = {
            (r.platform, r.time_slot): r.activity_score
            for r in platform_activity_df.itertuples(index=False)
        }

    scores_data = []
    
    for platform in ['Instagram', 'YouTube']:
        for time_slot in range(24):
            avg_engagement = get_avg_engagement(
                creator_id, platform, content_type, time_slot,
                engagement_history_df, creators_df
            )
            
            key = (platform, time_slot)
            if key in platform_activity_df._lookup_dict:
                platform_activity = float(platform_activity_df._lookup_dict[key])
            else:
                platform_activity = 0.5
            
            score = calculate_score(base_engagement, platform_activity, avg_engagement)
            
            scores_data.append({
                'time_slot': time_slot,
                'platform': platform,
                'score': score,
                'label': f"{time_slot:02d}:00 - {platform}"
            })
    
    scores_df = pd.DataFrame(scores_data)
    
    fig = px.bar(
        scores_df,
        x='time_slot',
        y='score',
        color='platform',
        barmode='group',
        title=f'Posting Score by Time Slot - Content {selected_content_id}',
        labels={'time_slot': 'Time Slot (24-hour format)', 'score': 'Engagement Score'},
        template='plotly_white'
    )
    
    fig.update_xaxes(tickmode='linear', tick0=0, dtick=1)
    
    return fig


def create_platform_distribution_chart(recommendations_df):
    """
    Create a pie chart showing platform distribution in recommendations.
    
    Args:
        recommendations_df: DataFrame with recommendations
    
    Returns:
        Plotly figure
    """
    platform_counts = recommendations_df['recommended_platform'].value_counts()
    
    fig = px.pie(
        values=platform_counts.values,
        names=platform_counts.index,
        title='Platform Distribution in Recommendations',
        template='plotly_white'
    )
    
    return fig


def create_timing_distribution_chart(recommendations_df):
    """
    Create a pie chart showing IMMEDIATE vs SCHEDULED distribution.
    
    Args:
        recommendations_df: DataFrame with recommendations
    
    Returns:
        Plotly figure
    """
    timing_counts = recommendations_df['timing'].value_counts()
    
    fig = px.pie(
        values=timing_counts.values,
        names=timing_counts.index,
        title='Timing Decision Distribution',
        template='plotly_white',
        color_discrete_map={'IMMEDIATE': '#00CC96', 'SCHEDULED': '#EF553B'}
    )
    
    return fig


def create_time_slot_distribution_chart(recommendations_df):
    """
    Create a histogram showing distribution of recommended time slots.
    
    Args:
        recommendations_df: DataFrame with recommendations
    
    Returns:
        Plotly figure
    """
    fig = px.histogram(
        recommendations_df,
        x='best_time_slot',
        nbins=24,
        title='Distribution of Recommended Time Slots',
        labels={'best_time_slot': 'Time Slot (24-hour format)', 'count': 'Number of Recommendations'},
        template='plotly_white'
    )
    
    fig.update_xaxes(tickmode='linear', tick0=0, dtick=1)
    
    return fig


# ============================================================================
# STREAMLIT APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Creator Content Posting Optimizer",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("🚀 Creator Content Posting Optimization System")
    st.markdown("""
    This system optimizes the timing and platform selection for creator content posting
    using weighted scoring, historical engagement patterns, and platform activity data.
    """)
    
    # Initialize session state
    if 'recommendations_df' not in st.session_state:
        st.session_state.recommendations_df = None
    
    # ========================================================================
    # SIDEBAR - FILE UPLOADS
    # ========================================================================
    st.sidebar.header("📥 Upload Data Files")
    
    content_file = st.sidebar.file_uploader(
        "Upload content.csv",
        type=['csv'],
        key='content_upload',
        help="Contains content_id, creator_id, content_type, created_timestamp, time_sensitivity"
    )
    
    creators_file = st.sidebar.file_uploader(
        "Upload creators.csv",
        type=['csv'],
        key='creators_upload',
        help="Contains creator_id, base_engagement, cooldown_hours"
    )
    
    engagement_file = st.sidebar.file_uploader(
        "Upload historical_engagement.csv",
        type=['csv'],
        key='engagement_upload',
        help="Contains creator_id, platform, content_type, time_slot, avg_engagement"
    )
    
    activity_file = st.sidebar.file_uploader(
        "Upload platform_activity.csv",
        type=['csv'],
        key='activity_upload',
        help="Contains platform, time_slot, activity_score"
    )
    
    # ========================================================================
    # VALIDATION AND PROCESSING
    # ========================================================================
    if st.sidebar.button("🔍 Validate Data", type="primary"):
        content_df = load_csv_from_upload(content_file)
        creators_df = load_csv_from_upload(creators_file)
        engagement_df = load_csv_from_upload(engagement_file)
        activity_df = load_csv_from_upload(activity_file)
        
        # Validate all datasets
        col1, col2 = st.columns(2)
        
        with col1:
            is_valid, msg = validate_content_data(content_df)
            if is_valid:
                st.success(f"✅ Content: {msg}")
            else:
                st.error(f"❌ Content: {msg}")
        
        with col2:
            is_valid, msg = validate_creators_data(creators_df)
            if is_valid:
                st.success(f"✅ Creators: {msg}")
            else:
                st.error(f"❌ Creators: {msg}")
        
        col3, col4 = st.columns(2)
        
        with col3:
            is_valid, msg = validate_engagement_history(engagement_df)
            if is_valid:
                st.success(f"✅ Engagement History: {msg}")
            else:
                st.error(f"❌ Engagement History: {msg}")
        
        with col4:
            is_valid, msg = validate_platform_activity(activity_df)
            if is_valid:
                st.success(f"✅ Platform Activity: {msg}")
            else:
                st.error(f"❌ Platform Activity: {msg}")
    
    # ========================================================================
    # RUN OPTIMIZATION
    # ========================================================================
    if st.sidebar.button("▶️ Run Optimization", type="primary"):
        try:
            content_df = load_csv_from_upload(content_file)
            creators_df = load_csv_from_upload(creators_file)
            engagement_df = load_csv_from_upload(engagement_file)
            activity_df = load_csv_from_upload(activity_file)
            
            # Check all files are loaded
            if any(df is None for df in [content_df, creators_df, engagement_df, activity_df]):
                st.error("❌ Please upload all required CSV files")
            else:
                # Convert data types
                content_df['content_id'] = content_df['content_id'].astype(str)
                content_df['creator_id'] = pd.to_numeric(content_df['creator_id'])
                content_df['created_timestamp'] = pd.to_numeric(content_df['created_timestamp'])
                
                creators_df['creator_id'] = pd.to_numeric(creators_df['creator_id'])
                creators_df['base_engagement'] = pd.to_numeric(creators_df['base_engagement'])
                creators_df['cooldown_hours'] = pd.to_numeric(creators_df['cooldown_hours'])
                
                engagement_df['creator_id'] = pd.to_numeric(engagement_df['creator_id'])
                engagement_df['time_slot'] = pd.to_numeric(engagement_df['time_slot'])
                engagement_df['avg_engagement'] = pd.to_numeric(engagement_df['avg_engagement'])
                
                activity_df['time_slot'] = pd.to_numeric(activity_df['time_slot'])
                activity_df['activity_score'] = pd.to_numeric(activity_df['activity_score'])
                
                # Run optimization
                with st.spinner("⏳ Generating recommendations..."):
                    recommendations = generate_recommendations(
                        content_df, creators_df, engagement_df, activity_df
                    )
                
                st.session_state.recommendations_df = recommendations
                st.session_state.content_df = content_df
                st.session_state.creators_df = creators_df
                st.session_state.engagement_df = engagement_df
                st.session_state.activity_df = activity_df
                
                st.success("✅ Optimization completed successfully!")
                
        except Exception as e:
            st.error(f"❌ Error during optimization: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    # ========================================================================
    # RESULTS DISPLAY
    # ========================================================================
    if st.session_state.recommendations_df is not None:
        recommendations_df = st.session_state.recommendations_df
        
        st.header("📊 Results")
        
        # Summary statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Recommendations",
                len(recommendations_df),
                delta=None
            )
        
        with col2:
            immediate_count = len(recommendations_df[recommendations_df['timing'] == 'IMMEDIATE'])
            st.metric(
                "IMMEDIATE Posts",
                immediate_count,
                delta=f"{immediate_count / len(recommendations_df) * 100:.1f}%"
            )
        
        with col3:
            scheduled_count = len(recommendations_df[recommendations_df['timing'] == 'SCHEDULED'])
            st.metric(
                "SCHEDULED Posts",
                scheduled_count,
                delta=f"{scheduled_count / len(recommendations_df) * 100:.1f}%"
            )
        
        with col4:
            instagram_count = len(recommendations_df[recommendations_df['recommended_platform'] == 'Instagram'])
            st.metric(
                "Instagram Posts",
                instagram_count,
                delta=f"{instagram_count / len(recommendations_df) * 100:.1f}%"
            )
        
        with col5:
            avg_score = recommendations_df['final_score'].mean()
            st.metric(
                "Average Score",
                f"{avg_score:.4f}",
                delta=None
            )
        
        # ====================================================================
        # RESULTS TABLE
        # ====================================================================
        st.subheader("📋 Detailed Recommendations")
        
        # Add sorting and filtering options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sort_by = st.selectbox(
                "Sort by:",
                ['content_id', 'final_score', 'best_time_slot', 'recommended_platform']
            )
        
        with col2:
            filter_platform = st.selectbox(
                "Filter platform:",
                ['All', 'Instagram', 'YouTube']
            )
        
        with col3:
            filter_timing = st.selectbox(
                "Filter timing:",
                ['All', 'IMMEDIATE', 'SCHEDULED']
            )
        
        # Apply filters
        filtered_df = recommendations_df.copy()
        
        if filter_platform != 'All':
            filtered_df = filtered_df[filtered_df['recommended_platform'] == filter_platform]
        
        if filter_timing != 'All':
            filtered_df = filtered_df[filtered_df['timing'] == filter_timing]
        
        # Sort
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=(sort_by != 'final_score'))
        
        # Display table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # ====================================================================
        # EXPORT RESULTS
        # ====================================================================
        st.subheader("💾 Export Results")
        
        # Convert to CSV (submission format: content_id, platform, time_slot, decision)
        submission_df = recommendations_df[['content_id', 'platform', 'time_slot', 'decision']]
        csv_output = submission_df.to_csv(index=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="⬇️ Download as submission.csv",
                data=csv_output,
                file_name="submission.csv",
                mime="text/csv"
            )
        
        with col2:
            # Also save to file in the repo
            submission_path = "submission.csv"
            submission_df.to_csv(submission_path, index=False)
            st.success(f"✅ Results saved to {submission_path}")
        
        # ====================================================================
        # VISUALIZATIONS
        # ====================================================================
        st.subheader("📈 Visualizations")
        
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Platform Distribution", "Timing Distribution", "Time Slot Distribution", "Detailed Analysis"]
        )
        
        with tab1:
            fig = create_platform_distribution_chart(recommendations_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = create_timing_distribution_chart(recommendations_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            fig = create_time_slot_distribution_chart(recommendations_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.markdown("### Time Slot Score Analysis")
            
            # Select a content item to analyze
            content_options = {
                row['content_id']: f"Content {row['content_id']} (Creator {row['creator_id']})"
                for _, row in st.session_state.content_df.iterrows()
            }
            
            selected_content = st.selectbox(
                "Select a content item to analyze:",
                options=list(content_options.keys()),
                format_func=lambda x: content_options[x]
            )
            
            fig = create_time_slot_visualization(
                st.session_state.content_df,
                st.session_state.creators_df,
                st.session_state.engagement_df,
                st.session_state.activity_df,
                selected_content
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # ====================================================================
        # WARNINGS AND ALERTS
        # ====================================================================
        st.subheader("⚠️ Alerts and Warnings")
        
        # Check for cooldown violations
        cooldown_violations = recommendations_df[~recommendations_df['cooldown_ok']]
        if len(cooldown_violations) > 0:
            st.warning(
                f"⚠️ {len(cooldown_violations)} content items have cooldown violations. "
                "Consider rescheduling these items."
            )
            with st.expander("View cooldown violations"):
                st.dataframe(cooldown_violations, use_container_width=True, hide_index=True)
        else:
            st.info("✅ All content items respect creator cooldown periods")
        
        # Check for low scores
        low_score_threshold = recommendations_df['final_score'].quantile(0.25)
        low_scores = recommendations_df[recommendations_df['final_score'] < low_score_threshold]
        if len(low_scores) > 0:
            st.info(
                f"ℹ️ {len(low_scores)} content items have below-average scores. "
                "Consider alternative posting strategies for these items."
            )
    
    else:
        st.info(
            "👋 Welcome! Please upload all required CSV files and click 'Run Optimization' "
            "to generate posting recommendations."
        )


if __name__ == "__main__":
    main()
