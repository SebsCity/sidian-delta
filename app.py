import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os

# ==========================================
# CONFIG & UI SETUP
# ==========================================
st.set_page_config(page_title="Sidian Bonus Lab PRO", layout="wide", page_icon="🚀")
st.title("🎯 Sidian Bonus Lab PRO")
st.caption("Engine: Correlation + Decay + Frequency (Space-Separated Input)")

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
        # Load only valid, non-null data to prevent 'nan' errors
        df = pd.read_sql("SELECT numbers, bonus FROM draws WHERE bonus IS NOT NULL", conn)
        df = df.dropna()
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_engine_scores(bonus_series):
    # Ensure series is numeric and clean
    bonus_series = pd.to_numeric(bonus_series, errors='coerce').dropna().astype(int)
    
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_s = (freq - freq.min()) / (freq.max() - freq.min()) if freq.max() > freq.min() else freq
    
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min()) if gaps.max() > gaps.min() else gaps
    
    return (0.70 * gap_s) + (0.30 * freq_s), gaps

# ==========================================
# SIDEBAR CONTROL
# ==========================================
st.sidebar.header("📊 Sidian Data Control")
mode = st.sidebar.selectbox("Action", ["Prediction Hub", "Upload Draw Data", "View History"])

history_df = load_data()

# ==========================================
# MODE: UPLOAD DATA
# ==========================================
if mode == "Upload Draw Data":
    st.subheader("Add New History")
    file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
    if file:
        df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        # Drop rows with missing Bonus values to prevent 'nan' in DB
        df_new = df_new.dropna(subset=['Bonus'])
        
        if st.button("Save to Sidian Database"):
            conn = sqlite3.connect(DB_PATH)
            # Combine main numbers for correlation scanning
            df_new['numbers'] = df_new[['Main_1','Main_2','Main_3','Main_4','Main_5','Main_6']].astype(str).agg(','.join, axis=1)
            df_new[['numbers', 'Bonus']].to_sql("draws", conn, if_exists="append", index=False)
            conn.close()
            st.success("Database Cleaned & Updated!")

# ==========================================
# MODE: PREDICTION HUB
# ==========================================
elif mode == "Prediction Hub":
    if history_df.empty:
        st.warning("History is empty. Upload data first.")
    else:
        bonus_series = history_df['bonus']
        base_scores, current_gaps = get_engine_scores(bonus_series)

        st.header("🔮 Manual Draw Trigger")
        st.write("Paste your 6 Main Numbers separated by **Spaces**:")
        
        with st.form("trigger_form"):
            # Switched to space-only input
            raw_input = st.text_input("Draw numbers:", placeholder="e.g. 7 14 22 31 38 45")
            submitted = st.form_submit_button("Predict Bonus")
            
            if submitted:
                if raw_input:
                    try:
                        # Logic: Split by any whitespace and ignore non-numeric 'nan' strings
                        current_draw = [int(x) for x in raw_input.split() if x.isdigit()]
                        
                        if len(current_draw) > 0:
                            buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))
                            
                            for row in history_df.itertuples():
                                # Clean data while loading for the correlation scan
                                try:
                                    hist_nums = [int(float(x)) for x in str(row.numbers).split(',') if x.strip() != 'nan']
                                    match_count = len(set(current_draw).intersection(set(hist_nums)))
                                    if match_count > 0:
                                        buddy_weights[int(row.bonus)] += (match_count ** 2)
                                except: continue
                            
                            buddy_s = (buddy_weights / buddy_weights.max()) if buddy_weights.max() > 0 else buddy_weights
                            final_prediction = (0.75 * buddy_s) + (0.25 * base_scores)
                            top_3 = final_prediction.nlargest(3)
                            
                            st.subheader("🎯 Result: Top 3 Probability Sequence")
                            cols = st.columns(3)
                            for i, (num, val) in enumerate(top_3.items()):
                                with cols[i]:
                                    st.metric(f"Rank {i+1}", f"#{num}")
                                    st.progress(min(val, 1.0))
                        else:
                            st.error("No valid numbers found. Type numbers like: 7 14 22")
                    except Exception as e:
                        st.error(f"Error: Check your input format.")
                else:
                    st.error("Input is empty.")

        # Visual Decay
        st.divider()
        st.subheader("📊 Overdue Pressure (Decay)")
        fig = px.bar(x=current_gaps.index, y=current_gaps.values, color=current_gaps.values, color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

elif mode == "View History":
    st.subheader("Archive")
    st.dataframe(history_df)
