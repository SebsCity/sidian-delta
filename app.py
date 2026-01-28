import streamlit as st
import pandas as pd
from datetime import timedelta
import calendar

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="⚽", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .pitch-card { 
        background-color: #E8F5E9; 
        border: 2px solid #2E7D32; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px;
        text-align: center;
    }
    .player-badge {
        background-color: #2E7D32;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 16px;
        display: inline-block;
        margin: 2px;
    }
    .split-arrow { font-size: 20px; color: #FF6F00; font-weight: bold; }
    .target-badge {
        background-color: #FF6F00;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ The Sidian Tactical Board")
st.markdown("System: **Physics**, **Rhythm**, **Magnetism**, and **The Invisible Ball (Splits)**.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Feed")
    uploaded_file = st.file_uploader("Upload Master Sequence (Excel/CSV)", type=['csv', 'xlsx'])
    st.divider()
    st.header("⚙️ Physics Mode")
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ ORACLE", "🧲 FIELDS", "⚽ TACTICS"
        ])

        # (Tabs 1-7 Hidden - Keep Previous Logic)
        # For brevity, I am only showing the new Tab 8 logic. 
        # Assume Tabs 1-7 are identical to Version 9.0.

        # ==================================================
        # TAB 8: THE TACTICAL BOARD (Soccer Split Logic)
        # ==================================================
        with tab8:
            st.subheader("⚽ The Tactical Board (Visualizing the Split)")
            st.markdown("Tracking the **Invisible Ball** movement from the Last Draw.")
            
            # 1. Get the "Players on the Field" (The Last Draw)
            last_draw_row = df.iloc[-1]
            last_players = [int(x) for x in last_draw_row[cols].values if x > 0]
            last_draw_name = f"{last_draw_row['Date'].strftime('%A %d %b')} {last_draw_row['Draw_Name']}"
            
            st.info(f"🏟️ **Current Formation (Last Draw):** {last_draw_name}")
            
            # Display Formation
            cols_f = st.columns(len(last_players))
            for i, p in enumerate(last_players):
                cols_f[i].markdown(f"<div class='player-badge'>#{p}</div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown("### ⚡ The Invisible Runs (Splits & Passes)")
            
            # 2. ANALYZE THE SPLITS
            # For each player, what happens next?
            
            cols_analysis = st.columns(3)
            
            # --- COLUMN 1: THE DIGIT SPLIT (Dribbling) ---
            with cols_analysis[0]:
                st.markdown("#### 🔪 The Digit Split")
                st.caption("Breaking the player into components.")
                
                for p in last_players:
                    if p > 9: # Only 2-digit numbers split
                        s_p = str(p)
                        d1 = int(s_p[0])
                        d2 = int(s_p[1])
                        
                        # Validate if these components are valid lotto numbers (always true for 1-49)
                        # Check "Possession": Do these split numbers usually follow the parent?
                        
                        # Simple Check: Does d1 or d2 hit in the next draw historically?
                        # (We can add complex logic here, but let's visualize first)
                        
                        st.markdown(f"**#{p}** <span class='split-arrow'>➞</span> <span class='target-badge'>#{d1}</span> & <span class='target-badge'>#{d2}</span>", unsafe_allow_html=True)
            
            # --- COLUMN 2: THE SUM & PRODUCT (The One-Two) ---
            with cols_analysis[1]:
                st.markdown("#### ➕ The One-Two (Sum)")
                st.caption("Passing into space (Digit Addition).")
                
                for p in last_players:
                    if p > 9:
                        s_p = str(p)
                        d1 = int(s_p[0])
                        d2 = int(s_p[1])
                        sum_val = d1 + d2
                        
                        # Check "Offside" (Is sum > 49? Not possible for max 49 (4+9=13))
                        st.markdown(f"**#{p}** <span class='split-arrow'>➞</span> <span class='target-badge'>#{sum_val}</span>", unsafe_allow_html=True)
            
            # --- COLUMN 3: THE THROUGH BALL (Partners) ---
            with cols_analysis[2]:
                st.markdown("#### 👟 The Through Ball")
                st.caption("Who runs when this player has the ball?")
                
                for p in last_players:
                    # Find historical partners
                    # (Quick scan of last 50 draws)
                    recent_history = df.tail(50)
                    partners = []
                    for idx, row in recent_history.iterrows():
                        if p in row[cols].values:
                            # Look at NEXT draw
                            if idx + 1 < len(df):
                                next_row = df.iloc[idx+1]
                                next_nums = [x for x in next_row[cols].values if x > 0]
                                partners.extend(next_nums)
                    
                    if partners:
                        from collections import Counter
                        most_common = Counter(partners).most_common(1)
                        best_target = most_common[0][0]
                        count = most_common[0][1]
                        
                        st.markdown(f"**#{p}** <span class='split-arrow'>➞</span> <span class='target-badge'>#{best_target}</span> <small>({count} passes)</small>", unsafe_allow_html=True)

            st.markdown("---")
            st.success("💡 **TIP:** Look for **Converging Runs**. If a 'Digit Split' (Col 1) and a 'Through Ball' (Col 3) point to the same number, that player is **OPEN ON GOAL**.")

    except Exception as e:
        st.error(f"Error: {e}")
