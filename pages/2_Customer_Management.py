import streamlit as st
import pandas as pd
import datetime
import altair as alt
import customer_management_utility as util

st.set_page_config(page_title="Customer Overview", page_icon="🏠", layout="wide")

title_col, customer_selection = st.columns([1, 2])
with title_col:
    st.title("Customer Management")

with customer_selection:
    df = pd.read_csv("data/SALES ORDER.csv")
    options = df.groupby('Customer Name')['Total Amount'].sum().sort_values(ascending=False).index.tolist()
    selection = st.selectbox("Choose Customer:", options)

st.markdown(f"## {selection} Sales Overview")

filtered_df = df[df['Customer Name'] == selection].reset_index(drop=True)
filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
filtered_df = filtered_df.sort_values('Date')

# Bar chart + current date line only
bar = alt.Chart(filtered_df).mark_bar().encode(
    x='Date:T',
    y='Total Amount:Q'
)
line_current = alt.Chart(pd.DataFrame({'Date': [datetime.datetime.now()]})).mark_rule(
    color='red', strokeDash=[5,5]
).encode(x='Date:T')

st.altair_chart(bar + line_current, use_container_width=True)

diff_days = filtered_df['Date'].diff().dt.days
average_reorder_time = diff_days.rolling(4, min_periods=1).mean().iloc[-1]
last_order_date = filtered_df['Date'].max()
days_since_last_order = (datetime.datetime.now() - last_order_date).days
average_order_amount = filtered_df['Total Amount'].rolling(4, min_periods=1).mean().iloc[-1]

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Average Reorder Time (days)", f"{average_reorder_time:.1f}")
kpi2.metric("Days Since Last Order", f"{days_since_last_order}")
kpi3.metric("Average Order Amount (past 4 orders)", f"₱{average_order_amount:,.2f}")
kpi4.metric("Total Orders", len(filtered_df))
kpi5.metric("Total Revenue", f"₱{filtered_df['Total Amount'].sum():,.2f}")

st.markdown("---")

st.subheader("Customer Overview")
overview_col1, overview_col2 = st.columns(2)
contact_column = "Customer's Name"
contact_name = filtered_df.at[0, contact_column]

overview_col1.write(f"**Customer Name:** {filtered_df.at[0, 'Customer Name']}")
overview_col1.write(f"**Account:** {filtered_df.at[0, 'Account']}")
overview_col2.write(f"**Location:** {filtered_df.at[0, 'Location']}")
overview_col2.write(f"**Type:** {filtered_df.at[0, 'Type']}")
overview_col2.write(f"**Contact Name:** {contact_name}")

st.markdown("---")

st.subheader("Recent Orders")
st.dataframe(filtered_df[['Date', "Total Amount", "Type", "Location"]].tail(10).reset_index(drop=True))
