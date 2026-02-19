import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import os
from itertools import combinations

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Sidian Bonus Lab PRO",
    layout="wide",
    page_icon="🚀"
)

st.title("🎯 Sidian Bonus Lab: Ripple Intelligence PRO")
st.caption("Advanced Bonus Ball & Follow-Triples Prediction Engine")

MAX_NUMBER = 49
DB_PATH = "draws.db"   # ✅ root-level DB (Cloud safe)

# ======================================================
# DATABASE INITIALIZATION
# ======================================================
def init_db():
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

# ======================================================
# DATABASE ACCESS
# ======================================================
def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT numbers, bonus FROM draws ORDER BY id ASC", conn)
    conn.close()
    return df

# ======================================================
# ADVANCED TRIPLE GENERATOR
# ======================================================
def generate_advanced_triples(history_df, target_bonus):

    follow_numbers = []

    # Collect next-draw numbers after the predicted bonus
    for i in range(len(history_df) - 1):
        try:
            if int(history_df.iloc[i]["bonus"]) == target_bonus:
                next_nums = str(history_df.iloc[i+1]["numbers"]).split(',')
                cleaned = [
                    int(float(x)) for x in next_nums
                    if str(x).lower() != "nan"
                ]
                if len(cleaned) >= 3:
                    follow_numbers.append(cleaned)
        except:
            continue

    if not follow_numbers:
        return []

    # Frequency weight
    flat = [n for sub in follow_numbers for n in sub]
    freq = pd.Series(flat).value_counts()

    triple_scores = {}

    for draw in follow_numbers:
        for triple in combinations(draw, 3):
            triple = tuple(sorted(triple))
            score = sum(freq.get(n, 0) for n in triple)
            triple_scores[triple] = triple_scores.get(triple, 0) + score

    if not triple_scores:
        return []

    ranked = sorted(triple_scores.items(), key=lambda x: x[1], reverse=True)

    return [combo for combo, _ in ranked[:3]]

# ======================================================
# BONUS PREDICTION ENGINE
# ======================================================
def run_prediction_engine(history_df, manual_input_str):

    try:
        bonus_series = pd.to_numeric(
            history_df["bonus"], errors="coerce"
        ).dropna().astype(int)
    except:
        return None, None

    if bonus_series.empty:
        return None, None

    # Frequency
    freq = bonus_series.value_counts().reindex(
        range(1, MAX_NUMBER+1), fill_value=0
    )

    # Gap analysis
    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER:
            last_seen[val] = idx

    gaps = pd.Series(
        [len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)],
        index=range(1, MAX_NUMBER+1)
    )

    # Normalize
    freq_s = (freq - freq.min()) / (freq.max() - freq.min() + 1e-9)
    gap_s = (gaps - gaps.min()) / (gaps.max() - gaps.min() + 1e-9)

    # Buddy correlation
    current_draw = [
        int(x) for x in manual_input_str.split()
        if x.isdigit()
    ]

    buddy_weights = pd.Series(0.0, index=range(1, MAX_NUMBER+1))

    for row in history_df.itertuples():
        try:
            hist_nums = [
                int(float(x))
                for x in str(row.numbers).split(',')
                if str(x).lower() != "nan"
            ]
            match_count = len(set(current_draw).intersection(hist_nums))
            if match_count > 0:
                buddy_weights[int(row.bonus)] += (match_count ** 2)
        except:
            continue

    buddy_s = (
        buddy_weights / buddy_weights.max()
        if buddy_weights.max() > 0
        else buddy_weights
    )

    final_score = (0.6 * buddy_s) + (0.4 * gap_s)

    return final_score.nlargest(3), gaps

# ======================================================
# SIDEBAR DATA MANAGEMENT
# ======================================================
history = get_history()

with st.sidebar:
    st.header("⚙️ Data Management")

    uploaded = st.file_uploader(
        "Upload Historical Draws",
        type=["csv", "xlsx"]
    )

    if uploaded:

        try:
            if uploaded.name.endswith(".xlsx"):
                df_new = pd.read_excel(uploaded)
            else:
                df_new = pd.read_csv(uploaded)

            st.success("File Loaded Successfully")

            if st.button("Commit to Database"):

                required_cols = [
                    "Main_1","Main_2","Main_3",
                    "Main_4","Main_5","Main_6","Bonus"
                ]

                if all(col in df_new.columns for col in required_cols):

                    df_new["numbers"] = (
                        df_new[required_cols[:6]]
                        .astype(str)
                        .agg(",".join, axis=1)
                    )

                    conn = sqlite3.connect(DB_PATH)
                    df_new[["numbers","Bonus"]].rename(
                        columns={"Bonus":"bonus"}
                    ).to_sql(
                        "draws",
                        conn,
                        if_exists="replace",
                        index=False
                    )
                    conn.close()

                    st.success("Database Updated Successfully!")
                    st.rerun()
                else:
                    st.error("Missing required columns.")
        except Exception as e:
            st.error("File processing error.")

# ======================================================
# MAIN INPUT
# ======================================================
st.subheader("🔮 Step 1: Enter Current Draw")

with st.form("prediction_form"):
    manual_input = st.text_input(
        "Enter 6 Main Numbers (space separated)",
        placeholder="e.g. 1 14 23 35 40 44"
    )
    submitted = st.form_submit_button("Generate Predictions")

# ======================================================
# RESULTS
# ======================================================
if submitted and not history.empty:

    top3, gaps = run_prediction_engine(history, manual_input)

    if top3 is None:
        st.error("Insufficient data.")
    else:
        st.divider()
        st.subheader("🎯 Top 3 Bonus Predictions + Smart Triples")

        cols = st.columns(3)

        for i, (bonus_num, weight) in enumerate(top3.items()):
            with cols[i]:
                st.metric(
                    f"Rank {i+1} Bonus",
                    f"#{bonus_num}"
                )

                st.caption(
                    f"Confidence: {int(weight*100)}% | Gap: {gaps[bonus_num]}"
                )

                st.markdown("---")
                st.markdown("**Predicted Follow Triples:**")

                triples = generate_advanced_triples(history, bonus_num)

                if triples:
                    for triple in triples:
                        triple_html = "".join([
                            f"<span style='background-color:#007BFF; color:white; padding:6px 12px; border-radius:18px; margin-right:5px; font-weight:bold;'>{n}</span>"
                            for n in triple
                        ])
                        st.markdown(triple_html, unsafe_allow_html=True)
                else:
                    st.caption("Not enough historical follow-up data.")

# ======================================================
# VISUAL ANALYTICS
# ======================================================
if not history.empty:

    st.divider()
    st.subheader("📊 Bonus Overdue Pressure Map")

    bonus_series = pd.to_numeric(
        history["bonus"], errors="coerce"
    ).dropna().astype(int)

    last_seen = {i: -1 for i in range(1, MAX_NUMBER+1)}
    for idx, val in enumerate(bonus_series):
        if 1 <= val <= MAX_NUMBER:
            last_seen[val] = idx

    gaps = pd.Series(
        [len(bonus_series) - last_seen[i] for i in range(1, MAX_NUMBER+1)],
        index=range(1, MAX_NUMBER+1)
    )

    fig = px.bar(
        x=gaps.index,
        y=gaps.values,
        color=gaps.values,
        color_continuous_scale="Reds",
        title="Bonus Ball Gap Pressure"
    )

    st.plotly_chart(fig, use_container_width=True)

elif history.empty:
    st.info("Upload historical dataset to begin analysis.")
