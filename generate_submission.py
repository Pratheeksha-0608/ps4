import pandas as pd
import requests
import time

API_URL = "http://127.0.0.1:8000"

def generate_submission():
    print("Loading content.csv...")
    content_df = pd.read_csv('content.csv')
    
    recommendations = []
    
    print(f"Processing {len(content_df)} items via API...")
    
    for _, row in content_df.iterrows():
        # Submit content
        payload = {
            "content_id": str(row['content_id']),
            "creator_id": int(row['creator_id']),
            "content_type": str(row['content_type']),
            "created_timestamp": int(row['created_timestamp']),
            "time_sensitivity": str(row['time_sensitivity'])
        }
        
        post_res = requests.post(f"{API_URL}/submit_content", json=payload)
        post_res.raise_for_status()
        
        # Get recommendation
        get_res = requests.get(f"{API_URL}/get_recommendation/{payload['content_id']}")
        get_res.raise_for_status()
        
        rec = get_res.json()
        recommendations.append(rec)
        
    # Create submission dataframe
    submission_df = pd.DataFrame(recommendations)
    # Ensure correct column order
    submission_df = submission_df[['content_id', 'platform', 'time_slot', 'decision']]
    
    # Save to CSV
    submission_df.to_csv('submission.csv', index=False)
    print("Successfully generated submission.csv via FastAPI backend.")

if __name__ == '__main__':
    generate_submission()
