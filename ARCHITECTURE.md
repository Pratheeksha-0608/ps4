# Creator Content Posting Optimization System - Architecture & Implementation Guide

## 🎯 System Overview

This is a sophisticated content posting optimization system that helps creators determine the best time and platform to post content to maximize engagement. The system uses:

- **Weighted Scoring Formula**: Combines creator engagement history with platform activity data
- **Max-Heap Priority Queue**: Efficiently finds the best platform + time slot combination
- **Constraint Satisfaction**: Respects creator cooldown periods and content sensitivity levels
- **Intelligent Timing Decisions**: Determines whether content should post IMMEDIATELY or be SCHEDULED

---

## 📊 Algorithm Details

### 1. Weighted Scoring Formula

```
score = (creator_engagement × 0.60) + (platform_activity × 0.40)
```

Where:
- **creator_engagement (60% weight)**: Historical average engagement for this creator-platform-content-timeslot combination
- **platform_activity (40% weight)**: General platform activity level at this time slot

**Fallback Strategy**: If no historical data exists for a specific combination:
1. Try to find data for the creator-platform-content-timeslot
2. Fall back to the creator's `base_engagement` value
3. Final fallback: Use 1.0 (neutral engagement)

### 2. Platform and Time Slot Selection

The algorithm evaluates **all 48 combinations** (2 platforms × 24 time slots):
- Instagram: 0-23 (midnight to 11 PM)
- YouTube: 0-23 (midnight to 11 PM)

**Implementation**: Max-Heap Priority Queue
- Uses Python's `heapq` module (min-heap, so we negate scores for max behavior)
- Time Complexity: O(48 log 48) ≈ O(1) per content item
- Ensures deterministic, greedy selection of the highest-scoring combination

### 3. Timing Decision Logic

Determines whether to post IMMEDIATELY or SCHEDULED:

```
if time_sensitivity == "High":
    decision = "IMMEDIATE"  # Always post now for high-urgency content

elif time_sensitivity == "Medium":
    time_diff = |best_time_slot - created_timestamp|
    if time_diff <= 2 hours:  # Account for 24-hour wraparound
        decision = "IMMEDIATE"
    else:
        decision = "SCHEDULED"

else:  # time_sensitivity == "Low"
    decision = "SCHEDULED"  # Always schedule for low-priority content
```

### 4. Cooldown Constraint Satisfaction

Each creator has a `cooldown_hours` period that must elapse between posts. The system:
1. Checks if the content creation falls within the cooldown window
2. Flags with `cooldown_ok` status
3. Warning system alerts users to cooldown violations

---

## 📁 Data Structure

### Input Datasets

#### content.csv
```
content_id, creator_id, content_type, created_timestamp, time_sensitivity
"1", "24", "LONG", "6", "Medium"
"2", "43", "LONG", "22", "Medium"
```

**Fields**:
- `content_id`: Unique identifier for content
- `creator_id`: Creator who posted this content
- `content_type`: "SHORT" or "LONG" form content
- `created_timestamp`: Hour (0-23) when content was submitted
- `time_sensitivity`: "High", "Medium", or "Low" urgency

#### creators.csv
```
creator_id, base_engagement, cooldown_hours
"1", "1.11", "4"
"2", "0.62", "6"
```

**Fields**:
- `creator_id`: Unique creator identifier
- `base_engagement`: Default engagement multiplier (fallback value)
- `cooldown_hours`: Minimum hours between posts for this creator

#### historical_engagement.csv
```
creator_id, platform, content_type, time_slot, avg_engagement
1, Instagram, SHORT, 0, 0.476
1, Instagram, SHORT, 1, 0.469
```

**Fields**:
- `creator_id`: Creator identifier
- `platform`: "Instagram" or "YouTube"
- `content_type`: "SHORT" or "LONG"
- `time_slot`: Hour (0-23)
- `avg_engagement`: Historical average engagement at this combination

#### platform_activity.csv
```
platform, time_slot, activity_score
Instagram, 0, 0.6
Instagram, 1, 0.6
```

**Fields**:
- `platform`: "Instagram" or "YouTube"
- `time_slot`: Hour (0-23)
- `activity_score`: Platform activity level (0-1 typically)

### Output Dataset

#### output.csv / recommendations.csv
```
content_id, creator_id, recommended_platform, best_time_slot, timing, final_score, cooldown_ok
"1", "24", "Instagram", "12", "SCHEDULED", "0.7823", "true"
"2", "43", "YouTube", "18", "IMMEDIATE", "0.9156", "true"
```

**Fields**:
- `content_id`: Original content identifier
- `creator_id`: Creator identifier
- `recommended_platform`: "Instagram" or "YouTube" (selected based on score)
- `best_time_slot`: Hour (0-23) with highest engagement potential
- `timing`: "IMMEDIATE" or "SCHEDULED"
- `final_score`: Weighted engagement score (0-1+)
- `cooldown_ok`: Whether cooldown constraint is satisfied

---

## 🏗️ Code Architecture

### Key Functions

#### Data Loading & Validation
```python
def load_csv_from_upload(uploaded_file)
def validate_content_data(df)
def validate_creators_data(df)
def validate_engagement_history(df)
def validate_platform_activity(df)
```

**Purpose**: Load and validate all input datasets, ensuring data integrity before processing.

#### Scoring Engine
```python
def get_avg_engagement(creator_id, platform, content_type, time_slot, 
                       engagement_history, creators_df)
    → Returns historical engagement (or fallback to base_engagement)

def calculate_score(creator_engagement, platform_activity, 
                   creator_weight=0.60, platform_weight=0.40)
    → Applies weighted formula to generate score

def find_best_posting_slot(content_row, engagement_history, creators_df, 
                          platform_activity_df)
    → Uses max-heap to find best platform+time slot combination
```

#### Optimization Pipeline
```python
def is_cooldown_respected(content_row, creators_df)
    → Checks cooldown constraint

def decide_timing(content_row, best_slot)
    → Determines IMMEDIATE vs SCHEDULED based on sensitivity

def generate_recommendations(content_df, creators_df, engagement_history_df, 
                            platform_activity_df)
    → Main orchestration function that processes all content items
```

#### Visualization
```python
def create_time_slot_visualization(...)
    → Bar chart showing scores for all time slots

def create_platform_distribution_chart(...)
    → Pie chart of platform distribution

def create_timing_distribution_chart(...)
    → Pie chart of IMMEDIATE vs SCHEDULED

def create_time_slot_distribution_chart(...)
    → Histogram of recommended time slots
```

#### Streamlit UI
```python
def main()
    → Main Streamlit application with:
        • File uploads for all 4 datasets
        • Data validation interface
        • Optimization execution
        • Results table with sorting/filtering
        • Multiple visualization tabs
        • Export functionality (CSV download)
        • Alert/warning system for violations
```

---

## 🚀 Running the Application

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Navigate to the project directory**:
```bash
cd ps4
```

3. **Run Streamlit**:
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### Workflow

1. **Upload CSV Files**: Use the sidebar to upload all 4 required CSV files
2. **Validate Data**: Click "Validate Data" to check for errors
3. **Run Optimization**: Click "Run Optimization" to generate recommendations
4. **View Results**: Explore the results table, visualizations, and metrics
5. **Export**: Download recommendations as CSV or save to output.csv

---

## 🔍 Validation Rules

### Content Data Validation
- ✅ All required columns present: content_id, creator_id, content_type, created_timestamp, time_sensitivity
- ✅ time_sensitivity values must be: "High", "Medium", or "Low"
- ✅ created_timestamp must be 0-23 (valid hour)

### Creators Data Validation
- ✅ All required columns present: creator_id, base_engagement, cooldown_hours
- ✅ base_engagement and cooldown_hours must be numeric

### Historical Engagement Validation
- ✅ All required columns present: creator_id, platform, content_type, time_slot, avg_engagement
- ✅ time_slot must be 0-23
- ✅ platform must be "Instagram" or "YouTube"

### Platform Activity Validation
- ✅ All required columns present: platform, time_slot, activity_score
- ✅ time_slot must be 0-23
- ✅ platform must be "Instagram" or "YouTube"

---

## 📊 Output Metrics

The system generates comprehensive analytics:

**Summary Metrics**:
- Total Recommendations
- IMMEDIATE Posts (count + %)
- SCHEDULED Posts (count + %)
- Instagram Posts (count + %)
- YouTube Posts (count + %)
- Average Score

**Visualizations**:
1. **Platform Distribution**: Pie chart showing Instagram vs YouTube split
2. **Timing Distribution**: Pie chart showing IMMEDIATE vs SCHEDULED split
3. **Time Slot Distribution**: Histogram of all 24 time slots
4. **Detailed Analysis**: Interactive bar charts for specific content items

**Alerts**:
- ⚠️ Cooldown violations detected
- ℹ️ Low-score content items flagged for review

---

## 🎛️ Customization

### Adjusting Weights

Edit the weights in `calculate_score()`:
```python
def calculate_score(creator_engagement, platform_activity, 
                   creator_weight=0.60, platform_weight=0.40):
    return (creator_engagement * creator_weight) + (platform_activity * platform_weight)
```

**Examples**:
- Creator-focused: (0.70, 0.30) - Prioritize creator's history
- Platform-focused: (0.40, 0.60) - Prioritize platform activity
- Balanced: (0.50, 0.50) - Equal weight

### Adjusting Timing Thresholds

Edit the window in `decide_timing()`:
```python
if time_diff <= 2:  # Change from 2 hours
    return 'IMMEDIATE'
```

### Adding New Platforms

1. Add platform values to validation functions
2. Ensure platform_activity.csv includes all platforms
3. Ensure historical_engagement.csv includes all platforms

---

## ⚡ Performance Characteristics

**Time Complexity**:
- Per Content Item: O(48 log 48) + O(data lookup) ≈ O(1)
- Total for N items: O(N)
- Typical runtime: < 1 second for 1000+ items

**Space Complexity**:
- O(H) where H = size of historical engagement data
- Typical: < 100MB for reasonable datasets

---

## 🐛 Error Handling

The system gracefully handles:
- ✅ Missing files (validation will fail)
- ✅ Invalid data types (auto-converts numeric columns)
- ✅ Missing engagement history (falls back to base_engagement)
- ✅ Malformed timestamps (validation catches and reports)
- ✅ Missing creators (assumes unknown creator, returns neutral engagement)

---

## 📝 Algorithm Decision Log

### Key Design Decisions

1. **Why 60/40 Split for Weights?**
   - Creator's historical performance is more reliable signal than platform-wide activity
   - Historical data is creator-specific and actionable
   - Platform activity provides context but is less personalized

2. **Why Max-Heap Priority Queue?**
   - Ensures optimal greedy selection
   - O(1) amortized time per content item
   - Deterministic: always picks the best score
   - Scales efficiently with more platforms/time slots

3. **Why Two-Hour Window for Medium Sensitivity?**
   - Balances urgency with optimization
   - Allows slightly delayed posting if significantly better score
   - Prevents long delays for moderately urgent content

4. **Why Fallback to Base Engagement?**
   - Missing historical data is common for new creator-platform pairs
   - Base engagement provides reasonable default
   - Prevents zero-engagement calculations

5. **Why Independent Platform+TimeSlot Evaluation?**
   - Platform affinity is already captured in historical engagement
   - Avoids hardcoded rules (e.g., "reels on Instagram")
   - Allows algorithm to discover platform preferences from data

---

## 🔐 Data Privacy & Security

- ✅ No data is stored on servers - runs locally in Streamlit
- ✅ All processing happens in-memory
- ✅ CSV exports are created only locally
- ✅ No external API calls
- ✅ No user data collection

---

## 📚 Further Reading

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Python heapq Module](https://docs.python.org/3/library/heapq.html)
- [Plotly Visualization](https://plotly.com/python/)

---

## 👥 Support & Contributions

For issues, questions, or improvements, please refer to the ISSUES.md file in this repository.

---

**Version**: 1.0  
**Last Updated**: May 2026  
**Status**: Production Ready
