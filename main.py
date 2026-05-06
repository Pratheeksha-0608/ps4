from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import heapq

app = FastAPI()

# Data stores
creators_df = pd.DataFrame()
platform_activity_df = pd.DataFrame()
engagement_history_df = pd.DataFrame()
content_store = {}

# Pydantic models
class ContentItem(BaseModel):
    content_id: str
    creator_id: int
    content_type: str
    created_timestamp: int
    time_sensitivity: str

class RecommendationResponse(BaseModel):
    content_id: str
    platform: str
    time_slot: int
    decision: str

@app.on_event("startup")
def load_data():
    global creators_df, platform_activity_df, engagement_history_df
    try:
        creators_df = pd.read_csv('creators.csv')
        platform_activity_df = pd.read_csv('platform_activity.csv')
        engagement_history_df = pd.read_csv('historical_engagement.csv')
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load CSV data: {e}")

@app.post("/submit_content")
def submit_content(item: ContentItem):
    content_store[item.content_id] = item.dict()
    return {"message": "Content submitted successfully", "content_id": item.content_id}

def get_avg_engagement(creator_id, platform, content_type, time_slot):
    match = engagement_history_df[
        (engagement_history_df['creator_id'] == creator_id) &
        (engagement_history_df['platform'] == platform) &
        (engagement_history_df['content_type'] == content_type) &
        (engagement_history_df['time_slot'] == time_slot)
    ]
    if len(match) > 0:
        return float(match.iloc[0]['avg_engagement'])
    
    creator_match = creators_df[creators_df['creator_id'] == creator_id]
    if len(creator_match) > 0:
        return float(creator_match.iloc[0]['base_engagement'])
    return 1.0

def calculate_score(base_engagement, platform_activity, avg_engagement):
    return base_engagement * platform_activity * avg_engagement

def decide_timing(sensitivity, created_time, best_slot):
    if sensitivity == 'High':
        return 'POST_NOW'
    elif sensitivity == 'Medium':
        time_diff = abs(best_slot - created_time)
        time_diff = min(time_diff, 24 - time_diff)
        if time_diff <= 2:
            return 'POST_NOW'
        else:
            return 'SCHEDULE'
    else:
        return 'SCHEDULE'

@app.get("/get_recommendation/{content_id}", response_model=RecommendationResponse)
def get_recommendation(content_id: str):
    if content_id not in content_store:
        raise HTTPException(status_code=404, detail="Content not found")
        
    content_row = content_store[content_id]
    creator_id = content_row['creator_id']
    content_type = content_row['content_type']
    created_time = content_row['created_timestamp']
    sensitivity = content_row['time_sensitivity']
    
    creator_match = creators_df[creators_df['creator_id'] == creator_id]
    if len(creator_match) > 0:
        base_engagement = float(creator_match.iloc[0]['base_engagement'])
    else:
        base_engagement = 1.0
        
    heap = []
    
    for platform in ['Instagram', 'YouTube']:
        for time_slot in range(24):
            avg_engagement = get_avg_engagement(creator_id, platform, content_type, time_slot)
            
            platform_match = platform_activity_df[
                (platform_activity_df['platform'] == platform) &
                (platform_activity_df['time_slot'] == time_slot)
            ]
            
            platform_activity = float(platform_match.iloc[0]['activity_score']) if len(platform_match) > 0 else 0.5
            
            score = calculate_score(base_engagement, platform_activity, avg_engagement)
            
            heapq.heappush(heap, (-score, platform, time_slot, score))
            
    if heap:
        neg_score, best_platform, best_slot, actual_score = heapq.heappop(heap)
    else:
        best_platform, best_slot = 'Instagram', 12
        
    decision = decide_timing(sensitivity, created_time, best_slot)
    
    return RecommendationResponse(
        content_id=content_id,
        platform=best_platform,
        time_slot=best_slot,
        decision=decision
    )
