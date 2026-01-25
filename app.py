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
    .day-card { border-radius: 10px; padding: 15px; margin: 10px 0; border: 1px solid #ddd; transition: transform 0.2s; }
    .day-card:hover { transform: scale(1.02); }
    .heat-low { background-color: #E8F5E9; border-left: 5px solid #43A047; }
    .heat-med { background-color: #FFFDE7; border-left: 5px solid #FDD835; }
    .heat-high { background-color: #FFEBEE; border-left: 5px solid #D32F2F; }
    .date-header { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
    .draw-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; margin-left: 10px; }
    .lunch-badge { background-color: #FF9800; }
    .tea-badge { background-color: #3F51B5; }
    .skip-beat { color: #2962FF; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("System: **Radar**, **Lab**, **Squads**, **Partners**, **Groups**, and **The Rhythm Heatmap**.")

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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ RHYTHM HEATMAP"])

        # (Tabs 1-5 Hidden for brevity - assume same logic as v6.0)
        # ... [Insert previous Tabs 1-5 logic here if rewriting full file] ...
        # For simplicity in this prompt, I will focus on the updated Tab 6 logic.
        # You should keep Tabs 1-5 from the previous code block.

        # ==================================================
        # TAB 6: RHYTHM HEATMAP (Skip-Beat Update)
        # ==================================================
        with tab6:
            st.subheader("🗓️ The Universal Rhythm Heatmap")
            st.markdown("Visualizing **Convergence** and **Skip-Beat Patterns**.")
            
            if st.button("🔄 Generate Rhythm Schedule"):
                schedule = {}
                
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
                            
                            # SKIP-BEAT DETECTION
                            last_draw_name = df.iloc[idx_last]['Draw_Name']
                            is_skip = False
                            if "Teatime" in str(last_draw_name) and "Teatime" in p_time: is_skip = True
                            if "Lunchtime" in str(last_draw_name) and "Lunchtime" in p_time: is_skip = True
                            
                            key = f"{p_date.strftime('%Y-%m-%d')} | {p_time}"
                            if key not in schedule: schedule[key] = []
                            schedule[key].append({"Num": num, "Skip": is_skip})

                # RENDER
                sorted_keys = sorted(schedule.keys())
                today_str = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
                
                for key in sorted_keys:
                    date_part, time_part = key.split(" | ")
                    if date_part >= today_str:
                        items = schedule[key]
                        nums_display = []
                        for item in items:
                            if item['Skip']:
                                nums_display.append(f"{item['Num']} (🌊)")
                            else:
                                nums_display.append(str(item['Num']))
                        
                        count = len(items)
                        if count >= 5: css = "heat-high"; icon = "🔥 SUPER DRAW"
                        elif count >= 3: css = "heat-med"; icon = "⚠️ High Pressure"
                        else: css = "heat-low"; icon = "🌱 Stable"
                        
                        badge = "lunch-badge" if "Lunch" in time_part else "tea-badge"
                        pretty_date = pd.to_datetime(date_part).strftime('%A, %d %b')
                        
                        st.markdown(f"""
                        <div class="day-card {css}">
                            <div class="date-header">{pretty_date} <span class="draw-badge {badge}">{time_part}</span></div>
                            <div><strong>{icon}</strong> ({count} Due)</div>
                            <div class="num-list">{', '.join(nums_display)}</div>
                            <div style="font-size:12px; color:gray; margin-top:5px;">🌊 = Skip-Beat Rhythm Detected</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
    except Exception as e:
        st.error(f"Error: {e}")
