import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import datetime

DB_FILE = 'trading_journal.db'

# --- Initialize or connect to the database ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            symbol TEXT,
            qty INTEGER,
            price REAL,
            direction TEXT,
            pnl REAL
        )
    ''')
    conn.commit()
    conn.close()

def add_trade(date, symbol, qty, price, direction, pnl):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO trades (date, symbol, qty, price, direction, pnl) VALUES (?, ?, ?, ?, ?, ?);",
        (date, symbol, qty, price, direction, pnl)
    )
    conn.commit()
    conn.close()

def load_trades():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    return df

init_db()

st.title("Trading Journal")

# --- Trade Input Form ---
with st.form("Add Trade", clear_on_submit=True):
    st.header("Add New Trade")
    date = st.date_input("Date", value=datetime.date.today())
    symbol = st.text_input("Symbol (e.g. AAPL)")
    qty = st.number_input("Quantity", min_value=1, value=100)
    price = st.number_input("Price", min_value=0.0, format="%.2f")
    direction = st.selectbox("Direction", ["Buy", "Sell"])
    pnl = st.number_input("Profit/Loss", format="%.2f")
    submitted = st.form_submit_button("Add Trade")
    if submitted:
        add_trade(str(date), symbol, int(qty), float(price), direction, float(pnl))
        st.success("Trade Added!")

# --- Show Trades Table ---
trades_df = load_trades()
if not trades_df.empty:
    st.header("All Trades")
    st.dataframe(trades_df)

    # --- Equity Curve Plot ---
    st.header("Equity Curve")
    trades_df['date'] = pd.to_datetime(trades_df['date'], errors='coerce', dayfirst=True)
    trades_df.sort_values('date', inplace=True)
    trades_df['CumulativeEquity'] = trades_df['pnl'].cumsum()
    daily_equity = trades_df.groupby('date')['CumulativeEquity'].last().reset_index()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(daily_equity['date'], daily_equity['CumulativeEquity'], marker='o')
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Equity")
    ax.set_title("Equity Curve")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No trades yet. Add a trade to begin!")

