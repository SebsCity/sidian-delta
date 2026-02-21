import streamlit as st
import random
import numpy as np

MAX_NUMBER = 49

# ==========================================
# STRUCTURE HELPERS
# ==========================================

def generate_balanced_set():
    lows = random.sample(range(1,25), 3)
    highs = random.sample(range(25,50), 3)
    return sorted(lows + highs)

def generate_low_heavy_set():
    lows = random.sample(range(1,25), 4)
    highs = random.sample(range(25,50), 2)
    return sorted(lows + highs)

def generate_high_heavy_set():
    lows = random.sample(range(1,25), 2)
    highs = random.sample(range(25,50), 4)
    return sorted(lows + highs)

def generate_even_heavy_set():
    evens = random.sample([x for x in range(1,50) if x%2==0], 4)
    odds = random.sample([x for x in range(1,50) if x%2!=0], 2)
    return sorted(evens + odds)

def generate_wide_spread_set():
    return sorted(random.sample(range(1,50), 6))

# ==========================================
# OVERLAP CONTROL
# ==========================================

def limit_overlap(portfolio, new_set, max_overlap=2):
    for existing in portfolio:
        if len(set(existing) & set(new_set)) > max_overlap:
            return False
    return True

def build_portfolio(size):
    portfolio = []
    generators = [
        generate_balanced_set,
        generate_low_heavy_set,
        generate_high_heavy_set,
        generate_even_heavy_set,
        generate_wide_spread_set
    ]

    while len(portfolio) < size:
        gen = random.choice(generators)
        candidate = gen()
        if limit_overlap(portfolio, candidate):
            portfolio.append(candidate)

    return portfolio

# ==========================================
# APP UI
# ==========================================

st.title("🔥 V7 – Structured Portfolio Engine")

st.write("""
This engine does NOT predict.
It builds disciplined, structured portfolios under randomness.
""")

portfolio_size = st.slider("Number of Sets", 1, 10, 5)

if st.button("Generate Structured Portfolio"):
    sets = build_portfolio(portfolio_size)

    for i, s in enumerate(sets, 1):
        st.write(f"Set {i}: {s}")
