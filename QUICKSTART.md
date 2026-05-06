# Quick Start Guide - Creator Content Posting Optimizer

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`.

### Step 3: Upload Your Data
In the left sidebar, upload these files:
1. **content.csv** - Your content submissions
2. **creators.csv** - Creator information
3. **historical_engagement.csv** - Past engagement history
4. **platform_activity.csv** - Platform activity data

### Step 4: Validate Data
Click **"Validate Data"** to ensure all files are correctly formatted.

You should see ✅ checkmarks for each validated dataset.

### Step 5: Run Optimization
Click **"Run Optimization"** to generate recommendations.

This will:
- Analyze all platform-time combinations
- Calculate engagement scores
- Select optimal posting strategies
- Generate warnings for violations

### Step 6: Explore Results
You'll see:
- **Summary Metrics** showing breakdown of recommendations
- **Results Table** with all recommendations (sortable/filterable)
- **Visualizations** showing patterns and distributions
- **Alerts** for any issues (cooldown violations, low scores)

### Step 7: Export Results
Download recommendations as CSV or automatically save to `output.csv`

---

## 📊 Understanding the Results

### Output Fields

| Field | Meaning | Example |
|-------|---------|---------|
| `content_id` | Your content identifier | "1" |
| `creator_id` | Creator who posted | "24" |
| `recommended_platform` | Where to post | "Instagram" |
| `best_time_slot` | When to post (0-23) | "14" (2 PM) |
| `timing` | Post strategy | "SCHEDULED" |
| `final_score` | Engagement potential | "0.7823" |
| `cooldown_ok` | No cooldown violation | "True" |

### Score Interpretation

- **0.0 - 0.3**: Low engagement potential, consider alternative strategy
- **0.3 - 0.6**: Moderate engagement potential
- **0.6 - 0.8**: Good engagement potential, recommended
- **0.8+**: Excellent engagement potential, high priority

### Timing Meanings

- **IMMEDIATE**: Post right now for maximum urgency/relevance
- **SCHEDULED**: Wait for the recommended time slot for better engagement

---

## 🎛️ Sample Data Format

### content.csv
```csv
content_id,creator_id,content_type,created_timestamp,time_sensitivity
1,24,LONG,6,Medium
2,43,LONG,22,Medium
3,44,SHORT,19,Medium
```

### creators.csv
```csv
creator_id,base_engagement,cooldown_hours
1,1.11,4
2,0.62,6
3,0.82,6
```

### historical_engagement.csv
```csv
creator_id,platform,content_type,time_slot,avg_engagement
1,Instagram,SHORT,0,0.476
1,Instagram,SHORT,1,0.469
1,Instagram,SHORT,2,0.859
```

### platform_activity.csv
```csv
platform,time_slot,activity_score
Instagram,0,0.6
Instagram,1,0.6
YouTube,0,0.7
```

---

## ❓ FAQ

**Q: What if I don't have historical engagement data?**  
A: The system will use each creator's `base_engagement` value as a fallback. It will still provide recommendations.

**Q: Can I use my own data files?**  
A: Yes! Just make sure they match the column names and data types described above.

**Q: Why is one platform recommended over another?**  
A: The algorithm scores all platform+time combinations and picks the highest score based on:
- Creator's historical performance on that platform at that time
- Platform's activity level at that time
- Your configured weights (60% creator, 40% platform)

**Q: What does cooldown mean?**  
A: It's the minimum hours required between posts from the same creator. For example, if cooldown_hours=6, creator can't post more often than every 6 hours.

**Q: Can I modify the weights?**  
A: Yes! Edit the `calculate_score()` function in `app.py` to adjust the 60/40 split.

**Q: How long does it take to generate recommendations?**  
A: Usually < 1 second for most datasets. Time scales linearly with number of content items.

**Q: Can I add new platforms?**  
A: Yes, just add them to your platform_activity.csv with activity scores for each time slot.

---

## 🐛 Troubleshooting

### Error: "Please upload all required CSV files"
→ Make sure all 4 files are uploaded before running optimization

### Error: "Invalid time_sensitivity values"
→ Use only: "High", "Medium", or "Low" (case-sensitive)

### Error: "Invalid platforms"
→ Use only: "Instagram" or "YouTube" (exact spelling)

### Error: "Invalid time slots"
→ Time slots must be 0-23 (representing hours 0:00 to 23:00)

### Error: "base_engagement and cooldown_hours must be numeric"
→ Ensure these columns contain numbers, not text

### App won't start
→ Make sure you have all requirements installed:
```bash
pip install -r requirements.txt
```

---

## 💡 Tips & Tricks

1. **Sort by Score**: Click on the "final_score" column header to find your best recommendations
2. **Filter by Platform**: Use the platform filter to focus on Instagram or YouTube recommendations
3. **Analyze Specifics**: Use the "Detailed Analysis" tab to see why a specific content got its recommendation
4. **Check Warnings**: Always review the "Alerts" section for potential issues
5. **Export Often**: Download results after each run to track changes

---

## 📈 Advanced Usage

### Batch Processing
```bash
# Add your content CSV path here and run optimization programmatically
python app.py
```

### Custom Weights
Modify this line in `app.py`:
```python
score = calculate_score(creator_eng, platform_activity, creator_weight=0.60, platform_weight=0.40)
```

Change weights like:
```python
# More creator-focused
score = calculate_score(creator_eng, platform_activity, creator_weight=0.70, platform_weight=0.30)

# More platform-focused  
score = calculate_score(creator_eng, platform_activity, creator_weight=0.50, platform_weight=0.50)
```

### Adjusting Timing Windows
```python
# In decide_timing() function, change:
if time_diff <= 2:  # Change 2 to your preferred hour threshold
    return 'IMMEDIATE'
```

---

## 📞 Getting Help

1. Check ARCHITECTURE.md for detailed algorithm explanations
2. Review ISSUES.md for project requirements
3. Look at the comments in app.py for code-level documentation

---

**Ready to optimize your posting strategy? Run `streamlit run app.py` now!**
