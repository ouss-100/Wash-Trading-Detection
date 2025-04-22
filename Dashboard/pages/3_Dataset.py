import streamlit as st
from utils.data_loader import load_data

def main():
    st.set_page_config(layout="wide")
    st.title("NFT Transaction Network Analysis")
    df = load_data()
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
