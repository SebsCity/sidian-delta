import streamlit as st
import pandas as pd
import itertools

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Lottery Dyno Test Protocol", layout="wide", page_icon="🏎️")

st.title("🏎️ The Dyno Test Protocol")
st.markdown("""
**System Status:** Ready for Testing  
**Objective:** Stress-test lottery numbers before betting.  
**Protocol:** 1. **Split Check:** Are the components (e.g., 3+4=7) exhausted?  
2. **Neighbor Check:** Is the lane blocked by adjacent numbers?  
3. **Gap Validation:** Is the number mathematically active in the current draw?
""")

# --- SIDEBAR ---
st.sidebar.header("🔧 Garage Settings")
uploaded_file = st.sidebar.file_uploader("Upload Draw History (CSV/Excel)", type=["csv", "xlsx"])

# --- LOGIC FUNCTIONS ---

def get_last_draws(df, n=2):
    """Returns the numbers from the last n draws as a flat list."""
    recent_draws = df.tail(n)
    numbers = []
    for _, row in recent_draws.iterrows():
        nums = [row[c] for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Bonus']]
        numbers.extend(nums)
    return numbers, df.iloc[-1]

def check_split_health(target, recent_numbers):
    """
    Step 1: Check if components (a+b=target) were just drawn.
    If components are HOT, the number might be 'exhausted' (Red Light).
    If components are COLD, the machine is forced to play the number (Green Light).
    """
    splits = []
    # Find all pairs that sum to target
    for i in range(1, target // 2 + 1):
        j = target - i
        if j != i and j <= 49:
            splits.append((i, j))
            
    # Check if these components appear in recent history
    used_splits = []
    for a, b in splits:
        if a in recent_numbers and b in recent_numbers:
            used_splits.append(f"{a}+{b}")
    
    if len(used_splits) > 0:
        return False, f"CRITICAL: Components used ({', '.join(used_splits)})"
    return True, "PASSED: Components are fresh."

def check_neighbor_traffic(target, recent_numbers):
    """
    Step 2: Check if neighbors (Target-1, Target+1) are crowding the lane.
    """
    neighbors = [target - 1, target + 1]
    clashes = [n for n in neighbors if n in recent_numbers]
    
    if len(clashes) > 0:
        return False, f"WARNING: Lane blocked by {clashes}"
    return True, "PASSED: Lane is clear."

def check_gap_validation(target, last_row):
    """
    Step 3: Check if the number exists as a mathematical gap in the LATEST draw.
    """
    current_nums = sorted([int(last_row[c]) for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']])
    bonus = int(last_row['Bonus'])
    
    gaps_found = []
    
    # Internal Gaps (N2-N1, etc.)
    for i in range(len(current_nums) - 1):
        diff = current_nums[i+1] - current_nums[i]
        if diff == target:
            gaps_found.append(f"Gap {current_nums[i+1]}-{current_nums[i]}")
            
    # Bonus Gap (N6 - Bonus or Bonus - N1 etc - usually N6-Bonus is strongest)
    if abs(current_nums[-1] - bonus) == target:
         gaps_found.append(f"Gap N6({current_nums[-1]})-Bonus({bonus})")
         
    if len(gaps_found) > 0:
        return True, f"PASSED: Active Gap ({', '.join(gaps_found)})"
    return False, "FAIL: No mathematical foundation in current draw."

# --- MAIN APP ---

if uploaded_file is not None:
    # Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Clean Data
        cols_needed = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Bonus']
        if not all(col in df.columns for col in cols_needed):
            st.error(f"Data missing columns. Need: {cols_needed}")
        else:
            # Prepare Data
            recent_pool, last_draw_row = get_last_draws(df, n=2)
            last_draw_nums = [last_draw_row[c] for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']]
            st.info(f"Loaded Last Draw: {last_draw_nums} + Bonus {last_draw_row['Bonus']}")

            # --- TAB INTERFACE ---
            tab1, tab2 = st.tabs(["🧪 Manual Dyno Test", "🤖 Auto-Scan Protocol"])

            with tab1:
                st.subheader("Test a Specific Number")
                user_num = st.number_input("Enter Number to Test (1-49)", min_value=1, max_value=49, value=7)
                
                if st.button("Run Dyno Test"):
                    col1, col2, col3 = st.columns(3)
                    
                    # 1. Split Check
                    s_pass, s_msg = check_split_health(user_num, recent_pool)
                    with col1:
                        st.markdown("### 1. Split Check")
                        if s_pass:
                            st.success(s_msg)
                        else:
                            st.error(s_msg)
                            
                    # 2. Neighbor Check
                    n_pass, n_msg = check_neighbor_traffic(user_num, recent_pool)
                    with col2:
                        st.markdown("### 2. Neighbor Check")
                        if n_pass:
                            st.success(n_msg)
                        else:
                            st.warning(n_msg)
                            
                    # 3. Gap Check
                    g_pass, g_msg = check_gap_validation(user_num, last_draw_row)
                    with col3:
                        st.markdown("### 3. Gap Validation")
                        if g_pass:
                            st.success(g_msg)
                        else:
                            st.error(g_msg)
                    
                    # Final Verdict
                    st.markdown("---")
                    score = sum([s_pass, n_pass, g_pass])
                    if score == 3:
                        st.balloons()
                        st.success(f"✅ **RACE READY:** Number {user_num} passed all checks. High Probability.")
                    elif score == 2:
                        st.warning(f"⚠️ **CAUTION:** Number {user_num} has mechanical issues. Proceed with risk.")
                    else:
                        st.error(f"🛑 **DO NOT RACE:** Number {user_num} failed critical tests.")

            with tab2:
                st.subheader("Find Race-Ready Numbers")
                st.write("Scanning all 49 numbers against the protocol...")
                
                green_light_nums = []
                yellow_light_nums = []
                
                for num in range(1, 50):
                    s_pass, _ = check_split_health(num, recent_pool)
                    n_pass, _ = check_neighbor_traffic(num, recent_pool)
                    g_pass, g_reason = check_gap_validation(num, last_draw_row)
                    
                    if s_pass and n_pass and g_pass:
                        green_light_nums.append((num, g_reason))
                    elif g_pass and (s_pass or n_pass):
                        yellow_light_nums.append((num, g_reason))
                
                st.markdown("### 🟢 Green Light (Passed All Tests)")
                if green_light_nums:
                    for num, reason in green_light_nums:
                        st.success(f"**Number {num}**: {reason}")
                else:
                    st.write("No perfect matches found.")
                    
                st.markdown("### 🟡 Yellow Light (Gap Validated, but crowded)")
                if yellow_light_nums:
                    for num, reason in yellow_light_nums:
                        st.warning(f"**Number {num}**: {reason}")
                else:
                    st.write("No secondary matches found.")

    except Exception as e:
        st.error(f"Error: {e}")
