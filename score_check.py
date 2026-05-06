import pandas as pd

def score_check():
    creators = pd.read_csv('creators.csv')
    activity = pd.read_csv('platform_activity.csv')
    history = pd.read_csv('historical_engagement.csv')
    content = pd.read_csv('content.csv')
    
    try:
        submission = pd.read_csv('submission.csv')
    except Exception as e:
        print("Could not load submission.csv:", e)
        return

    merged = submission.merge(content, on='content_id')
    merged = merged.merge(creators, on='creator_id')
    
    total_score = 0
    total_engagement = 0
    total_timing = 0
    total_platform = 0
    total_efficiency = 0
    
    for _, row in merged.iterrows():
        # Get activity
        act_match = activity[(activity['platform'] == row['platform']) & (activity['time_slot'] == row['time_slot'])]
        act_score = act_match['activity_score'].iloc[0] if len(act_match) > 0 else 0.5
        
        # Get history
        hist_match = history[(history['creator_id'] == row['creator_id']) & 
                             (history['platform'] == row['platform']) & 
                             (history['content_type'] == row['content_type']) &
                             (history['time_slot'] == row['time_slot'])]
        avg_eng = hist_match['avg_engagement'].iloc[0] if len(hist_match) > 0 else row['base_engagement']
        
        engagement = row['base_engagement'] * act_score * avg_eng
        timing = act_score
        
        if row['content_type'] == 'SHORT' and row['platform'] == 'Instagram': p_score = 1.0
        elif row['content_type'] == 'LONG' and row['platform'] == 'YouTube': p_score = 1.0
        elif row['content_type'] == 'SHORT' and row['platform'] == 'YouTube': p_score = 0.85
        elif row['content_type'] == 'LONG' and row['platform'] == 'Instagram': p_score = 0.70
        else: p_score = 0.5
        
        # Latency
        latency_hours = (row['time_slot'] - row['created_timestamp']) % 24
        latency = latency_hours / 24.0
        efficiency = max(0, 1 - latency)
        
        final = 0.50 * engagement + 0.20 * timing + 0.15 * p_score + 0.15 * efficiency
        
        total_score += final
        total_engagement += engagement
        total_timing += timing
        total_platform += p_score
        total_efficiency += efficiency

    n = len(merged)
    print(f"Total Submissions Evaluated: {n}")
    print(f"Average Engagement Score: {total_engagement / n:.4f}")
    print(f"Average Timing Score: {total_timing / n:.4f}")
    print(f"Average Platform Quality: {total_platform / n:.4f}")
    print(f"Average Efficiency: {total_efficiency / n:.4f}")
    print(f"FINAL AVERAGE SCORE: {total_score / n:.4f}")

if __name__ == '__main__':
    score_check()
