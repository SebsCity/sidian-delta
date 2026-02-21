import streamlit as st
import pandas as pd
import numpy as np
import itertools

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Sidian 2–3 Hunter", layout="wide", page_icon="🎯")
MAX_NUMBER = 49
ANALYSIS_WINDOW = 250  # Cloud-safe limit

st.title("🎯 Sidian 2–3 Hunter Engine")
st.caption("Cloud Optimized | Android Stable | Short-Term Structural Bias")

# ==========================================
# DATA LOAD (CACHED)
# ==========================================
@st.cache_data
def load_file(uploaded):
    if uploaded.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    df = df.dropna(how="all").reset_index(drop=True)

    # Auto-detect numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 6:
        st.error("File must contain at least 6 numeric columns.")
        st.stop()

    return df, numeric_cols

# ==========================================
# ANALYTICS ENGINE (LIGHTWEIGHT)
# ==========================================
@st.cache_data
def analyze(df, numeric_cols):

    df = df.tail(ANALYSIS_WINDOW).iloc[::-1]  # Newest first

    main_cols = numeric_cols[:6]
    bonus_col = numeric_cols[6] if len(numeric_cols) > 6 else None

    # --- Last 3 Draws → 21 Pool ---
    last3 = df.head(3)

    pool = []
    for _, row in last3.iterrows():
        mains = [int(row[c]) for c in main_cols]
        pool.extend(mains)
        if bonus_col:
            pool.append(int(row[bonus_col]))

    unique_21 = sorted(list(set(pool)))

    # --- Stickiness ---
    sticky_scores = {n: 0 for n in unique_21}

    for i in range(len(df)-1):
        curr = set(df.iloc[i][main_cols].astype(int))
        prev = set(df.iloc[i+1][main_cols].astype(int))
        repeats = curr.intersection(prev)

        for n in repeats:
            if n in sticky_scores:
                sticky_scores[n] += 1

    top_sticky = pd.Series(sticky_scores).nlargest(5)

    # --- AI Weighted Scoring ---
    scores = {}

    for n in unique_21:
        freq = pool.count(n)
        scores[n] = freq * 3

        # recency bonus
        if n in last3.iloc[0][main_cols].values:
            scores[n] += 2

        # mild cooling penalty
        if freq >= 3:
            scores[n] -= 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # --- Build 3-number Hunter Sets ---
    top7 = [n for n, s in ranked[:7]]
    combos = list(itertools.combinations(top7, 3))

    combo_scores = []
    for c in combos:
        combo_scores.append((c, sum(scores[n] for n in c)))

    combo_scores = sorted(combo_scores, key=lambda x: x[1], reverse=True)

    return unique_21, top_sticky, ranked, combo_scores[:5]

# ==========================================
# UI
# ==========================================
uploaded = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

if uploaded:

    df, numeric_cols = load_file(uploaded)
    u21, sticky, ranked, top_combos = analyze(df, numeric_cols)

    st.subheader("📍 The 21 Exclusion Pool")
    st.write(u21)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔄 Sticky Leaders")
        for num, score in sticky.items():
            st.write(f"#{num} — Repeat Score: {score}")

    with col2:
        st.subheader("🧠 AI Ranked Core")
        for num, score in ranked[:7]:
            st.write(f"#{num} — AI Score: {score}")

    st.divider()

    st.subheader("🔥 Top 3-Number Hunter Sets")

    for combo, score in top_combos:
        st.write(f"{combo} — Priority Score: {score}")

else:
    st.info("Upload your historical sheet to begin.")
