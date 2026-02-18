import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os
from scipy.stats import zscore

# ==========================================
# CONFIG & UI SETUP
# ==========================================
st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🚀")
st.title("🎯 Sidian Bonus Lab PRO")
st.caption("Precision Hybrid Probability Engine: Correlation + Decay + Frequency")

MAX_NUMBER = 49
DB_PATH = "database/draws.db"

# ==========================================
# DATABASE & UTILS
# ==========================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM draws", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# ==========================================
# ADVANCED SCORING ENGINE
# ==========================================
def get_engine_scores(bonus_series):
    # 1. Frequency Score
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_s = (freq - freq.min()) / (freq.max() - freq.min()) if freq.max() > freq.min() else freq
    
    # 2. Recency / Gap Analysis
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min()) if gaps.max() > gaps.min() else gaps
    
    # 3. Momentum (Recent 50)
    momentum = bonus_series.iloc[-50:].value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    mom_s = momentum / momentum.max() if momentum.max() > 0 else momentum
    
    # Combine (60% Pressure/Gap, 20% Freq, 20% Momentum)
    final_base = (0.60 * gap_s) + (0.20 * freq_s) + (0.20 * mom_s)
    return final_base, gaps

# ==========================================
# SIDEBAR CONTROL
# ==========================================
st.sidebar.header("📊 Sidian Data Control")
mode = st.sidebar.selectbox("Action", ["Prediction Hub", "Upload Draw Data", "View History"])

# ==========================================
# MAIN LOGIC
# ==========================================
history_df = load_data()

if mode == "Upload Draw Data":
    st.subheader("Add New History")
    file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
    if file:
        df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        # Assuming columns: Main_1, Main_2, Main_3, Main_4, Main_5, Main_6, Bonus
        st.write("Preview:", df_new.head(3))
        if st.button("Save to Sidian Database"):
            conn = sqlite3.connect(DB_PATH)
            # Flatten main numbers to string for storage
            df_new['numbers'] = df_new[['Main_1','Main_2','Main_3','Main_4','Main_5','Main_6']].astype(str).agg(','.join, axis=1)
            df_new[['numbers', 'Bonus']].to_sql("draws", conn, if_exists="append", index=False)
            conn.close()
            st.success("Data successfully merged!")

elif mode == "Prediction Hub":
    if history_df.empty:
        st.warning("Please upload draw history first.")
    else:
        bonus_series = history_df['bonus'].astype(int)
        base_scores, current_gaps = get_engine_scores(bonus_series)

        st.header("🔮 Manual Draw Predictor")
        st.write("Paste your current 6 Main Numbers to find the highest probability Bonus.")
        
        raw_input = st.text_input("Enter draw (comma separated):", placeholder="e.g. 7, 14, 22, 31, 38, 45")
        
        if raw_input:
            try:
                # 1. Parse Input
                current_draw = [int(x.strip()) for x in raw_input.split(',') if x.strip().isdigit()]
                
                if len(current_draw) > 0:
                    # 2. Correlation Analysis (The 'Buddy' Logic)
                    buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))
                    
                    for row in history_df.itertuples():
                        hist_nums = [int(x) for x in str(row.numbers).split(',')]
                        # Calculate how many numbers match the current draw
                        match_count = len(set(current_draw).intersection(set(hist_nums)))
                        if match_count > 0:
                            # Heavier weight for more matches
                            buddy_weights[row.bonus] += (match_count ** 2)
                    
                    # Normalize Buddy Score
                    buddy_s = (buddy_weights / buddy_weights.max()) if buddy_weights.max() > 0 else buddy_weights
                    
                    # 3. Final Hybrid Calculation (70% Correlation, 30% Base Stats)
                    final_prediction = (0.70 * buddy_s) + (0.30 * base_scores)
                    
                    # Display TOP 3
                    top_3 = final_prediction.nlargest(3)
                    total_p = top_3.sum()
                    
                    st.divider()
                    st.subheader(f"🎯 Top 3 Predicted Bonuses for Draw: {current_draw}")
                    cols = st.columns(3)
                    for i, (num, val) in enumerate(top_3.items()):
                        confidence = (val / total_p) * 100
                        with cols[i]:
                            st.metric(f"Possibility {i+1}", f"#{num}", f"{confidence:.1f}% Confidence")
                            st.progress(int(confidence))
                            st.caption(f"Pressure Index: {int(current_gaps[num])} draws overdue")
                
                else: st.error("Please enter at least one number.")
            except Exception as e:
                st.error(f"Input Error: {e}")

        # --- Visual Decay Map ---
        st.divider()
        st.subheader("📊 Bonus Ball Decay Heatmap")
        fig = px.bar(x=current_gaps.index, y=current_gaps.values, color=current_gaps.values,
                     color_continuous_scale='Reds', labels={'x':'Ball Number', 'y':'Draws Since Seen'})
        st.plotly_chart(fig, use_container_width=True)

elif mode == "View History":
    st.subheader("Sidian Draw Archives")
    st.dataframe(history_df, use_container_width=True)
