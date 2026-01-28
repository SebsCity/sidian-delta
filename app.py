import streamlit as st
import pandas as pd
from datetime import timedelta
import calendar

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sidian Precision Engine", page_icon="🧮", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .algebra-card { 
        background-color: #F3E5F5; 
        border: 2px solid #8E24AA; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px;
    }
    .formula-text { font-family: monospace; font-size: 16px; color: #4A148C; }
    .result-badge {
        background-color: #8E24AA;
        color: white;
        padding: 5px 15px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 18px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧮 The Sidian Algebraic Processor")
st.markdown("System: **Physics**, **Rhythm**, **Magnetism**, **Tactics**, and **Positional Algebra**.")

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
            "🔭 Radar", "🔬 Lab", "⛓️ Squads", "🤝 Partners", "🧩 Groups", "🗓️ ORACLE", "🧲 FIELDS", "⚽ TACTICS", "🧮 ALGEBRA"
        ])

        # (Tabs 1-8 Hidden - Keep Previous Logic)

        # ==================================================
        # TAB 9: POSITIONAL ALGEBRA (The New Code Breaker)
        # ==================================================
        with tab9:
            st.subheader("🧮 Positional Algebra Processor")
            st.markdown("Solving the equation: **First**, **Last**, and **Bonus**.")
            
            # Need Last 2 Draws
            if len(df) >= 2:
                # CURRENT DRAW (Last row)
                curr_row = df.iloc[-1]
                curr_nums = [int(x) for x in curr_row[cols].values if x > 0]
                curr_n1 = curr_nums[0]
                curr_n2 = curr_nums[1]
                curr_n6 = curr_nums[-1]
                curr_bonus = int(curr_row['Bonus'])
                
                # PREVIOUS DRAW (2nd to last row)
                prev_row = df.iloc[-2]
                prev_nums = [int(x) for x in prev_row[cols].values if x > 0]
                prev_n1 = prev_nums[0]
                prev_n6 = prev_nums[-1]
                
                st.info(f"**Analyzing Sequence:** {prev_row['Draw_Name']} ➡️ {curr_row['Draw_Name']}")

                # --- EQUATION 1: THE BRACKET (Prev N6 - Prev N1) ---
                eq1_res = abs(prev_n6 - prev_n1)
                st.markdown(f"""
                <div class="algebra-card">
                    <h4>1. The Bracket (Hold)</h4>
                    <div class="formula-text">Equation: Prev N6 ({prev_n6}) - Prev N1 ({prev_n1})</div>
                    <br>
                    <div class="result-badge">Target: {eq1_res}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- EQUATION 2: THE INTERNAL PRODUCT (Prev N6 Digits) ---
                p_s = str(prev_n6)
                if len(p_s) > 1:
                    eq2_res = int(p_s[0]) * int(p_s[1])
                else:
                    eq2_res = prev_n6 # Single digit fallback
                
                st.markdown(f"""
                <div class="algebra-card">
                    <h4>2. The Internal Product (Split Check)</h4>
                    <div class="formula-text">Equation: Digits of Prev N6 ({prev_n6}) multiplied</div>
                    <br>
                    <div class="result-badge">Target: {eq2_res}</div>
                    <small>If {eq2_res} misses, look for its Split (e.g. 28 -> 6 & 22)</small>
                </div>
                """, unsafe_allow_html=True)

                # --- EQUATION 3: THE POWERBALL SOLVE (Bonus - Curr N6 Product) ---
                c_s = str(curr_n6)
                if len(c_s) > 1:
                    curr_n6_prod = int(c_s[0]) * int(c_s[1])
                else:
                    curr_n6_prod = curr_n6
                
                eq3_res = abs(curr_bonus - curr_n6_prod)
                
                st.markdown(f"""
                <div class="algebra-card">
                    <h4>3. The Powerball Solve</h4>
                    <div class="formula-text">Equation: Curr Bonus ({curr_bonus}) - (Digits of Curr N6 ({curr_n6}))</div>
                    <div class="formula-text">Calculation: {curr_bonus} - {curr_n6_prod}</div>
                    <br>
                    <div class="result-badge">Target: {eq3_res}</div>
                </div>
                """, unsafe_allow_html=True)

                # --- EQUATION 4: THE ANCHOR (Curr N6 + Curr N2) ---
                eq4_res = curr_n6 + curr_n2
                # Check for > 49 wrapping (though user didn't specify wrapping, usually Lotto implies subtraction if > 49 or just raw sum)
                # User example: 41 + 6 = 47. 
                
                st.markdown(f"""
                <div class="algebra-card">
                    <h4>4. The Anchor Add</h4>
                    <div class="formula-text">Equation: Curr N6 ({curr_n6}) + Curr N2 ({curr_n2})</div>
                    <br>
                    <div class="result-badge">Target: {eq4_res}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # SUMMARY
                st.divider()
                st.success(f"**🧮 ALGEBRAIC PREDICTION:** {eq1_res}, {eq2_res}, {eq3_res}, {eq4_res}")
                
            else:
                st.warning("Need at least 2 draws of history to run Algebra.")

    except Exception as e:
        st.error(f"Error: {e}")
