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
    df = st.cache_data(pd.read_csv)("data/SALES ORDER.csv")
    options = df.groupby('Customer Name')['Total Amount'].sum().sort_values(ascending=False).index.tolist()
    selection = st.selectbox("Choose Customer:", options)

st.markdown(f"## Sales Overview: {selection}")

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
collections_df = st.cache_data(pd.read_csv)("data/SUMMARY COLLECTIONS.csv")
receivables_df = st.cache_data(pd.read_csv)("data/ACCOUNTS RECEIVABLE.csv")


f_collections_df = collections_df[collections_df['Customer Name'] == selection].reset_index(drop=True)
f_receivables_df = receivables_df[receivables_df['Customer Name'] == selection].reset_index(drop=True)

# Convert 'Date' to datetime
f_collections_df['Date'] = pd.to_datetime(f_collections_df['Date'])
f_receivables_df['Date'] = pd.to_datetime(f_receivables_df['Date'])

st.markdown("### Collections and Receivables")
# --- Collections chart (bar + current-date line) ---
collections_bar = (
    alt.Chart(f_collections_df)
    .mark_bar()
    .encode(
        x=alt.X('Date:T'),
        y=alt.Y('Check Amount:Q'),
        color=alt.Color('Type:N', legend=alt.Legend(title="Collections Type"))
    )
)

collections_line_current = (
    alt.Chart(pd.DataFrame({'Date': [datetime.datetime.now()]}))
    .mark_rule(color='red', strokeDash=[5, 5])
    .encode(x='Date:T')
)

collections_chart = alt.layer(
    collections_bar,
    collections_line_current
)

# --- Receivables chart (bar + current-date line) ---
receivables_bar = (
    alt.Chart(f_receivables_df)
    .mark_bar()
    .encode(
        x=alt.X('Date:T'),
        y=alt.Y('Balance:Q'),
        color=alt.Color('Type:N', legend=alt.Legend(title="Receivables Type"))
    )
)

receivables_line_current = (
    alt.Chart(pd.DataFrame({'Date': [datetime.datetime.now()]}))
    .mark_rule(color='red', strokeDash=[5, 5])
    .encode(x='Date:T')
)

receivables_chart = alt.layer(
    receivables_bar,
    receivables_line_current
)

# --- Final vertically stacked charts with shared x and shared y ---
final_chart = (
    alt.vconcat(collections_chart, receivables_chart)
    .resolve_scale(x='shared', y='shared')
    .resolve_legend(color='independent')
)

final_chart

ckpi1, ckpi2, ckpi3, ckpi4 = st.columns(4)

# Average amounts of the last 4 transactions (use tail(4) as before)
average_collection_amount = f_collections_df['Check Amount'].tail(4).mean()
average_receivable_amount = f_receivables_df['Balance'].tail(4).mean()

# Convert 'Date' to datetime
f_collections_df['Date'] = pd.to_datetime(f_collections_df['Date'])
f_receivables_df['Date'] = pd.to_datetime(f_receivables_df['Date'])

# --- Average Collection Period ---
# Get last 4 distinct collection dates
distinct_collection_dates = f_collections_df['Date'].drop_duplicates().tail(4).sort_values()
if len(distinct_collection_dates) > 1:
    collection_intervals = distinct_collection_dates.diff().dt.days.dropna()
    average_collection_period = collection_intervals.mean()
else:
    average_collection_period = 0  # Not enough distinct dates to calculate interval

# --- Average Receivable Period ---
# Get last 4 distinct receivable dates
distinct_receivable_dates = f_receivables_df['Date'].drop_duplicates().tail(4).sort_values()
if len(distinct_receivable_dates) > 1:
    receivable_intervals = distinct_receivable_dates.diff().dt.days.dropna()
    average_receivable_period = receivable_intervals.mean()
else:
    average_receivable_period = 0  # Not enough distinct dates to calculate interval

ckpi1.metric("Average Collection Period (days)", f"{average_collection_period:.1f}")
ckpi2.metric("Average Receivable Period (days)", f"{average_receivable_period:.1f}")
ckpi3.metric("Average Collection Amount", f"₱{average_collection_amount:,.2f}")
ckpi4.metric("Average Receivable Amount", f"₱{average_receivable_amount:,.2f}")
