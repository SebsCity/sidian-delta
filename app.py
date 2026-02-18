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

def get_engine_scores(bonus_series):
    # Frequency Score
    freq = bonus_series.value_counts().reindex(range(1, MAX_NUMBER+1), fill_value=0)
    freq_s = (freq - freq.min()) / (freq.max() - freq.min()) if freq.max() > freq.min() else freq
    
    # Recency / Gap Analysis
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER: last_seen[val] = idx
    gaps = pd.Series([len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)], index=range(1, MAX_NUMBER+1))
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min()) if gaps.max() > gaps.min() else gaps
    
    # Final Score (Weighted toward overdue)
    final_base = (0.70 * gap_s) + (0.30 * freq_s)
    return final_base, gaps

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
        st.write("Preview:", df_new.head(3))
        if st.button("Save to Sidian Database"):
            conn = sqlite3.connect(DB_PATH)
            # Assuming columns: Main_1, Main_2... Bonus
            df_new['numbers'] = df_new[['Main_1','Main_2','Main_3','Main_4','Main_5','Main_6']].astype(str).agg(','.join, axis=1)
            df_new[['numbers', 'Bonus']].to_sql("draws", conn, if_exists="append", index=False)
            conn.close()
            st.success("Database Updated!")

# ==========================================
# MODE: PREDICTION HUB
# ==========================================
elif mode == "Prediction Hub":
    if history_df.empty:
        st.warning("Please upload draw history first.")
    else:
        bonus_series = history_df['bonus'].astype(int)
        base_scores, current_gaps = get_engine_scores(bonus_series)

        st.header("🔮 Manual Draw Trigger")
        
        # FIXED: Using st.form to ensure input is captured before processing
        with st.form("trigger_form"):
            raw_input = st.text_input("Paste Draw Numbers (e.g. 7, 14, 22, 31, 38, 45)")
            submitted = st.form_submit_button("Calculate Top 3 Bonus Balls")
            
            if submitted:
                if raw_input:
                    try:
                        current_draw = [int(x.strip()) for x in raw_input.replace(' ', ',').split(',') if x.strip().isdigit()]
                        
                        if len(current_draw) > 0:
                            # Correlation Calculation
                            buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))
                            for row in history_df.itertuples():
                                hist_nums = [int(x) for x in str(row.numbers).split(',')]
                                match_count = len(set(current_draw).intersection(set(hist_nums)))
                                if match_count > 0:
                                    buddy_weights[row.bonus] += (match_count ** 2)
                            
                            buddy_s = (buddy_weights / buddy_weights.max()) if buddy_weights.max() > 0 else buddy_weights
                            final_prediction = (0.75 * buddy_s) + (0.25 * base_scores)
                            top_3 = final_prediction.nlargest(3)
                            
                            st.subheader("🎯 Result: Top 3 Predicted Bonuses")
                            cols = st.columns(3)
                            for i, (num, val) in enumerate(top_3.items()):
                                with cols[i]:
                                    st.metric(f"Rank {i+1}", f"#{num}")
                                    st.progress(min(val, 1.0))
                        else:
                            st.error("Numbers not recognized. Use commas like: 1, 2, 3...")
                    except Exception as e:
                        st.error(f"Error processing numbers: {e}")
                else:
                    st.error("Please enter the main draw numbers first.")

        # Visual Decay Map
        st.divider()
        st.subheader("📊 Overdue Pressure (Decay)")
        fig = px.bar(x=current_gaps.index, y=current_gaps.values, color=current_gaps.values, color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MODE: VIEW HISTORY
# ==========================================
elif mode == "View History":
    st.subheader("Draw Archive")
    st.dataframe(history_df, use_container_width=True)
