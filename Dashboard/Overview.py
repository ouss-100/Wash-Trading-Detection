import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import overview_load_data


# ✅ Set page config
st.set_page_config(
    page_title="NFT Sales Dashboard",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="collapsed"
)



def apply_filters(df):
    st.subheader("🔎 Filter Transactions")

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_chains = st.multiselect(
            "Select Chains", options=df['chain'].dropna().unique(),
            default=list(df['chain'].dropna().unique())
        )
    with col2:
        selected_token_types = st.multiselect(
            "Select Token Types", options=df['token_type'].dropna().unique(),
            default=list(df['token_type'].dropna().unique())
        )
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=[df['tx_timestamp'].min().date(), df['tx_timestamp'].max().date()],
            min_value=df['tx_timestamp'].min().date(),
            max_value=df['tx_timestamp'].max().date()
        )

    min_price, max_price = st.slider(
        "Price Range (USD)",
        float(df['usd_price'].min()), float(df['usd_price'].max()),
        (float(df['usd_price'].min()), float(df['usd_price'].max()))
    )

    filtered = df[
        (df['chain'].isin(selected_chains)) &
        (df['token_type'].isin(selected_token_types)) &
        (df['tx_timestamp'].dt.date.between(date_range[0], date_range[1])) &
        (df['usd_price'].between(min_price, max_price))
    ]
    return filtered

def show_kpis(filtered_df):
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sales", f"${filtered_df['usd_price'].sum():,.2f}")
    with col2:
        st.metric("Average Sale Price", f"${filtered_df['usd_price'].mean():,.2f}")
    with col3:
        st.metric("Total NFTs Sold", filtered_df.shape[0])
    with col4:
        st.metric("Unique Collections", filtered_df['collection_name'].nunique())

def tab_overview(filtered_df):
    st.subheader("Sales Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(filtered_df, names='chain', values='usd_price', title='Sales Distribution by Chain')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(filtered_df, names='token_type', values='usd_price', title='Sales Distribution by Token Type')
        st.plotly_chart(fig, use_container_width=True)


def tab_performance(filtered_df):
    st.subheader("Performance Metrics")
    col1, col2 = st.columns(2)
    with col1:
        avg_price_chain = filtered_df.groupby('chain')['usd_price'].mean().reset_index()
        fig = px.bar(avg_price_chain, x='chain', y='usd_price', title='Average Sale Price by Chain', color='chain')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        total_sales_chain = filtered_df.groupby('chain')['usd_price'].sum().reset_index()
        fig = px.bar(total_sales_chain, x='chain', y='usd_price', title='Total Sales Volume by Chain', color='chain')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gains Analysis")
    fig = px.scatter(
        filtered_df.dropna(subset=['usd_gain']),
        x='days_held', y='usd_gain', color='chain',
        size='usd_price', hover_name='nft_name',
        title='Holding Period vs. USD Gain', log_y=True
    )
    st.plotly_chart(fig, use_container_width=True)

def tab_collections(filtered_df):
    st.subheader("Top Collections")
    top_collections = filtered_df.groupby('collection_name').agg({
        'usd_price': 'sum', 'token_id': 'count'
    }).sort_values('usd_price', ascending=False).head(10).reset_index()

    fig = px.bar(
        top_collections, x='collection_name', y='usd_price',
        title='Top 10 Collections by Sales Volume (USD)',
        color='usd_price', hover_data=['token_id']
    )
    st.plotly_chart(fig, use_container_width=True)


def tab_transactions(filtered_df):
    st.subheader("Recent Transactions")
    st.dataframe(
        filtered_df.sort_values('tx_timestamp', ascending=False).head(20)[[
            'tx_timestamp', 'nft_name', 'collection_name', 'chain',
            'price', 'token', 'usd_price', 'from_account', 'to_account'
        ]],
        use_container_width=True
    )

    st.subheader("Transaction Timeline")
    timeline_df = filtered_df.groupby(pd.Grouper(key='tx_timestamp', freq='H')).agg({
        'usd_price': 'sum', 'token_id': 'count'
    }).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timeline_df['tx_timestamp'], y=timeline_df['usd_price'],
                             name='Sales Volume (USD)', line=dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=timeline_df['tx_timestamp'], y=timeline_df['token_id'],
                             name='Number of Sales', line=dict(color='firebrick'), yaxis='y2'))

    fig.update_layout(
        title='Hourly Transaction Volume and Count',
        yaxis=dict(title='Sales Volume (USD)'),
        yaxis2=dict(title='Number of Sales', overlaying='y', side='right'),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    df = overview_load_data()
    st.title("📊 NFT Sales Analytics Dashboard")
    st.markdown("Comprehensive overview of NFT sales data with interactive visualizations. Use the filters below to customize your view.")
    
    filtered_df = apply_filters(df)
    show_kpis(filtered_df)

    # 📁 Tabs for organized views
    tabs = st.tabs(["📈 Overview", "📊 Performance", "💎 Top Collections", "🔁 Transactions"])

    with tabs[0]:
        tab_overview(filtered_df)

    with tabs[1]:
        tab_performance(filtered_df)

    with tabs[2]:
        tab_collections(filtered_df)

    with tabs[3]:
        tab_transactions(filtered_df)

    st.markdown("---")
    st.caption("NFT Sales Dashboard - Powered by Streamlit")


if __name__ == "__main__":
    main()
