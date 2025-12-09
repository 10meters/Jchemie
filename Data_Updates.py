import streamlit as st
import pandas as pd
import addtl_info as util
import os


st.set_page_config(page_title="Add Sheets", page_icon="🏠")
st.set_page_config(layout="wide")

# Change working directory to the folder where this script is located
cwd = os.path.dirname(os.path.abspath(__file__))
os.chdir(cwd)

# Make wide
st.set_page_config(
    page_title="Add Sheets",
    layout="wide",  # makes the app span the full width
    initial_sidebar_state="expanded"
)

st.markdown("### Upload Your Excel Sheet")

# File uploader reacts immediately
sheet = st.file_uploader("Upload your excel sheets here")
sheet_options = ['Sales Order', "Summary Collections", "Customer Masterlist", "Accounts Receivable", "Summary per Item", "Stock Level"]
sheet_type = st.selectbox("Select data type", sheet_options, type=["xls", "xlsx"])

df = None

# Added overwrite checkbox next to submit button
col1, col2 = st.columns([0.15, 0.85])
with col1:
    submitted = st.button("Submit Data")
with col2:
    overwrite = st.checkbox("Overwrite")

#
# SALES ORDER
#
if sheet and sheet_type=="Sales Order":
    st.markdown("### Uploaded Data")
    df = util.convert_sales_file_to_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Sales Order":
    if df is not None:
        file_path = 'data/SALES ORDER.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")


#
# SUMMARY COLLECTIONS
#
if sheet and sheet_type=="Summary Collections":
    st.markdown("### Uploaded Data")
    df = util.convert_collections_to_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Summary Collections":
    if df is not None:
        file_path = 'data/SUMMARY COLLECTIONS.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")


#
# RECEIVABLES
#
if sheet and sheet_type=="Accounts Receivable":
    st.markdown("### Uploaded Data")
    df = util.convert_receivables_to_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Accounts Receivable":
    if df is not None:
        file_path = 'data/ACCOUNTS RECEIVABLE.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")


#
# SUMMARY PER ITEM
#
if sheet and sheet_type=="Summary per Item":
    st.markdown("### Uploaded Data")
    df = util.convert_summary_to_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Summary per Item":
    if df is not None:
        file_path = 'data/SUMMARY PER ITEM.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")

#
# CUSTOMER MASTERLIST
#
if sheet and sheet_type=="Customer Masterlist":
    st.markdown("### Uploaded Data")
    df = util.convert_customer_masterlist_to_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Customer Masterlist":
    if df is not None:
        file_path = 'data/CUSTOMERS_LIST.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")


#
# STOCK LEVELS
#
if sheet and sheet_type=="Stock Level":
    st.markdown("### Uploaded Data")
    df = util.process_raw_materials_stock_df(sheet)
    st.dataframe(df)
if submitted and sheet_type=="Stock Level":
    if df is not None:
        file_path = 'data/STOCK LEVELS.csv'

        if os.path.isfile(file_path) and not overwrite:
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")