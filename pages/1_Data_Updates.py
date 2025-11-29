import streamlit as st
import pandas as pd
import addtl_info as util
import os

st.markdown("### Upload Your Excel Sheet")

# File uploader reacts immediately
sheet = st.file_uploader("Upload your excel sheets here")
sheet_options = ['Sales Order', "Per item Summary", "Customer Masterlist"]
sheet_type = st.selectbox("Select data type", sheet_options)

df = None
if sheet:
    st.markdown("### Uploaded Data")
    df = util.convert_sales_file_to_df(sheet)
    st.dataframe(df)

# Submit button triggers saving
submitted = st.button("Submit Data")
if submitted and sheet_options=="Sales Order":
    if df is not None:
        file_path = 'data/SALES ORDER.csv'

        if os.path.isfile(file_path):
            existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
            df = df[existing_cols]
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, mode='w', index=False, header=True)
        st.success("Data saved successfully!")
    else:
        st.warning("Please upload a file before submitting.")
