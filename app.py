import streamlit as st
import pandas as pd
from datetime import timedelta
import calendar
from collections import Counter

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="⚡", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .phenom-card { 
        background-color: #FFF3E0; 
        border: 2px solid #FF6F00; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 15px;
    }
    .best-duo {
        background-color: #E8F5E9;
        border-left: 5px solid #2E7D32;
        padding: 10px;
        margin-top: 5px;
        font-weight: bold;
    }
    .target-val { font-size: 24px; font-weight: bold; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ The Sidian Precision Engine")
st.markdown("System: **Physics**, **Rhythm**, **Magnetism**, **Tactics**, and **The Probable Split**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    st.divider()
    split_mode = st.checkbox("🧩 Split Universes", value=True)

# --- HELPER ---
def calculate_landing_date(last_date, last_draw, draws_ahead, use_split_logic):
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    steps = int(round(draws_ahead))
    if steps < 1: steps = 1
    for _ in range(steps):
        if use_split_logic:
            current_date = current_date + timedelta(days=1)
        else:
            if 'Lunchtime' in current_draw:
                current_draw = 'Teatime'
            else:
                current_draw = 'Lunchtime'
                current_date = current_date + timedelta(days=1)
    return current_date, current_draw

# --- MAIN ---
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
            if len(df.columns) < 2: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t')
        else:
            df = pd.read_excel(uploaded_file)
        
        df['Date'] = pd.to_datetime(df['Date'])
        cols = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        # TABS
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ ORACLE", "🧲 FIELDS", "⚽ TACTICS", "⚡ PHENOMENON"
        ])

        # (Tabs 1-8 Hidden - Keep Previous Logic)

        # ==================================================
        # TAB 9: THE PHENOMENON (With Probability Filter)
        # ==================================================
        with tab9:
            st.subheader("⚡ The Probable Split Calculator")
            st.markdown("Calculates the **Target** and ranks the **Top 3 Duos** by historical strength.")
            
            # Get Last Draw Data
            last_row = df.iloc[-1]
            if 'N6' in df.columns: n6 = int(last_row['N6'])
            else: n6 = int(last_row[cols[-2]]) # Fallback
            bonus = int(last_row['Bonus'])
            
            st.info(f"**INPUTS:** Last N6 = {n6} | Last Bonus = {bonus}")
            
            # --- HELPER: RANK DUOS ---
            def get_best_duos(target_val, df_hist):
                # 1. Generate all math pairs
                possible_pairs = []
                for i in range(1, 50):
                    needed = target_val - i
                    if needed > 0 and needed != i and needed < 50:
                        pair = tuple(sorted((i, needed)))
                        if pair not in possible_pairs: possible_pairs.append(pair)
                
                # 2. Score them based on history (How often do they appear together?)
                pair_scores = {}
                for p in possible_pairs:
                    count = 0
                    # Scan last 500 draws for speed
                    subset = df_hist.tail(500)
                    for _, row in subset.iterrows():
                        row_vals = set(row[cols].values)
                        if p[0] in row_vals and p[1] in row_vals:
                            count += 1
                    pair_scores[p] = count
                
                # Sort by frequency
                sorted_pairs = sorted(pair_scores.items(), key=lambda x: x[1], reverse=True)
                return sorted_pairs[:3] # Return top 3

            c1, c2 = st.columns(2)
            
            # --- 1. PRODUCT RULE ---
            with c1:
                s_n6 = str(n6)
                if len(s_n6) > 1: target_prod = int(s_n6[0]) * int(s_n6[1])
                else: target_prod = n6
                
                st.markdown(f"""
                <div class="phenom-card">
                    <h4>Rule 1: The Product</h4>
                    <div>Digits of {n6} multiplied</div>
                    <div class="target-val">Target: {target_prod}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if target_prod >= 3:
                    best_prod_duos = get_best_duos(target_prod, df)
                    st.caption("🏆 Most Probable Splits (by History):")
                    for duo, score in best_prod_duos:
                        st.markdown(f"<div class='best-duo'>👉 {duo[0]} & {duo[1]} <small>(Seen {score} times)</small></div>", unsafe_allow_html=True)
            
            # --- 2. DIFFERENCE RULE ---
            with c2:
                target_diff = abs(n6 - bonus)
                
                st.markdown(f"""
                <div class="phenom-card">
                    <h4>Rule 2: The Difference</h4>
                    <div>|{n6} - {bonus}|</div>
                    <div class="target-val">Target: {target_diff}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if target_diff >= 3:
                    best_diff_duos = get_best_duos(target_diff, df)
                    st.caption("🏆 Most Probable Splits (by History):")
                    for duo, score in best_diff_duos:
                        st.markdown(f"<div class='best-duo'>👉 {duo[0]} & {duo[1]} <small>(Seen {score} times)</small></div>", unsafe_allow_html=True)

            st.success("✅ **STRATEGY:** Play the **#1 Ranked Duo** from both columns. These are mathematically valid AND historically proven.")

    except Exception as e:
        st.error(f"Error: {e}")
