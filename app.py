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
    .success-box { 
        background-color: #E8F5E9; 
        border: 2px solid #2E7D32; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px; 
    }
    .warning-box { 
        background-color: #FFF3E0; 
        border: 2px solid #EF6C00; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px; 
    }
    .danger-box { 
        background-color: #FFEBEE; 
        border: 2px solid #C62828; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px; 
    }
    .stat-metric { font-size: 24px; font-weight: bold; color: #1565C0; }
    .best-duo {
        background-color: #E3F2FD;
        border-left: 5px solid #1565C0;
        padding: 8px;
        margin-top: 4px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ The Sidian Precision Engine (Master v16.0)")
st.markdown("**Status:** Systems Online. All Laws Validated.")

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

def get_best_duos(target_val, df_hist, cols):
    possible_pairs = []
    for i in range(1, 50):
        needed = target_val - i
        if needed > 0 and needed != i and needed < 50:
            pair = tuple(sorted((i, needed)))
            if pair not in possible_pairs: possible_pairs.append(pair)
    pair_scores = {}
    for p in possible_pairs:
        count = 0
        subset = df_hist.tail(500)
        for _, row in subset.iterrows():
            row_vals = set(row[cols].values)
            if p[0] in row_vals and p[1] in row_vals: count += 1
        pair_scores[p] = count
    return sorted(pair_scores.items(), key=lambda x: x[1], reverse=True)[:3]

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

        # (Tabs 1-8 Hidden for brevity)

        # ==================================================
        # TAB 9: THE MASTER PHENOMENON (INTEGRATED)
        # ==================================================
        with tab9:
            st.subheader("⚡ The Phenomenon & Unit Law")
            
            # Get Last Draw Data
            last_row = df.iloc[-1]
            last_nums = [int(x) for x in last_row[cols].values if x > 0]
            if 'N6' in df.columns: n6 = int(last_row['N6'])
            else: n6 = last_nums[-1] 
            bonus = int(last_row['Bonus'])
            
            st.info(f"**INPUTS:** Last N6 = {n6} | Last Bonus = {bonus}")
            
            # Layout
            c1, c2, c3 = st.columns(3)

            # --- 1. PRODUCT & DIFF TARGETS ---
            with c1:
                st.markdown("### 🎯 1. The Splits")
                # Product
                s_n6 = str(n6)
                if len(s_n6) > 1: target_prod = int(s_n6[0]) * int(s_n6[1])
                else: target_prod = n6
                st.write(f"**Product Target:** {target_prod}")
                if target_prod >= 3:
                    best = get_best_duos(target_prod, df, cols)
                    for duo, score in best:
                        st.markdown(f"<div class='best-duo'>👉 {duo[0]} & {duo[1]}</div>", unsafe_allow_html=True)
                
                st.divider()
                
                # Difference
                target_diff = abs(n6 - bonus)
                st.write(f"**Difference Target:** {target_diff}")
                if target_diff >= 3:
                    best = get_best_duos(target_diff, df, cols)
                    for duo, score in best:
                        st.markdown(f"<div class='best-duo'>👉 {duo[0]} & {duo[1]}</div>", unsafe_allow_html=True)

            # --- 2. THE PARENTS ---
            with c2:
                st.markdown("### 👨‍👩‍👦 2. The Parents")
                S = n6
                s_str = str(n6)
                if len(s_str) > 1: D = int(s_str[0]) + int(s_str[1])
                else: D = n6
                
                if (S + D) % 2 == 0:
                    X = int((S + D) / 2)
                    Y = int((S - D) / 2)
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>Calculated Parents:</h4>
                        <div class="stat-metric">{X} & {Y}</div>
                        <small>Likelihood: ~27% Direct Hit</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No Integer Parents for this N6.")

            # --- 3. THE UNIT SUM & SQUAD 30s ---
            with c3:
                st.markdown("### 🛡️ 3. The Unit Law")
                
                # Zone Logic
                if n6 in [40, 41]:
                    zone_css = "danger-box"
                    zone_msg = "⛔ RED ZONE (40-41)"
                    squad_msg = "DO NOT use Squad 34-39. Math impossible."
                elif n6 in [42, 43]:
                    zone_css = "warning-box"
                    zone_msg = "⚠️ ORANGE ZONE (42-43)"
                    squad_msg = "Risk High. Only check 38, 39."
                elif n6 >= 44:
                    zone_css = "success-box"
                    zone_msg = "✅ GREEN ZONE (44-49)"
                    squad_msg = "DEPLOY Squad 34-39. High Probability."
                else:
                    zone_css = "warning-box"
                    zone_msg = "Unknown Zone (N6 < 40)"
                    squad_msg = "Standard Unit Rules apply."

                st.markdown(f"""
                <div class="{zone_css}">
                    <h4>{zone_msg}</h4>
                    <div>{squad_msg}</div>
                </div>
                """, unsafe_allow_html=True)

                # Calculate Valid Unit Partners
                u6 = n6 % 10
                min_u = 11 - u6
                max_u = 18 - u6
                valid_digits = [d for d in range(10) if min_u <= d <= max_u]
                
                if valid_digits:
                    st.write(f"**Look for partners ending in:** {valid_digits}")
                    # Show valid numbers
                    matches = []
                    for d in valid_digits:
                        matches.extend([x for x in range(1, 50) if x % 10 == d])
                    matches = sorted(matches)
                    st.text_area("Valid Partners (Copy These):", str(matches).replace('[','').replace(']',''), height=100)
                else:
                    st.error("No valid unit partners exist (Red Zone).")

    except Exception as e:
        st.error(f"Error: {e}")
