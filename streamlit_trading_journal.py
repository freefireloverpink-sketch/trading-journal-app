import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import datetime

DB_FILE = 'trading_journal.db'

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
            pnl REAL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_trade(date, symbol, qty, price, direction, pnl, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO trades (date, symbol, qty, price, direction, pnl, notes) VALUES (?, ?, ?, ?, ?, ?, ?);",
        (date, symbol, qty, price, direction, pnl, notes)
    )
    conn.commit()
    conn.close()

def load_trades():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    return df

init_db()

st.set_page_config(page_title='Trading Journal', layout='wide')
st.title("Advanced Trading Journal 📈")

# Trade Input
with st.form("Add Trade", clear_on_submit=True):
    st.subheader("Add New Trade")
    date = st.date_input("Date", value=datetime.date.today())
    symbol = st.text_input("Symbol")
    qty = st.number_input("Quantity", min_value=1, value=100)
    price = st.number_input("Price", min_value=0.0, format="%.2f")
    direction = st.selectbox("Direction", ["Buy", "Sell"])
    pnl = st.number_input("Profit/Loss", format="%.2f")
    notes = st.text_area("Trade Notes")
    submitted = st.form_submit_button("Add")
    if submitted:
        add_trade(str(date), symbol, int(qty), float(price), direction, float(pnl), notes)
        st.success("Trade added!")

# Display Table & Stats
df = load_trades()
tab1, tab2, tab3 = st.tabs(["Trades", "Stats", "Equity Curve"])

with tab1:
    st.subheader("Your Trades")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No trades yet.")

with tab2:
    st.subheader("Trade Statistics")
    if not df.empty:
        win_trades = df[df['pnl'] > 0]
        loss_trades = df[df['pnl'] < 0]
        st.metric("Total Trades", len(df))
        st.metric("Win Rate (%)", round(100 * len(win_trades) / len(df), 2) if len(df) > 0 else 0)
        st.metric("Average Win", round(win_trades['pnl'].mean(), 2) if not win_trades.empty else 0)
        st.metric("Average Loss", round(loss_trades['pnl'].mean(), 2) if not loss_trades.empty else 0)
        st.metric("Profit Factor", round(win_trades['pnl'].sum() / abs(loss_trades['pnl'].sum()), 2) if not loss_trades.empty else "N/A")
    else:
        st.info("Stats will show after you log trades.")

with tab3:
    st.subheader("Equity Curve")
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
        df = df.sort_values('date')
        df['CumulativeEquity'] = df['pnl'].cumsum()
        eq_curve = df.groupby('date')['CumulativeEquity'].last().reset_index()
        fig, ax = plt.subplots(figsize=(9,4))
        ax.plot(eq_curve['date'], eq_curve['CumulativeEquity'], marker='o', linewidth=2)
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Equity")
        ax.set_title("Equity Curve")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Add trades for the equity curve.")

st.caption("Built with Streamlit. For more advanced features and dashboards, check out open-source trading journal projects on GitHub.[web:2]")

