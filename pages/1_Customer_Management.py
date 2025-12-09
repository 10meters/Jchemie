import streamlit as st
import pandas as pd
import datetime
import altair as alt

st.set_page_config(page_title="Customer Overview", page_icon="🏠", layout="wide")

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Show login if not logged in
if not st.session_state.logged_in:
    password = st.text_input("Enter password:", type="password")
    if password:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.success("Login successful!")
        else:
            st.error("Incorrect password")
    if not st.session_state.logged_in:
        st.stop()  # Only stop if login is still False


title_col, customer_selection = st.columns([1, 2])
with title_col:
    st.title("Customer Management")

with customer_selection:
    df = st.cache_data(pd.read_csv)("data/SALES ORDER.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    cust_options = df.groupby('Customer Name')['Total Amount'].sum().sort_values(ascending=False).index.tolist()
    options = ["All Customers"] + cust_options
    selection = st.selectbox("Choose Customer:", options)

st.markdown(f"## Sales Overview: {selection}")

if selection == "All Customers":
    filtered_df = df.copy()
else:
    filtered_df = df[df['Customer Name'] == selection].reset_index(drop=True)

filtered_df = filtered_df.sort_values('Date')

bar = alt.Chart(filtered_df).mark_bar().encode(
    x='Date:T',
    y='Total Amount:Q'
)
line_current = alt.Chart(pd.DataFrame({'Date': [datetime.datetime.now()]})).mark_rule(
    color='red', strokeDash=[5,5]
).encode(x='Date:T')

st.altair_chart(bar + line_current, use_container_width=True)

if selection == "All Customers":
    grp = df.groupby('Customer Name')
    
    reorder_means = grp['Date'].apply(lambda x: x.sort_values().diff().dt.days.rolling(4, min_periods=1).mean().iloc[-1])
    average_reorder_time = reorder_means.median()
    
    last_dates = grp['Date'].max()
    days_since_last_order = (datetime.datetime.now() - last_dates).dt.days.median()
    
    amt_means = grp['Total Amount'].apply(lambda x: x.rolling(4, min_periods=1).mean().iloc[-1])
    average_order_amount = amt_means.median()
else:
    diff_days = filtered_df['Date'].diff().dt.days
    average_reorder_time = diff_days.rolling(4, min_periods=1).mean().iloc[-1]
    last_order_date = filtered_df['Date'].max()
    days_since_last_order = (datetime.datetime.now() - last_order_date).days
    average_order_amount = filtered_df['Total Amount'].rolling(4, min_periods=1).mean().iloc[-1]

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Median Reorder Time (days)", f"{average_reorder_time:.1f}")
kpi2.metric("Median Days Since Last Order", f"{days_since_last_order:.1f}")
kpi3.metric("Median Order Amount (past 4 orders)", f"₱{average_order_amount:,.2f}")
kpi4.metric("Total Orders", len(filtered_df))
kpi5.metric("Total Revenue", f"₱{filtered_df['Total Amount'].sum():,.2f}")

st.markdown("---")

if selection != "All Customers":
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

collections_df['Date'] = pd.to_datetime(collections_df['Date'])
receivables_df['Date'] = pd.to_datetime(receivables_df['Date'])

if selection == "All Customers":
    f_collections_df = collections_df.copy()
    f_receivables_df = receivables_df.copy()
else:
    f_collections_df = collections_df[collections_df['Customer Name'] == selection].reset_index(drop=True)
    f_receivables_df = receivables_df[receivables_df['Customer Name'] == selection].reset_index(drop=True)

st.markdown("### Collections and Receivables")

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

final_chart = (
    alt.vconcat(collections_chart, receivables_chart)
    .resolve_scale(x='shared', y='shared')
    .resolve_legend(color='independent')
)

final_chart

ckpi1, ckpi2, ckpi3, ckpi4 = st.columns(4)

if selection == "All Customers":
    col_grp = f_collections_df.groupby('Customer Name')
    average_collection_amount = col_grp['Check Amount'].apply(lambda x: x.tail(4).mean()).median()
    
    def get_period(dates):
        d_dates = dates.drop_duplicates().tail(4).sort_values()
        if len(d_dates) > 1:
            return d_dates.diff().dt.days.dropna().mean()
        return 0
    
    average_collection_period = col_grp['Date'].apply(get_period).median()

    rec_grp = f_receivables_df.groupby('Customer Name')
    average_receivable_amount = rec_grp['Balance'].apply(lambda x: x.tail(4).mean()).median()
    average_receivable_period = rec_grp['Date'].apply(get_period).median()

else:
    average_collection_amount = f_collections_df['Check Amount'].tail(4).mean()
    average_receivable_amount = f_receivables_df['Balance'].tail(4).mean()

    distinct_collection_dates = f_collections_df['Date'].drop_duplicates().tail(4).sort_values()
    if len(distinct_collection_dates) > 1:
        average_collection_period = distinct_collection_dates.diff().dt.days.dropna().mean()
    else:
        average_collection_period = 0

    distinct_receivable_dates = f_receivables_df['Date'].drop_duplicates().tail(4).sort_values()
    if len(distinct_receivable_dates) > 1:
        average_receivable_period = distinct_receivable_dates.diff().dt.days.dropna().mean()
    else:
        average_receivable_period = 0

ckpi1.metric("Median Collection Period (days)", f"{average_collection_period:.1f}")
ckpi2.metric("Median Receivable Period (days)", f"{average_receivable_period:.1f}")
ckpi3.metric("Median Collection Amount", f"₱{average_collection_amount:,.2f}")
ckpi4.metric("Median Receivable Amount", f"₱{average_receivable_amount:,.2f}")