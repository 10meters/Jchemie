import streamlit as st
import pandas as pd

upload_form = st.form("Sheet Uploads")

with upload_form:
    sheet = st.file_uploader("Upload your excel sheets here")

    sheet_options = ['Sales Order', "Per item Summary", "Customer Masterlist"]

    sheet_type = st.selectbox("Select data type", sheet_options)

    submitted = st.form_submit_button("Submit Data")

    if submitted:
        df = pd.read_excel(sheet)
        st.dataframe(df)

