import streamlit as st
import pandas as pd



dataset= "assets/data/nft_transactions2.csv"
# Load data
@st.cache_data
def load_data():
    # Replace with your actual file path
    return pd.read_csv(dataset)




@st.cache_data
def overview_load_data():
    df = pd.read_csv(dataset)
    df['tx_timestamp'] = pd.to_datetime(df['tx_timestamp'], errors='coerce')
    df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
    df['days_held'] = (df['tx_timestamp'] - df['created_date']).dt.days

    if 'usd_gain' not in df.columns:
        if 'gain' in df.columns and 'to_usd' in df.columns:
            df['usd_gain'] = df['gain'] * df['to_usd']
        else:
            df['usd_gain'] = np.nan

    df.dropna(subset=['tx_timestamp', 'usd_price'], inplace=True)
    return df