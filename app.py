import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & SESSION STATE
# ==========================================
st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🚀")

st.title("🎯 Sidian Bonus Lab: Ripple Edition")
st.caption("Predicting Bonus Balls + The 'Splits' (Next Main Numbers) Due to Follow")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE LOGIC
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY AUTOINCREMENT, numbers TEXT, bonus INTEGER)")
    conn.commit()
    conn.close()

init_db()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT numbers, bonus FROM draws", conn)
    conn.close()
    return df

# ==========================================
# RIPPLE ENGINE (Predicts Main Numbers following a Bonus)
# ==========================================
def get_historical_splits(history_df, target_bonus):
    """Finds the main numbers that follow a specific bonus in the next draw."""
    splits = []
    # Loop through history to find where the bonus matches
    for i in range(len(history_df) - 1):
        if int(history_df.iloc[i]['bonus']) == target_bonus:
            # Get the main numbers from the NEXT draw (the 'split')
            next_draw_nums = str(history_df.iloc[i+1]['numbers']).split(',')
            splits.extend([int(float(x)) for x in next_draw_nums if x != 'nan'])
    
    if splits:
        return pd.Series(splits).value_counts().head(3).index.tolist()
    return []

# ==========================================
# PREDICTION ENGINE
# ==========================================
def run_prediction_engine(history_df, manual_input_str):
    bonus_series = pd.to_numeric(history_df['bonus'], errors='coerce').dropna().astype(int)
    
    # 1. Base Stats
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_s = (freq - freq.min()) / (freq.max() - freq.min()) if freq.max() > freq.min() else freq
    
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min()) if gaps.max() > gaps.min() else gaps
    
    # 2. Buddy Correlation
    current_draw = [int(x) for x in manual_input_str.split() if x.isdigit()]
    buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))
    
    for row in history_df.itertuples():
        hist_nums = [int(float(x)) for x in str(row.numbers).split(',') if x != 'nan']
        match_count = len(set(current_draw).intersection(set(hist_nums)))
        if match_count > 0:
            buddy_weights[int(row.bonus)] += (match_count ** 2)
    
    buddy_s = (buddy_weights / buddy_weights.max()) if buddy_weights.max() > 0 else buddy_weights
    
    final_score = (0.70 * buddy_s) + (0.30 * gap_s)
    return final_score.nlargest(3), gaps

# ==========================================
# UI LAYOUT
# ==========================================
history = get_history()

with st.sidebar:
    st.header("⚙️ Data Management")
    file = st.file_uploader("Refresh History", type=["xlsx", "csv"])
    if file:
        df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        if st.button("Commit to Database"):
            conn = sqlite3.connect(DB_PATH)
            df_new['numbers'] = df_new[['Main_1','Main_2','Main_3','Main_4','Main_5','Main_6']].astype(str).agg(','.join, axis=1)
            df_new[['numbers', 'Bonus']].to_sql("draws", conn, if_exists="replace", index=False)
            conn.close()
            st.success("Synced!")
            st.rerun()

st.subheader("🔮 Step 1: Input Current Draw")
with st.form("main_form"):
    manual_input = st.text_input("Paste 6 Main Numbers (Space separated)", placeholder="e.g. 1 14 23 35 40 44")
    submitted = st.form_submit_button("Generate Predicted Bonuses & Follow-up Splits")

if submitted and not history.empty:
    top3, gaps = run_prediction_engine(history, manual_input)
    
    st.divider()
    st.subheader("🎯 Result: Top 3 Bonus Possibilities & Predicted Splits")
    
    cols = st.columns(3)
    for i, (bonus_num, weight) in enumerate(top3.items()):
        with cols[i]:
            # Bonus Prediction Card
            st.metric(f"Rank {i+1} Bonus", f"#{bonus_num}")
            st.caption(f"Confidence: {int(weight*100)}% | Gap: {gaps[bonus_num]} draws")
            
            # --- THE SPLITS LOGIC ---
            st.markdown("---")
            st.markdown("**Predicted Next-Draw Splits:**")
            predicted_splits = get_historical_splits(history, bonus_num)
            
            if predicted_splits:
                # Display splits as little tags
                split_html = "".join([f"<span style='background-color:#007BFF; color:white; padding:5px 10px; border-radius:15px; margin-right:5px;'>{s}</span>" for s in predicted_splits])
                st.markdown(split_html, unsafe_allow_html=True)
                st.caption("These main numbers often follow this Bonus.")
            else:
                st.caption("No historical follow-up data yet.")

elif history.empty:
    st.info("Please upload your data sheet in the sidebar to begin.")

# Visualizations...
if not history.empty:
    st.divider()
    fig = px.bar(x=gaps.index, y=gaps.values, color=gaps.values, color_continuous_scale='Reds', title="Bonus Ball Overdue Pressure (Decay)")
    st.plotly_chart(fig, use_container_width=True)
