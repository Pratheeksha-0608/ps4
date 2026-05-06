import pandas as pd
import numpy as np
import random
import os

def generate_data():
    random.seed(42)
    np.random.seed(42)
    
    # 1. creators.csv
    creators = []
    for i in range(1, 51):
        creators.append({
            'creator_id': i,
            'base_engagement': round(random.uniform(0.6, 1.4), 2),
            'cooldown_hours': random.randint(2, 12)
        })
    pd.DataFrame(creators).to_csv('creators.csv', index=False)
    
    # 2. platform_activity.csv
    activity = []
    for platform in ['Instagram', 'YouTube']:
        for hour in range(24):
            if platform == 'Instagram':
                # peak 18-22
                score = random.uniform(0.8, 1.0) if 18 <= hour <= 22 else random.uniform(0.3, 0.7)
            else:
                # peak 20-23
                score = random.uniform(0.8, 1.0) if 20 <= hour <= 23 else random.uniform(0.3, 0.7)
            activity.append({'platform': platform, 'time_slot': hour, 'activity_score': round(score, 2)})
    pd.DataFrame(activity).to_csv('platform_activity.csv', index=False)
    
    # 3. historical_engagement.csv
    history = []
    for i in range(1, 51):
        for platform in ['Instagram', 'YouTube']:
            for ctype in ['SHORT', 'LONG']:
                base = random.uniform(0.5, 1.5)
                if ctype == 'SHORT' and platform == 'Instagram':
                    base *= 1.25
                elif ctype == 'LONG' and platform == 'YouTube':
                    base *= 1.25
                
                slots = random.sample(range(24), 5)
                for slot in slots:
                    history.append({
                        'creator_id': i,
                        'platform': platform,
                        'content_type': ctype,
                        'time_slot': slot,
                        'avg_engagement': round(base * random.uniform(0.9, 1.1), 2)
                    })
    pd.DataFrame(history).to_csv('historical_engagement.csv', index=False)
    
    # 4. content.csv
    content = []
    for i in range(1, 1201):
        content.append({
            'content_id': f'C{i:04d}',
            'creator_id': random.randint(1, 50),
            'content_type': random.choice(['SHORT', 'LONG']),
            'created_timestamp': random.randint(0, 23),
            'time_sensitivity': random.choice(['High', 'Medium', 'Low'])
        })
    pd.DataFrame(content).to_csv('content.csv', index=False)
    
    print("Generated 4 CSV files successfully.")

if __name__ == '__main__':
    generate_data()
