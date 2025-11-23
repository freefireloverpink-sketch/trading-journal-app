import streamlit as st
import pandas as pd
import sqlite3
import datetime
import matplotlib.pyplot as plt
import numpy as np

DB_FILE = "trading_journal.db"

# Initialize DB and trades table
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            instrument TEXT,
            bos BOOLEAN,
            retest BOOLEAN,
            fib_retracement TEXT,
            strike TEXT,
            buy_sell TEXT,
            entry_price REAL,
            exit_price REAL,
            sl REAL,
            tp REAL,
            risk_to_reward REAL,
            trade_outcome TEXT,
            profit_loss REAL,
            tags TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# Load all trades as DataFrame
@st.cache_data(ttl=60)
def load_trades():
    df = pd.read_sql("SELECT * FROM trades ORDER BY date DESC", conn, parse_dates=["date"])
    return df

# Add new trade to DB
def add_trade(data):
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades
        (date, instrument, bos, retest, fib_retracement, strike, buy_sell,
         entry_price, exit_price, sl, tp, risk_to_reward, trade_outcome, profit_loss, tags, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()

# Update existing trade
def update_trade(trade_id, data):
    c = conn.cursor()
    c.execute('''
        UPDATE trades SET
        date=?, instrument=?, bos=?, retest=?, fib_retracement=?, strike=?, buy_sell=?,
        entry_price=?, exit_price=?, sl=?, tp=?, risk_to_reward=?, trade_outcome=?, profit_loss=?, tags=?, notes=?
        WHERE id=?
    ''', data + (trade_id,))
    conn.commit()

# Delete trade
def delete_trade(trade_id):
    c = conn.cursor()
    c.execute("DELETE FROM trades WHERE id=?", (trade_id,))
    conn.commit()

# Calculate Risk-to-Reward ratio
def calc_risk_reward(entry, sl, tp, buy_sell):
    try:
        entry = float(entry)
        sl = float(sl)
        tp = float(tp)
        buy_sell = buy_sell.lower()
        if buy_sell == 'buy':
            risk = entry - sl
            reward = tp - entry
        else:
            risk = sl - entry
            reward = entry - tp
        if risk > 0:
            return round(reward / risk, 2)
        else:
            return 0.0
    except:
        return None

st.title("Trading Journal Web App")

# Sidebar: Add new trade form
st.sidebar.header("Add New Trade")

with st.sidebar.form(key='add_trade_form', clear_on_submit=True):
    new_date = st.date_input("Date", datetime.date.today())
    new_instrument = st.selectbox("Instrument", ["Nifty", "Bank Nifty", "Equity"])
    new_bos = st.checkbox("BOS")
    new_retest = st.checkbox("RETEST")
    new_fib_retracement_enabled = st.checkbox("Fibonacci Retracement Level")
    fib_levels = ['0.23-0.3%', '0.3-0.5%', '0.5-0.61%', '0.618-0.7%']
    new_fib_retracement = st.selectbox("Fib Levels", fib_levels) if new_fib_retracement_enabled else ''
    new_strike = st.text_input("Strike Chosen")
    new_buy_sell = st.selectbox("Buy/Sell", ["Buy", "Sell"])
    new_entry_price = st.text_input("Entry Price")
    new_exit_price = st.text_input("Exit Price")
    new_sl = st.text_input("SL")
    new_tp = st.text_input("TP")
    new_risk_reward = calc_risk_reward(new_entry_price, new_sl, new_tp, new_buy_sell)
    st.write(f"Risk-To-Reward Ratio (auto): {new_risk_reward if new_risk_reward is not None else 'Calc error'}")
    new_trade_outcome = st.selectbox("Trade Outcome", ["TP Hit", "SL Hit", "Breakeven"])
    new_profit_loss = st.text_input("Profit/Loss")
    new_tags = st.text_input("Tags (optional)")
    new_notes = st.text_area("Notes (optional)")
    submitted = st.form_submit_button("Add Trade")

    if submitted:
        if not (new_entry_price and new_exit_price and new_sl and new_tp and new_profit_loss):
            st.warning("Please fill all numeric fields correctly.")
        else:
            try:
                profit_loss_val = float(new_profit_loss)
                entry_price_val = float(new_entry_price)
                exit_price_val = float(new_exit_price)
                sl_val = float(new_sl)
                tp_val = float(new_tp)
                data = (
                    new_date.strftime('%d/%m/%Y'),
                    new_instrument,
                    int(new_bos),
                    int(new_retest),
                    new_fib_retracement,
                    new_strike,
                    new_buy_sell,
                    entry_price_val,
                    exit_price_val,
                    sl_val,
                    tp_val,
                    new_risk_reward if new_risk_reward is not None else 0,
                    new_trade_outcome,
                    profit_loss_val,
                    new_tags,
                    new_notes
                )
                add_trade(data)
                st.success("Trade added successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Load Data
df = load_trades()

# Showing trades table with edit and delete options
st.subheader("Your Trades")

if df.empty:
    st.info("No trades yet. Add trades from the sidebar.")
else:
    # Show filter by date
    unique_dates = df['date'].dropna().unique()
    selected_date = st.selectbox("Filter trades by Date", options=["All"] + list(unique_dates))
    if selected_date != "All":
        df_filtered = df[df['date'] == selected_date]
    else:
        df_filtered = df

    selected_id = st.selectbox("Select Trade ID to Edit/Delete", options=["None"] + df_filtered['id'].astype(str).tolist())

    st.dataframe(df_filtered[['id','date','instrument','buy_sell','entry_price','exit_price','profit_loss','trade_outcome']])

    if selected_id != "None":
        edit_trade = df[df['id'] == int(selected_id)].iloc[0]

        st.subheader("Edit Selected Trade")
        with st.form(key='edit_trade_form'):
            e_date = st.date_input("Date", datetime.datetime.strptime(edit_trade['date'], '%d/%m/%Y'))
            e_instrument = st.selectbox("Instrument", options=["Nifty", "Bank Nifty", "Equity"], index=["Nifty", "Bank Nifty", "Equity"].index(edit_trade['instrument']))
            e_bos = st.checkbox("BOS", value=bool(edit_trade['bos']))
            e_retest = st.checkbox("RETEST", value=bool(edit_trade['retest']))
            e_fib_enabled = st.checkbox("Fibonacci Retracement Level", value=bool(edit_trade['fib_retracement']))
            e_fib_levels = ['0.23-0.3%', '0.3-0.5%', '0.5-0.61%', '0.618-0.7%']
            e_fib_retracement = st.selectbox("Fib Levels", e_fib_levels, index=e_fib_levels.index(edit_trade['fib_retracement']) if edit_trade['fib_retracement'] in e_fib_levels else 0)
            e_strike = st.text_input("Strike Chosen", value=edit_trade['strike'])
            e_buy_sell = st.selectbox("Buy/Sell", options=["Buy", "Sell"], index=["Buy", "Sell"].index(edit_trade['buy_sell']))
            e_entry_price = st.text_input("Entry Price", value=str(edit_trade['entry_price']))
            e_exit_price = st.text_input("Exit Price", value=str(edit_trade['exit_price']))
            e_sl = st.text_input("SL", value=str(edit_trade['sl']))
            e_tp = st.text_input("TP", value=str(edit_trade['tp']))
            e_risk_reward = calc_risk_reward(e_entry_price, e_sl, e_tp, e_buy_sell)
            st.write(f"Risk-To-Reward Ratio (auto): {e_risk_reward if e_risk_reward is not None else 'Calc error'}")
            e_trade_outcome = st.selectbox("Trade Outcome", ["TP Hit", "SL Hit", "Breakeven"], index=["TP Hit", "SL Hit", "Breakeven"].index(edit_trade['trade_outcome']))
            e_profit_loss = st.text_input("Profit/Loss", value=str(edit_trade['profit_loss']))
            e_tags = st.text_input("Tags (optional)", value=edit_trade['tags'])
            e_notes = st.text_area("Notes (optional)", value=edit_trade['notes'])

            is_edit_submitted = st.form_submit_button("Save Changes")

            if is_edit_submitted:
                try:
                    data = (
                        e_date.strftime('%d/%m/%Y'),
                        e_instrument,
                        int(e_bos),
                        int(e_retest),
                        e_fib_retracement if e_fib_enabled else '',
                        e_strike,
                        e_buy_sell,
                        float(e_entry_price),
                        float(e_exit_price),
                        float(e_sl),
                        float(e_tp),
                        e_risk_reward if e_risk_reward is not None else 0,
                        e_trade_outcome,
                        float(e_profit_loss),
                        e_tags,
                        e_notes
                    )
                    update_trade(int(selected_id), data)
                    st.success("Trade updated successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("Delete Selected Trade") and selected_id != "None":
        delete_trade(int(selected_id))
        st.success("Trade deleted successfully!")
        st.experimental_rerun()

# Equity curve plot
st.subheader("Equity Curve")

if df.empty:
    st.info("No trades yet to plot equity curve.")
else:
    df_dates = pd.to_datetime(df['date'], dayfirst=True)
    grouped = df.groupby(df_dates)['profit_loss'].sum().cumsum().reset_index()
    grouped.rename(columns={'date': 'Date', 'profit_loss': 'Cumulative P&L'}, inplace=True)
    grouped['Date'] = pd.to_datetime(grouped['index'], dayfirst=True)
    grouped = grouped[['index', 'profit_loss']]
    dates = [datetime.datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S') for d in grouped.index]
    cum_pl = grouped['profit_loss'].tolist()

    # Smooth with moving average window 3
    window = 3
    if len(cum_pl) >= window:
        smooth = np.convolve(cum_pl, np.ones(window)/window, mode='same')
    else:
        smooth = cum_pl

    fig, ax = plt.subplots(figsize=(10,4))
    ax.axhline(0, color='gray', linestyle='--')

    # Color line segments green/red
    for i in range(len(smooth)-1):
        color = 'green' if smooth[i] >= 0 else 'red'
        ax.plot(dates[i:i+2], smooth[i:i+2], color=color, marker='o')

    ax.set_title("Smoothed Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative P&L")
    fig.autofmt_xdate()
    st.pyplot(fig)
