import streamlit as st
import pandas as pd
import addtl_info as util
from io import BytesIO

st.set_page_config(page_title="Add Sheets", layout="wide", page_icon="🏠")

st.markdown("### Upload Your Excel Sheet")

# File uploader reacts immediately
sheet = st.file_uploader("Upload your excel sheets here", type=["xls", "xlsx"])
sheet_options = ['Sales Order', "Summary Collections", "Customer Masterlist", 
                 "Accounts Receivable", "Summary per Item", "Stock Level"]
sheet_type = st.selectbox("Select data type", sheet_options)

df = None

# Submit + overwrite
col1, col2 = st.columns([0.15, 0.85])
with col1:
    submitted = st.button("Submit Data")
with col2:
    overwrite = st.checkbox("Overwrite")

# Initialize session storage for each "file path"
if 'session_files' not in st.session_state:
    st.session_state.session_files = {}

# Helper function to get a session "file" as BytesIO
def get_session_file(file_path, df=None, overwrite=False):
    if overwrite or file_path not in st.session_state.session_files:
        buf = BytesIO()
        if df is not None:
            df.to_csv(buf, index=False)
        st.session_state.session_files[file_path] = buf
    else:
        # Append: read existing CSV, concatenate new data
        buf = st.session_state.session_files[file_path]
        buf.seek(0)
        existing_df = pd.read_csv(buf)
        combined_df = pd.concat([existing_df, df[existing_df.columns]], ignore_index=True)
        buf = BytesIO()
        combined_df.to_csv(buf, index=False)
        st.session_state.session_files[file_path] = buf
    return st.session_state.session_files[file_path]

# --- DATA HANDLING ---
if sheet and sheet_type=="Sales Order":
    st.markdown("### Uploaded Data")
    df = util.convert_sales_file_to_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Sales Order":
    if df is not None:
        file_path = 'data/SALES ORDER.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")

if sheet and sheet_type=="Summary Collections":
    st.markdown("### Uploaded Data")
    df = util.convert_collections_to_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Summary Collections":
    if df is not None:
        file_path = 'data/SUMMARY COLLECTIONS.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")

if sheet and sheet_type=="Accounts Receivable":
    st.markdown("### Uploaded Data")
    df = util.convert_receivables_to_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Accounts Receivable":
    if df is not None:
        file_path = 'data/ACCOUNTS RECEIVABLE.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")

if sheet and sheet_type=="Summary per Item":
    st.markdown("### Uploaded Data")
    df = util.convert_summary_to_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Summary per Item":
    if df is not None:
        file_path = 'data/SUMMARY PER ITEM.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")

if sheet and sheet_type=="Customer Masterlist":
    st.markdown("### Uploaded Data")
    df = util.convert_customer_masterlist_to_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Customer Masterlist":
    if df is not None:
        file_path = 'data/CUSTOMERS_LIST.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")

if sheet and sheet_type=="Stock Level":
    st.markdown("### Uploaded Data")
    df = util.process_raw_materials_stock_df(sheet)
    st.dataframe(df)

if submitted and sheet_type=="Stock Level":
    if df is not None:
        file_path = 'data/STOCK LEVELS.csv'
        get_session_file(file_path, df, overwrite)
        st.success("Data saved in session!")
    else:
        st.warning("Please upload a file before submitting.")
