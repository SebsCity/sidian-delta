import streamlit as st
import pandas as pd
import itertools

# --- CONFIGURATION & TITLE ---
st.set_page_config(page_title="Lottery Forensics: The Construction Protocol", layout="wide")
st.title("🕵️‍♂️ Lottery Forensics: The Master Protocol")
st.markdown("""
**System Status:** Operational  
**Strategy:** Unfazed (Debt) + Breadcrumbs (Spare Parts) + Intention (Next Move)  
**Objective:** Detect the 'Sleight of Hand' and predict the 'Manifestation'.
""")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ Configuration")
uploaded_file = st.sidebar.file_uploader("Upload Lottery History (CSV/Excel)", type=["csv", "xlsx"])
lookback_period = st.sidebar.slider("Backtest Range (Draws)", 10, 100, 50)

# --- LOGIC FUNCTIONS ---

def calculate_intention(row):
    """
    Calculates the 'Intention' for the NEXT draw based on N6 and Bonus.
    Logic: 
    1. Sum Intention (N6 + Bonus) -> Target Unit.
    2. Gap Intention (|N6 - Bonus|) -> Target Number.
    """
    try:
        n6 = int(row['N6'])
        bonus = int(row['Bonus'])
        
        intention_sum = n6 + bonus
        intention_unit = intention_sum % 10
        intention_gap = abs(n6 - bonus)
        
        return {
            "Intention Unit": intention_unit,
            "Intention Gap": intention_gap,
            "Raw Sum": intention_sum
        }
    except:
        return None

def find_unfazed_candidates(numbers, bonus):
    """
    Identifies 'Unfazed' numbers (Hidden Sums) in the current draw.
    These are numbers the machine 'built' but didn't drop.
    """
    draw_set = set(numbers)
    unfazed_counts = {}
    
    # Check all pairs in the draw (Construction via Addition)
    for a, b in itertools.combinations(numbers, 2):
        hidden_sum = a + b
        if hidden_sum <= 49 and hidden_sum not in draw_set:
            unfazed_counts[hidden_sum] = unfazed_counts.get(hidden_sum, 0) + 1
            
    # Check Difference with Bonus (Construction via Subtraction)
    for n in numbers:
        hidden_diff = abs(n - bonus)
        if hidden_diff > 0 and hidden_diff not in draw_set:
            unfazed_counts[hidden_diff] = unfazed_counts.get(hidden_diff, 0) + 1
            
    # Filter for strong signals (numbers that appear as calculations multiple times are 'Ghosts')
    strong_candidates = [num for num, count in unfazed_counts.items()]
    return strong_candidates

def check_breadcrumbs(target, numbers, bonus):
    """
    Checks if the 'Breadcrumbs' (Spare Parts) exist to hide the Target again.
    Returns: TRUE if parts exist (Machine can hide it), FALSE if parts missing (Machine must drop it).
    """
    # Check Addition parts
    for a, b in itertools.combinations(numbers, 2):
        if a + b == target:
            return True, f"Found {a}+{b}"
            
    # Check Subtraction parts
    for n in numbers:
        if abs(n - target) in numbers: # e.g. If Target is 14, and we have 24 and 10 (24-10=14)
            return True, f"Found subtraction pair for {target}"
            
    return False, "No Parts Found"

# --- MAIN APP LOGIC ---

if uploaded_file is not None:
    # Load Data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Standardize Columns (Ensure N1..N6, Bonus exist)
        cols_needed = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Bonus']
        if not all(col in df.columns for col in cols_needed):
            st.error(f"Data must contain columns: {cols_needed}")
        else:
            # --- ANALYSIS OF LATEST DRAW ---
            st.header("🔮 Next Draw Prediction")
            
            last_row = df.iloc[-1]
            last_numbers = [last_row[c] for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']]
            last_bonus = last_row['Bonus']
            
            st.subheader(f"Latest Draw Analysis (Date: {last_row.get('Date', 'Unknown')})")
            st.write(f"**Numbers Drawn:** {last_numbers} + **Bonus:** {last_bonus}")
            
            # 1. Determine Intention
            intention = calculate_intention(last_row)
            
            # 2. Find Unfazed (The Debt)
            unfazed_raw = find_unfazed_candidates(last_numbers, last_bonus)
            
            # 3. Filter by Breadcrumbs (The Construction Scan)
            final_predictions = []
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 1. The Intention")
                st.info(f"**Target Unit:** {intention['Intention Unit']} (from Sum {intention['Raw Sum']})")
                st.info(f"**Target Gap:** {intention['Intention Gap']} (from N6-Bonus)")
                
            with col2:
                st.markdown("### 2. The Unfazed (Ghosts)")
                st.write(f"Hidden Sums Detected: {unfazed_raw[:5]}...")
            
            with col3:
                st.markdown("### 3. The Breadcrumb Scan")
                for target in unfazed_raw:
                    # We prioritize numbers that match the Intention Unit or Intention Gap
                    is_relevant = (target % 10 == intention['Intention Unit']) or (target == intention['Intention Gap'])
                    
                    if is_relevant:
                        has_parts, reason = check_breadcrumbs(target, last_numbers, last_bonus)
                        if not has_parts:
                            st.success(f"**{target}**: NO PARTS FOUND (Must Drop) 🟢")
                            final_predictions.append(target)
                        else:
                            st.warning(f"**{target}**: Parts Available ({reason}) 🔴")
            
            # --- FINAL BET GENERATION ---
            st.markdown("---")
            st.header("🎫 The Final Construction Ticket")
            
            if len(final_predictions) > 0:
                # Add the Intention Unit as a safety
                intention_play = [n for n in range(1, 50) if n % 10 == intention['Intention Unit']][:2]
                
                prediction_set = list(set(final_predictions + intention_play))
                
                # Generate Duos
                duos = list(itertools.combinations(prediction_set, 2))
                
                st.write(f"**Bankers (Unfazed & Naked):** {final_predictions}")
                st.write("**Top 3 Calculated Duos:**")
                for i, duo in enumerate(duos[:3]):
                    st.code(f"Bet {i+1}: {duo[0]} - {duo[1]}")
            else:
                st.warning("System detects high 'Sleight of Hand' risk. No naked numbers found. Play the Intention Unit.")

            # --- BACKTESTING ---
            st.markdown("---")
            st.header("📊 Backtest: Does this Strategy Work?")
            
            if st.button("Run Backtest on Last 50 Draws"):
                hits = 0
                total = 0
                log = []
                
                # Loop through history
                for i in range(len(df) - lookback_period - 1, len(df) - 1):
                    current_row = df.iloc[i]
                    next_row = df.iloc[i+1]
                    
                    # Run Strategy
                    curr_nums = [current_row[c] for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']]
                    curr_bonus = current_row['Bonus']
                    
                    intent = calculate_intention(current_row)
                    candidates = find_unfazed_candidates(curr_nums, curr_bonus)
                    
                    # Filter for 'No Breadcrumbs' + Matches Intention
                    picks = []
                    for cand in candidates:
                        if (cand % 10 == intent['Intention Unit']) or (cand == intent['Intention Gap']):
                             has_parts, _ = check_breadcrumbs(cand, curr_nums, curr_bonus)
                             if not has_parts:
                                 picks.append(cand)
                    
                    # Check Result
                    next_nums = [next_row[c] for c in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'Bonus']]
                    hit_count = len(set(picks).intersection(set(next_nums)))
                    
                    if len(picks) > 0:
                        total += 1
                        if hit_count >= 1:
                            hits += 1
                            log.append(f"Draw {current_row.get('Date', i)}: Predicted {picks} -> HIT {hit_count} numbers")
                
                st.metric("Strategy Win Rate (1+ Number Hit)", f"{round((hits/total)*100, 1)}%")
                with st.expander("See Backtest Log"):
                    for l in log:
                        st.text(l)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Awaiting Data Upload... The machine is waiting.")

