import streamlit as st

def display_sidebar():
    st.sidebar.title("Navigation")
    return st.sidebar.radio("Go to", ["Home", "Analytics", "Reports", "Settings"])
