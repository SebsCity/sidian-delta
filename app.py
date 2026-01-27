import streamlit as st
import pandas as pd
from datetime import timedelta
import calendar

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
    .magnet-card {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 10px;
        border-left: 6px solid #6200EA;
        margin-bottom: 10px;
    }
    .super-magnet {
        background-color: #F3E5F5;
        border-left: 6px solid #D500F9;
        padding: 15px;
        border-radius: 10px;
    }
    .cluster-header { color: #D32F2F; font-weight: bold; font-size: 18px; }
    .clean-header { color: #00C853; font-weight: bold; font-size: 18px; }
    .why-text { font-style: italic; color: #555; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 The Sidian Precision Engine")
st.markdown("System: **Physics (Radar)**, **Rhythm (Oracle)**, and **Magnetism (Fields)**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    
    st.divider()
    st.header("⚙️ Physics Mode")
    split_mode = st.checkbox("🧩 Split Universes (Higher Accuracy)", value=True, help="Separates Lunch and Tea into two different datasets. Removes interference.")

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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ ORACLE", "🧲 MAGNETIC FIELDS"
        ])

        # (Tabs 1-5 Hidden - Keep previous logic)
        
        # ==================================================
        # TAB 1: RADAR (Simplified for length)
        # ==================================================
        with tab1:
            st.subheader("🔭 Individual Target Radar")
            if split_mode:
                session_filter = st.radio("Select Universe:", ["Lunchtime Only", "Teatime Only"], horizontal=True)
                if "Lunch" in session_filter:
                    df_active = df[df['Draw_Name'].str.contains("Lunchtime", case=False, na=False)].copy()
                else:
                    df_active = df[df['Draw_Name'].str.contains("Teatime", case=False, na=False)].copy()
            else:
                df_active = df.copy()

            candidates = []
            for num in range(1, 50):
                hits = []
                for idx, row in df_active.iterrows():
                    if num in row[cols].values: hits.append(idx)
                
                if len(hits) >= 3:
                    idx_last = hits[-1]; idx_prev = hits[-2]; idx_old = hits[-3]
                    gap_new = idx_last - idx_prev; gap_old = idx_prev - idx_old
                    if gap_old > 0:
                        ratio = gap_new / gap_old
                        pred_gap = gap_new * ratio
                        p_date, p_time = calculate_landing_date(df_active.loc[idx_last, 'Date'], df_active.loc[idx_last, 'Draw_Name'], pred_gap, split_mode)
                        draws_since = (df_active.index[-1]) - idx_last
                        remaining = pred_gap - draws_since
                        if remaining < 3.5:
                            candidates.append({"Number": num, "Ratio": round(ratio,2), "Est. Arrival": f"{p_date.strftime('%d %b')} ({p_time})", "Universe": session_filter if split_mode else "Combined"})
            if candidates: st.dataframe(pd.DataFrame(candidates), hide_index=True)

        # ==================================================
        # TAB 6: MONTHLY ORACLE (Keep Logic)
        # ==================================================
        with tab6:
            st.subheader("🗓️ The Monthly Focus Oracle")
            if st.button("🔮 Generate Focus"):
                # (Insert previous Tab 6 logic here or keep it simple for now)
                st.info("Use the code from Version 8.0 for full Oracle logic.")

        # ==================================================
        # TAB 7: MAGNETIC FIELDS (NEW!)
        # ==================================================
        with tab7:
            st.subheader("🧲 Magnetic Field Detector")
            st.markdown("Identifies numbers susceptible to **Day-of-Week** and **Day-of-Month** forces.")
            
            # 1. Date Picker
            target_date = st.date_input("Select Target Date:", value=pd.to_datetime("today"))
            target_day_name = target_date.strftime('%A') # e.g. "Tuesday"
            target_day_num = target_date.day # e.g. 27
            
            st.divider()
            
            if st.button("🧲 Scan Magnetic Fields"):
                # Add columns for analysis
                df['DayName'] = df['Date'].dt.day_name()
                df['DayNum'] = df['Date'].dt.day
                
                # --- FIELD 1: DAY NAME (e.g. Tuesday) ---
                df_day = df[df['DayName'] == target_day_name]
                day_counts = {}
                for _, row in df_day.iterrows():
                    for n in row[cols].values:
                        if n > 0: day_counts[n] = day_counts.get(n, 0) + 1
                
                # Top 10 for Day Name
                sorted_day = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                day_leaders = [x[0] for x in sorted_day]
                
                # --- FIELD 2: DAY NUMBER (e.g. 27th) ---
                df_date = df[df['DayNum'] == target_day_num]
                date_counts = {}
                for _, row in df_date.iterrows():
                    for n in row[cols].values:
                        if n > 0: date_counts[n] = date_counts.get(n, 0) + 1
                        
                # Top 10 for Date
                sorted_date = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                date_leaders = [x[0] for x in sorted_date]
                
                # --- FIELD 3: SUPER CONVERGENCE ---
                super_magnets = list(set(day_leaders).intersection(date_leaders))
                
                # DISPLAY
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.markdown(f"#### 📅 {target_day_name} Field")
                    st.caption(f"Numbers that love {target_day_name}s")
                    for n, c in sorted_day:
                        st.write(f"**#{n}** (Hits: {c})")
                        
                with c2:
                    st.markdown(f"#### 📆 The {target_day_num}th Field")
                    st.caption(f"Numbers that love the {target_day_num}th")
                    for n, c in sorted_date:
                        st.write(f"**#{n}** (Hits: {c})")
                        
                with c3:
                    st.markdown("#### 🔥 SUPER-MAGNETS")
                    st.caption("Caught in BOTH fields")
                    if super_magnets:
                        for n in super_magnets:
                            st.markdown(f"""
                            <div class="super-magnet">
                                <h3>#{n}</h3>
                                <div>Magnetism: <b>CRITICAL</b></div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No overlap detected today.")

    except Exception as e:
        st.error(f"Error: {e}")
