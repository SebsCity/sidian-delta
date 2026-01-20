import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Sidian Master System", page_icon="🎱", layout="wide")

st.title("🎱 The Sidian Master System")

# --- FILE UPLOADER (Global for all tabs) ---
st.sidebar.header("📂 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Master Sequence (CSV/Excel)", type=['csv', 'xlsx'])

df = None
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, sep='\t' if 'tsv' in uploaded_file.name else ',')
        # Check if it was tab separated but read wrong
        if len(df.columns) < 2: 
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep='\t')
    else:
        df = pd.read_excel(uploaded_file)
    
    # Ensure Date is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    st.sidebar.success(f"Loaded {len(df)} draws.")

# --- HELPER FUNCTIONS ---
def get_future_draw(start_date, start_draw_name, draws_to_add):
    current_date = pd.to_datetime(start_date)
    current_draw = str(start_draw_name).strip()
    steps = int(round(draws_to_add))
    if steps < 1: steps = 1
    
    for _ in range(steps):
        if 'Lunchtime' in current_draw:
            current_draw = 'Teatime'
        else:
            current_draw = 'Lunchtime'
            current_date = current_date + timedelta(days=1)
    return current_date.strftime('%A %d %b'), current_draw

# --- TABS CONFIGURATION (FIXED) ---
# This is where the error was. We now define 3 tabs.
tab1, tab2, tab3 = st.tabs(["🧮 Daily Calculator", "📉 Gravity Lab (Physics)", "🔊 Resonance Chamber"])

# ==========================================
# TAB 1: THE SIDIAN TRIAD (The Daily Math)
# ==========================================
with tab1:
    st.header("The Sidian Triad Auditor")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        play_date = st.number_input("📅 Date of Draw (D)", min_value=1, max_value=31, value=18)
    with col2:
        bonus_ball = st.number_input("🔵 Last Bonus Ball (B)", min_value=1, max_value=49, value=25)
    with col3:
        lowest_main = st.number_input("📉 Lowest Main (M)", min_value=1, max_value=49, value=5)

    st.divider()

    # Calculations
    target_1_sum = bonus_ball + play_date
    target_1_diff = abs(bonus_ball - play_date)
    
    diff_b_d = abs(bonus_ball - play_date)
    sum_b_d = bonus_ball + play_date
    target_2_inv_diff = 49 - diff_b_d
    target_2_inv_sum = 49 - sum_b_d
    
    target_3_gap = abs(bonus_ball - lowest_main)

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**Date Drivers (Flow)**\n# {target_1_sum if target_1_sum <= 49 else target_1_sum-49} | {target_1_diff}")
    with c2:
        st.warning(f"**The Traps (Inverse)**\n# {target_2_inv_diff} | {target_2_inv_sum if target_2_inv_sum > 0 else 'N/A'}")
        
    st.success(f"**The Feeder (Gap)**: # {target_3_gap}")

# ==========================================
# TAB 2: THE GRAVITY LAB (Bouncing Ball)
# ==========================================
with tab2:
    st.header("📉 Bouncing Ball Physics")
    
    if df is not None:
        target_num = st.number_input("Enter a Number to Audit (e.g. 16)", min_value=1, max_value=49, value=16)
        
        # Find hits
        hits = []
        cols_to_check = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
        
        for idx, row in df.iterrows():
            if target_num in row[cols_to_check].values:
                hits.append(idx)
                
        if len(hits) >= 3:
            idx_last = hits[-1]
            idx_prev = hits[-2]
            idx_old = hits[-3]
            
            gap_new = idx_last - idx_prev
            gap_old = idx_prev - idx_old
            
            last_date = df.iloc[idx_last]['Date']
            last_draw_name = df.iloc[idx_last]['Draw_Name']
            
            if gap_old > 0:
                ratio = gap_new / gap_old
                st.write(f"**Sequence:** Gap {gap_old} ➔ Gap {gap_new}")
                st.metric("Physics Ratio", f"{ratio:.2f}")
                
                next_gap_float = gap_new * ratio
                
                # Logic: Standard or Sleeper
                if ratio <= 1.1:
                    pred_date, pred_time = get_future_draw(last_date, last_draw_name, next_gap_float)
                    if ratio < 0.8:
                        st.error(f"🚀 ACCELERATING (Hot)")
                    else:
                        st.warning(f"⚠️ STABLE")
                    st.success(f"**Target:** {pred_date} ({pred_time})")
                    
                elif ratio > 4.0:
                    st.info(f"💤 SLEEPER WAKE-UP! Expect a 'Double Tap' (Repeat) in 1-3 draws.")
                else:
                    st.write("🔵 Decelerating (Going Cold).")
        else:
            st.warning("Not enough history for this number (Need 3 hits).")
    else:
        st.warning("Please upload your Master File in the sidebar.")

# ==========================================
# TAB 3: THE RESONANCE CHAMBER (Harmonic Pairs)
# ==========================================
with tab3:
    st.header("🔊 The Resonance Chamber")
    st.caption("Predict which pair lands next based on the last pair.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        trigger_1 = st.number_input("Trigger Number A", min_value=1, max_value=49, value=5)
    with col_r2:
        trigger_2 = st.number_input("Trigger Number B", min_value=1, max_value=49, value=17)

    st.divider()

    if st.button("🔉 Pulse the Speaker"):
        if df is not None:
            matches = []
            cols_check = [c for c in df.columns if c.startswith('N') or c == 'Bonus']
            
            for i in range(len(df) - 1):
                row = df.iloc[i]
                vals = row[cols_check].values
                
                if trigger_1 in vals and trigger_2 in vals:
                    # Found Trigger
                    found_next = False
                    for j in range(i + 1, len(df)):
                        next_row = df.iloc[j]
                        next_vals = next_row[cols_check].values
                        
                        if trigger_1 in next_vals:
                            height = j - i
                            partners = [x for x in next_vals if x != trigger_1 and x > 0]
                            matches.append({
                                "Date": row['Date'].strftime('%Y-%m-%d'),
                                "Height": height,
                                "Next_Partners": str(partners)
                            })
                            found_next = True
                            break
            
            if len(matches) > 0:
                st.write(f"Found {len(matches)} resonances.")
                res_df = pd.DataFrame(matches)
                st.dataframe(res_df)
                
                avg_height = res_df['Height'].mean()
                st.metric("Average Bounce Height", f"{avg_height:.1f} Draws")
                st.info(f"Prediction: Watch for {trigger_1} in approx {round(avg_height)} draws.")
            else:
                st.error("This pair has never appeared together in history.")
        else:
            st.warning("Please upload your Master File in the sidebar.")
