import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import datetime

DB_FILE = 'trading_journal.db'

# Initialize DB and trades table
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Symbol TEXT,
            Qty INTEGER,
            Price REAL,
            Direction TEXT,
            PnL REAL
        )
    ''')
    conn.commit()
    conn.close()

# Add a trade to the database
def add_trade(date, symbol, qty, price, direction, pnl):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (Date, Symbol, Qty, Price, Direction, PnL)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, symbol, qty, price, direction, pnl))
    conn.commit()
    conn.close()

# Load all trades from the database
def load_trades():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('SELECT * FROM trades', conn)
    conn.close()
    return df

init_db()

st.title("Trading Journal App")

# Trade entry section
st.header("Add a Trade")
with st.form("trade_form"):
    date = st.date_input("Date", value=datetime.date.today())
    symbol = st.text_input("Symbol")
    qty = st.number_input("Quantity", min_value=1)
    price = st.number_input("Price", min_value=0.0, format="%.2f")
    direction = st.selectbox("Direction", ['Buy', 'Sell'])
    pnl = st.number_input("Profit/Loss", format="%.2f")
    submitted = st.form_submit_button("Add Trade")
    if submitted:
        add_trade(str(date), symbol, int(qty), float(price), direction, float(pnl))
        st.success("Trade added!")

# Load trades
df = load_trades()
if not df.empty:
    st.header("Trades Table")
    st.dataframe(df)

    # Equity Curve section
    st.header("Equity Curve")

    # Ensure the 'Date' column is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df = df.sort_values('Date')

    # Compute cumulative equity = cumulative sum of PnL
    df['CumulativeEquity'] = df['PnL'].cumsum()

    # For daily equity curve, group by date (last equity value for each day)
    grouped = df.groupby('Date').agg({'CumulativeEquity': 'last'}).reset_index()

    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(grouped['Date'], grouped['CumulativeEquity'], marker='o', linestyle='-')
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.set_title("Equity Curve")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No trades found. Add trades above to see the equity curve.")


