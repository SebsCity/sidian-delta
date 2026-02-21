import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import re

# ==========================================
# DATABASE SETUP
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "database", "v6_draws.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            numbers TEXT,
            bonus INTEGER
        )
    """)
    conn.close()

init_db()

def get_history():
    if not os.path.exists(DB_PATH):
        st.warning("Database not found. Upload a sheet first.")
        return pd.DataFrame(columns=["id","numbers","bonus"])
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM draws ORDER BY id ASC", conn)
    except Exception as e:
        st.error(f"Failed reading database: {e}")
        df = pd.DataFrame(columns=["id","numbers","bonus"])
    finally:
        conn.close()
    return df

# ==========================================
# SAFE PARSERS
# ==========================================
def safe_int(x):
    try:
        return int(float(str(x).strip()))
    except:
        return None

def parse_manual_input(text):
    parts = re.split(r"[,\s]+", text.strip())
    nums = [safe_int(p) for p in parts if safe_int(p) is not None]
    return nums

def parse_numbers_str(s):
    return [safe_int(x) for x in str(s).split(",") if safe_int(x) is not None]

# ==========================================
# MOBILE-SAFE WEIGHTED ENGINE
# ==========================================
MAX_NUMBER = 49

def train_weighted_model(history):
    counts_main = np.zeros(MAX_NUMBER)
    counts_bonus = np.zeros(MAX_NUMBER)

    for _, row in history.iterrows():
        nums = parse_numbers_str(row["numbers"])
        for n in nums:
            if n and 1 <= n <= MAX_NUMBER:
                counts_main[n-1] += 1
        b = safe_int(row["bonus"])
        if b and 1 <= b <= MAX_NUMBER:
            counts_bonus[b-1] += 1

    # Weighted probabilities (recent numbers slightly more weight)
    weights_main = counts_main + 0.5 * np.roll(counts_main, 1)  # recent influence
    weights_bonus = counts_bonus + 0.5 * np.roll(counts_bonus, 1)

    return weights_main, weights_bonus

def predict_next_draw(weights_main, weights_bonus):
    top6_idx = weights_main.argsort()[-6:][::-1] + 1
    bonus_pred = int(weights_bonus.argmax()) + 1
    return list(top6_idx), bonus_pred

# ==========================================
# APP UI
# ==========================================
st.title("🔥 SIDIAN DELTA V6 – Mobile-Safe AI Engine")

# --- SIDEBAR UPLOAD ---
with st.sidebar:
    st.header("📂 Upload Draw History")
    file = st.file_uploader("CSV or XLSX", type=["csv", "xlsx"])
    if file:
        df_new = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        st.write("Preview:", df_new.head())
        if st.button("Commit to Database"):
            m_cols = df_new.columns[:6]
            b_col = df_new.columns[6] if len(df_new.columns) > 6 else None
            cleaned = pd.DataFrame()
            cleaned["numbers"] = df_new[m_cols].apply(
                lambda row: ",".join(str(safe_int(x)) for x in row if safe_int(x) is not None),
                axis=1
            )
            cleaned["bonus"] = df_new[b_col].apply(safe_int) if b_col else None
            cleaned = cleaned.dropna()
            conn = sqlite3.connect(DB_PATH)
            cleaned.to_sql("draws", conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"{len(cleaned)} rows committed successfully!")
            st.rerun()

# --- MAIN PANEL ---
history = get_history()
st.subheader("📊 Database Status")
st.write(f"Stored Draws: {len(history)}")

if len(history) < 10:
    st.info("Upload at least 10 draws for reliable weighted AI predictions.")
else:
    st.subheader("🔮 Generate Next Prediction")
    weights_main, weights_bonus = train_weighted_model(history)
    if st.button("Run Weighted AI Engine"):
        pred_nums, pred_bonus = predict_next_draw(weights_main, weights_bonus)
        st.success(f"Predicted Main Numbers: {pred_nums}")
        st.success(f"Predicted Bonus: {pred_bonus}")

    st.subheader("🧪 Manual Basket Backtest")
    manual_input = st.text_input(
        "Enter past draw to test (6 numbers + bonus, spaces/commas OK)",
        placeholder="5 12 19 27 33 41 9"
    )
    if manual_input:
        parsed = parse_manual_input(manual_input)
        if len(parsed) < 7:
            st.warning("Enter 6 main numbers + 1 bonus")
        else:
            test_nums = parsed[:6]
            test_bonus = parsed[6]
            pred_main, pred_bonus = predict_next_draw(weights_main, weights_bonus)
            match_count = len(set(test_nums) & set(pred_main))
            bonus_match = (test_bonus == pred_bonus)
            st.write(f"Main Matches: {match_count}/6")
            st.write(f"Bonus Match: {bonus_match}")
