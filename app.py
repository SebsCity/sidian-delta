import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from itertools import combinations

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="🎯", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .oracle-card { 
        background-color: #f9f9f9; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 6px solid #2962FF; 
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .cluster-header { color: #D32F2F; font-weight: bold; font-size: 18px; }
    .skip-header { color: #2962FF; font-weight: bold; font-size: 18px; }
    .why-text { font-style: italic; color: #555; margin-top: 5px; }
    .note-text { font-size: 14px; color: #777; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("System: **Radar**, **Lab**, **Squads**, **Partners**, and **The Monthly Focus Oracle**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])

# --- HELPER ---
def calculate_landing_date(last_date, last_draw, draws_ahead):
    current_date = pd.to_datetime(last_date)
    current_draw = str(last_draw).strip()
    steps = int(round(draws_ahead))
    if steps < 1: steps = 1
    for _ in range(steps):
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ MONTHLY FOCUS"])

        # (Existing Logic for Tabs 1-5 Hidden for brevity - assume Standard Sidian Logic)
        # ==================================================
        # TAB 6: MONTHLY FOCUS ORACLE (The Assistant Update)
        # ==================================================
        with tab6:
            st.subheader("🗓️ The Monthly Focus Oracle")
            st.markdown("Generates detailed **Cluster** and **Skip-Beat** narratives for the entire month.")
            
            if st.button("🔮 Generate Monthly Focus"):
                schedule = {}
                
                # 1. RUN PHYSICS ON ALL NUMBERS
                for num in range(1, 50):
                    hits = []
                    for idx, row in df.iterrows():
                        if num in row[cols].values: hits.append(idx)
                    
                    if len(hits) >= 3:
                        idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                        gap_new = idx_last - idx_prev; gap_old = idx_prev - idx_old
                        
                        if gap_old > 0:
                            ratio = gap_new / gap_old
                            pred_gap = gap_new * ratio
                            p_date, p_time = calculate_landing_date(df.iloc[idx_last]['Date'], df.iloc[idx_last]['Draw_Name'], pred_gap)
                            
                            # LOGIC: DETECT PATTERN
                            last_draw_name = df.iloc[idx_last]['Draw_Name']
                            is_skip = False
                            
                            # Skip-Beat Logic (Tea->Tea OR Lunch->Lunch)
                            if ("Teatime" in str(last_draw_name) and "Teatime" in p_time) or \
                               ("Lunchtime" in str(last_draw_name) and "Lunchtime" in p_time):
                                is_skip = True
                            
                            # Store Data
                            key = f"{p_date.strftime('%Y-%m-%d')} | {p_time}"
                            if key not in schedule: schedule[key] = []
                            schedule[key].append({
                                "Num": num, 
                                "Skip": is_skip, 
                                "Frequency": f"{last_draw_name}-to-{p_time}"
                            })

                # 2. GENERATE NARRATIVE OUTPUT
                sorted_keys = sorted(schedule.keys())
                today_str = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
                
                # Filter for Next 30 Days
                count_days = 0
                
                for key in sorted_keys:
                    date_part, time_part = key.split(" | ")
                    
                    if date_part >= today_str:
                        items = schedule[key]
                        
                        # Extract Lists
                        all_nums = sorted([x['Num'] for x in items])
                        skip_nums = sorted([x['Num'] for x in items if x['Skip']])
                        freq_type = items[0]['Frequency'] if items else "Unknown"
                        
                        # Only show relevant days (High Activity)
                        if len(all_nums) > 0:
                            pretty_date = pd.to_datetime(date_part).strftime('%A %d %b')
                            
                            # Dynamic "Why" Generator
                            why_msg = ""
                            if skip_nums:
                                why_msg = f"The physics engine sees that **{skip_nums}** are vibrating on a \"{freq_type}\" frequency. They are ignoring the noise of the in-between draw to hit this specific target."
                            else:
                                why_msg = f"Standard convergence detected. These numbers are resolving their individual gap ratios simultaneously."
                                
                            # Note Generator
                            note_msg = ""
                            if len(all_nums) >= 5:
                                note_msg = "⚠️ **CRITICAL:** This is a High-Density Cluster. Expect a potential Jackpot Line."
                            elif len(skip_nums) == len(all_nums):
                                note_msg = "🌊 **PURE RHYTHM:** Every number here is a Skip-Beat. This is a highly stable lock."

                            # HTML RENDER
                            st.markdown(f"""
                            <div class="oracle-card">
                                <h3>{pretty_date} ({time_part})</h3>
                                <div class="cluster-header">⚠️ The Cluster: {all_nums}</div>
                                <div class="skip-header">🌊 The Skip-Beat: {skip_nums if skip_nums else "None"}</div>
                                <div class="why-text"><b>Why?</b> {why_msg}</div>
                                <div class="note-text">{note_msg}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            count_days += 1
                            if count_days > 30: break # Cap at 30 entries

    except Exception as e:
        st.error(f"Error: {e}")
