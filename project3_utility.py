import pandas as pd
import streamlit as st
import altair as alt

######################
# DATA CLEANING
#######################

@st.cache_data
def clean_data(df):
    # Ensure 'Date' column is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    # Clean 'Total Amount' and convert to numeric
    # Convert amount to numeric
    amount_col = 'Total Amount'
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    df = df.dropna(subset=[amount_col])

    return df


######################
# MONTHLY SALES VOLUME
#######################

@st.cache_data
def compute_monthly_sales(df):
    # Truncate to month start
    df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()

    # Group by month
    monthly_sales = df.groupby('Month')['Total Amount'].sum().reset_index()
    return monthly_sales

def show_monthly_sales_volume(df):
    # Create interactive Altair chart
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X('Month:T', axis=alt.Axis(format='%b %Y', labelAngle=-45)),
            y='Total Amount:Q',
            tooltip=['Month:T', 'Total Amount:Q']
        )
        .interactive()  # enables zoom/pan
    )

    return chart



######################
# SALES BENTO
#######################

@st.cache_data
def compute_periodic_sales(df, frequency: str):
    DATE_COL = "Date"
    AMOUNT_COL = "Total Amount"

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, AMOUNT_COL])

    if frequency == "weekly":
        df_daily = df.groupby(df[DATE_COL].dt.date)[AMOUNT_COL].sum().reset_index()
        df_daily[DATE_COL] = pd.to_datetime(df_daily[DATE_COL])
        df_weekly = df_daily.groupby(pd.Grouper(key=DATE_COL, freq="W-MON"))[AMOUNT_COL].sum().reset_index().sort_values(DATE_COL)

        min_date = df_weekly[DATE_COL].max() - pd.Timedelta(weeks=4)
        df_daily = df_daily[df_daily[DATE_COL] >= min_date]
        df_weekly = df_weekly[df_weekly[DATE_COL] >= min_date]

        growth_pct = 0 if len(df_weekly) < 2 else (df_weekly[AMOUNT_COL].iloc[-1] - df_weekly[AMOUNT_COL].iloc[-2]) / df_weekly[AMOUNT_COL].iloc[-2] * 100

        bars = alt.Chart(df_daily).mark_bar(color="steelblue").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y(f"{AMOUNT_COL}:Q", title="")
        )
        line = alt.Chart(df_weekly).mark_line(point=True, color="orange").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y(f"{AMOUNT_COL}:Q", title="")
        )

        last_val = df_weekly[AMOUNT_COL].iloc[-1]
        return last_val, growth_pct, bars, line

    elif frequency == "monthly":
        df_weekly = df.groupby(pd.Grouper(key=DATE_COL, freq="W-MON"))[AMOUNT_COL].sum().reset_index().sort_values(DATE_COL)
        df_monthly = df.groupby(pd.Grouper(key=DATE_COL, freq="MS"))[AMOUNT_COL].sum().reset_index().sort_values(DATE_COL)

        min_date = df_monthly[DATE_COL].max() - pd.DateOffset(months=4)
        df_weekly = df_weekly[df_weekly[DATE_COL] >= min_date]
        df_monthly = df_monthly[df_monthly[DATE_COL] >= min_date]

        growth_pct = 0 if len(df_monthly) < 2 else (df_monthly[AMOUNT_COL].iloc[-1] - df_monthly[AMOUNT_COL].iloc[-2]) / df_monthly[AMOUNT_COL].iloc[-2] * 100

        bars = alt.Chart(df_weekly).mark_bar(color="steelblue").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y(f"{AMOUNT_COL}:Q", title="")
        )
        line = alt.Chart(df_monthly).mark_line(point=True, color="orange").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y(f"{AMOUNT_COL}:Q", title="")
        )

        last_val = df_monthly[AMOUNT_COL].iloc[-1]
        
        return last_val, growth_pct, bars, line
    else:
        raise ValueError("frequency must be either 'weekly' or 'monthly'")

def show_sales_bento(df, frequency: str):

    last_val, growth_pct, bars, line = compute_periodic_sales(df, frequency)

    KPI_NAME = "Sales"
    kpi_col, chart_col = st.columns([1, 2])
    with kpi_col:
        st.metric(label=KPI_NAME, value=f"₱ {last_val:,.2f}", delta=f"{growth_pct:.2f}%")

    with chart_col:
        chart = (bars + line).properties(height=150)
        st.altair_chart(chart, use_container_width=True)



######################
# CUSTOMERS BENTO
#######################

@st.cache_data
def compute_customers_bento(df, frequency: str):
    DATE_COL = "Date"
    CUSTOMER_COL = "Customer Name"

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, CUSTOMER_COL])

    if frequency == "weekly":
        df_daily = df.groupby(df[DATE_COL].dt.date)[CUSTOMER_COL].nunique().reset_index()
        df_daily[DATE_COL] = pd.to_datetime(df_daily[DATE_COL])
        df_daily.rename(columns={CUSTOMER_COL: "CustomerCount"}, inplace=True)

        df_weekly = df.groupby(pd.Grouper(key=DATE_COL, freq="W-MON"))[CUSTOMER_COL].nunique().reset_index().sort_values(DATE_COL)
        df_weekly.rename(columns={CUSTOMER_COL: "CustomerCount"}, inplace=True)

        min_date = df_weekly[DATE_COL].max() - pd.Timedelta(weeks=4)
        df_daily = df_daily[df_daily[DATE_COL] >= min_date]
        df_weekly = df_weekly[df_weekly[DATE_COL] >= min_date]

        if len(df_weekly) < 2:
            growth_pct = 0
        else:
            prev_val = df_weekly["CustomerCount"].iloc[-2]
            curr_val = df_weekly["CustomerCount"].iloc[-1]
            growth_pct = 0 if prev_val == 0 else (curr_val - prev_val) / prev_val * 100

        bars = alt.Chart(df_daily).mark_bar(color="teal").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y("CustomerCount:Q", title="")
        )
        line = alt.Chart(df_weekly).mark_line(point=True, color="orange").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y("CustomerCount:Q", title="")
        )

        last_val = df_weekly["CustomerCount"].iloc[-1]

        return last_val, growth_pct, bars, line

    elif frequency == "monthly":
        df_weekly = df.groupby(pd.Grouper(key=DATE_COL, freq="W-MON"))[CUSTOMER_COL].nunique().reset_index().sort_values(DATE_COL)
        df_weekly.rename(columns={CUSTOMER_COL: "CustomerCount"}, inplace=True)

        df_monthly = df.groupby(pd.Grouper(key=DATE_COL, freq="MS"))[CUSTOMER_COL].nunique().reset_index().sort_values(DATE_COL)
        df_monthly.rename(columns={CUSTOMER_COL: "CustomerCount"}, inplace=True)

        min_date = df_monthly[DATE_COL].max() - pd.DateOffset(months=4)
        df_weekly = df_weekly[df_weekly[DATE_COL] >= min_date]
        df_monthly = df_monthly[df_monthly[DATE_COL] >= min_date]

        if len(df_monthly) < 2:
            growth_pct = 0
        else:
            prev_val = df_monthly["CustomerCount"].iloc[-2]
            curr_val = df_monthly["CustomerCount"].iloc[-1]
            growth_pct = 0 if prev_val == 0 else (curr_val - prev_val) / prev_val * 100

        bars = alt.Chart(df_weekly).mark_bar(color="teal").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y("CustomerCount:Q", title="")
        )
        line = alt.Chart(df_monthly).mark_line(point=True, color="orange").encode(
            x=alt.X(f"{DATE_COL}:T", title=""),
            y=alt.Y("CustomerCount:Q", title="")
        )

        last_val = df_monthly["CustomerCount"].iloc[-1]

        return last_val, growth_pct, bars, line

    else:
        raise ValueError("frequency must be either 'weekly' or 'monthly'")

def show_customers_bento(df, frequency: str):
    KPI_NAME = "Customers"

    last_val, growth_pct, bars, line = compute_customers_bento(df, frequency)

    kpi_col, chart_col = st.columns([1, 2])
    with kpi_col:
        st.metric(label=KPI_NAME, value=f"{last_val:,}", delta=f"{growth_pct:.2f}%")

    with chart_col:
        chart = (bars + line).properties(height=150)
        st.altair_chart(chart, use_container_width=True)


######################
# STATIC KPIS
#######################

@st.cache_data
def reorder_time_stats(df, customer_col='Customer Name', date_col='Date'):
    # Ensure dates are datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, customer_col])
    
    # Sort by customer and date
    df = df.sort_values([customer_col, date_col])
    
    # Compute reorder days
    df['Reorder_Days'] = df.groupby(customer_col)[date_col].diff().dt.days
    df_valid = df.dropna(subset=['Reorder_Days'])
    
    # Descriptive stats
    mean_val = df_valid['Reorder_Days'].mean()
    min_val = df_valid['Reorder_Days'].min()
    max_val = df_valid['Reorder_Days'].max()
    
    # IQR = Q3 - Q1
    q1 = df_valid['Reorder_Days'].quantile(0.25)
    q3 = df_valid['Reorder_Days'].quantile(0.75)
    iqr = q3 - q1
    
    return {
        "mean": mean_val,
        "min": min_val,
        "max": max_val,
        "range": max_val - min_val,
        "q1": q1,
        "q3": q3,
        "iqr": iqr
    }

@st.cache_data
def show_median_transaction_value(df):
    DATE_COL = "Date"
    AMOUNT_COL = "Total Amount"

    # Ensure proper dtypes
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, AMOUNT_COL])

    # Keep only the current year
    current_year = df[DATE_COL].dt.year.max()
    df_year = df[df[DATE_COL].dt.year == current_year]

    if df_year.empty:
        st.warning("No transactions available for the current year.")
        return

    # Median transaction value
    median_val = df_year[AMOUNT_COL].median()

    return median_val

@st.cache_data
def count_active_customers(df: pd.DataFrame, date_col: str = 'Date', customer_col: str = 'Customer Name') -> int:
    """
    Returns the number of active customers.
    Active = customers who placed an order within their individual Q3 reorder interval.
    Customers with fewer than 3 unique order dates are excluded.
    Fully vectorized for speed.
    """
    # Ensure datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, customer_col])

    # Clean customer names
    df[customer_col] = df[customer_col].str.strip()

    # Deduplicate multiple orders per customer per day
    df_unique = df.drop_duplicates(subset=[customer_col, date_col])

    # Sort by customer and date
    df_unique = df_unique.sort_values([customer_col, date_col])

    # Compute reorder intervals in days
    df_unique['prev_date'] = df_unique.groupby(customer_col)[date_col].shift(1)
    df_unique['interval'] = (df_unique[date_col] - df_unique['prev_date']).dt.days

    # Remove 0-day intervals
    df_unique = df_unique[df_unique['interval'] > 0]

    # Count unique dates per customer
    date_counts = df_unique.groupby(customer_col)[date_col].nunique()
    eligible_customers = date_counts[date_counts >= 3].index

    # Filter to eligible customers
    df_filtered = df_unique[df_unique[customer_col].isin(eligible_customers)]

    # Compute Q3 interval per customer
    q3_intervals = df_filtered.groupby(customer_col)['interval'].quantile(0.75) * 1.25

    # Get last order per customer
    last_order = df_filtered.groupby(customer_col)[date_col].max()

    # Latest date in dataset
    max_date = df_filtered[date_col].max()

    # Determine active customers
    active_mask = (max_date - last_order).dt.days <= q3_intervals
    active_customers_count = active_mask.sum()

    return active_customers_count


######################
# CHURN BENTO
######################
@st.cache_data
def compute_churn_bento(df, customer_col: str = "Customer Name", date_col: str = "Date"):
    """
    Compute historical churn stats.
    Inactive = customers who have not ordered within 1.25 * Q3 of their reorder interval.
    Returns last churn rate, growth %, and chart (bars + line with dual axis).
    """
    # Ensure datetime
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, customer_col])
    df[customer_col] = df[customer_col].str.strip()

    # Deduplicate orders per customer per day
    df_unique = df.drop_duplicates(subset=[customer_col, date_col])
    df_unique = df_unique.sort_values([customer_col, date_col])

    # Compute reorder intervals
    df_unique["prev_date"] = df_unique.groupby(customer_col)[date_col].shift(1)
    df_unique["interval"] = (df_unique[date_col] - df_unique["prev_date"]).dt.days
    df_unique = df_unique[df_unique["interval"] > 0]

    # Eligible customers = at least 3 unique order dates
    date_counts = df_unique.groupby(customer_col)[date_col].nunique()
    eligible_customers = date_counts[date_counts >= 3].index
    df_filtered = df_unique[df_unique[customer_col].isin(eligible_customers)]

    if df_filtered.empty:
        return None, 0, None

    # Q3 intervals per customer
    q3_intervals = df_filtered.groupby(customer_col)["interval"].quantile(0.75) * 1.25

    # Build daily records
    all_dates = pd.date_range(df_filtered[date_col].min(), df_filtered[date_col].max(), freq="D")

    churn_records = []
    for current_date in all_dates:
        last_orders = df_filtered[df_filtered[date_col] <= current_date].groupby(customer_col)[date_col].max()
        if last_orders.empty:
            continue

        # Align Q3 with last_orders
        aligned_q3 = q3_intervals.reindex(last_orders.index)
        inactive_mask = (current_date - last_orders).dt.days > aligned_q3

        churned = inactive_mask.sum()
        active = (~inactive_mask).sum()
        total = active + churned
        churn_rate = 0 if total == 0 else churned / total * 100

        churn_records.append({
            "Date": current_date,
            "ChurnRate": churn_rate,
            "Active": active,
            "Inactive": churned
        })

    churn_df = pd.DataFrame(churn_records)

    # Weekly aggregation (avg churn %)
    churn_df_weekly = churn_df.groupby(pd.Grouper(key="Date", freq="W-MON"))["ChurnRate"].mean().reset_index()

    # Restrict to last ~4 weeks
    min_date = churn_df_weekly["Date"].max() - pd.Timedelta(weeks=4)
    churn_df = churn_df[churn_df["Date"] >= min_date]
    churn_df_weekly = churn_df_weekly[churn_df_weekly["Date"] >= min_date]

    # Growth %
    if len(churn_df_weekly) < 2:
        growth_pct = 0
    else:
        prev_val = churn_df_weekly["ChurnRate"].iloc[-2]
        curr_val = churn_df_weekly["ChurnRate"].iloc[-1]
        growth_pct = 0 if prev_val == 0 else (curr_val - prev_val) / prev_val * 100

    last_val = churn_df_weekly["ChurnRate"].iloc[-1]

    # Clustered daily bars (slight opacity so line is always visible)
    daily_melted = churn_df.melt(
        id_vars="Date", 
        value_vars=["Active", "Inactive"], 
        var_name="Status", 
        value_name="Count"
    )

    bars = alt.Chart(daily_melted).mark_bar(opacity=0.7).encode(
        x=alt.X("Date:T", title=""),
        y=alt.Y("Count:Q", title="Customers"),
        color="Status:N",
        tooltip=["Date:T", "Status:N", "Count:Q"]
    )

    # Weekly churn rate line (drawn on top)
    line = alt.Chart(churn_df_weekly).mark_line(point=True, color="orange", strokeWidth=2).encode(
        x=alt.X("Date:T", title=""),
        y=alt.Y("ChurnRate:Q", title="Churn %", axis=alt.Axis(titleColor="orange"))
    )

    # Layer line on top of bars with dual axis
    chart = alt.layer(bars, line).resolve_scale(y="independent")

    return last_val, growth_pct, chart


def show_churn_bento(df):
    """
    Streamlit bento visualization for churn rate.
    """
    last_val, growth_pct, chart = compute_churn_bento(df)

    if last_val is None:
        st.warning("Not enough customer data to compute churn rate.")
        return

    kpi_col, chart_col = st.columns([1, 2])
    with kpi_col:
        st.metric(label="Churn Rate", value=f"{last_val:.2f}%", delta=f"{growth_pct:.2f}%")

    with chart_col:
        st.altair_chart(chart.properties(height=150), use_container_width=True)


import pandas as pd
import altair as alt
import streamlit as st

##################
# CUSTOMER DATA
##################

@st.cache_data
def prepare_aggregated_data(df: pd.DataFrame, frequency: str, metric: str):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Type'] = df['Type'].fillna("Unknown")

    if frequency == 'weekly':
        df['FreqPeriod'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
    elif frequency == 'monthly':
        df['FreqPeriod'] = df['Date'].dt.to_period('M').apply(lambda r: r.start_time)
    else:
        raise ValueError("frequency must be 'weekly' or 'monthly'")

    latest_periods = df['FreqPeriod'].drop_duplicates().nlargest(5)
    df = df[df['FreqPeriod'].isin(latest_periods)]

    if metric == "Sales (Total)":
        agg_df = df.groupby('Type', as_index=False)['Total Amount'].sum().rename(columns={'Total Amount':'Value'})
    elif metric == "Number of Customers":
        agg_df = df.groupby('Type', as_index=False)['Customer Name'].nunique().rename(columns={'Customer Name':'Value'})
    elif metric == "Sales per Customer":
        temp = df.groupby('Type', as_index=False).agg(
            Total_Sales=('Total Amount','sum'),
            Num_Customers=('Customer Name','nunique')
        )
        temp['Value'] = temp['Total_Sales']/temp['Num_Customers']
        agg_df = temp[['Type','Value']]
    else:
        raise ValueError("Invalid metric")

    return agg_df.sort_values('Value', ascending=False)

def display_comparative_chart(df: pd.DataFrame, frequency: str):
    theme_base = st.get_option("theme.base")
    text_color = "black" if theme_base == "dark" else "white"
    n_types = len(df['Type'].dropna().unique())

    # INLINE RADIO + SHOW ALL
    col_radio, col_checkbox = st.columns([0.7, 0.3])
    with col_radio:
        metric_key = f"metric_type_{frequency}_{hash(df.shape)}"
        metric = st.radio(
            "Metric:",
            ["Sales (Total)", "Number of Customers", "Sales per Customer"],
            horizontal=True,
            key=metric_key
        )
    with col_checkbox:
        show_all = False
        if n_types > 10:
            show_key = f"show_all_type_{frequency}_{hash(df.shape)}"
            show_all = st.checkbox("Show all", key=show_key)

    st.markdown(f"#### Customer Type (Aggregated over Last 5 {frequency.capitalize()}s)")

    agg_df = prepare_aggregated_data(df, frequency, metric)
    n_types = len(agg_df)

    if show_all or n_types <= 10:
        subset_df = agg_df
    else:
        top_df = agg_df.head(10).copy()
        others_sum = agg_df['Value'].iloc[10:].sum()
        if others_sum > 0:
            top_df.loc[len(top_df)] = ['Others', others_sum]
        subset_df = top_df

    order = subset_df['Type'].tolist()
    if 'Others' in order:
        order.remove('Others')
        order.append('Others')

    chart_height = 60*len(subset_df)

    bar = (
        alt.Chart(subset_df, height=chart_height)
        .mark_bar(size=16)
        .encode(
            x=alt.X('Value:Q', title=metric),
            y=alt.Y('Type:N', sort=order, title=None),
            color=alt.Color('Type:N', legend=None),
            tooltip=[alt.Tooltip('Type:N', title='Type'), alt.Tooltip('Value:Q', format=',.0f', title=metric)]
        )
    )

    text = (
        alt.Chart(subset_df, height=chart_height)
        .mark_text(baseline='middle', dx=5, align='left', color=text_color)
        .encode(
            x='Value:Q',
            y=alt.Y('Type:N', sort=order),
            text=alt.Text('Value:Q', format=',.0f')
        )
    )

    st.altair_chart(bar + text, use_container_width=True)

####################
# LOCATION DATA
####################

@st.cache_data
def prepare_aggregated_data_location(df: pd.DataFrame, frequency: str, metric: str):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    def clean_location(loc):
        if pd.isna(loc) or str(loc).strip() == "":
            return "Unknown"
        parts = [p.strip() for p in str(loc).split(',')]
        return parts[-1] if len(parts) > 1 else parts[0]

    df['Clean_Location'] = df['Location'].apply(clean_location)

    if frequency == 'weekly':
        df['FreqPeriod'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
    elif frequency == 'monthly':
        df['FreqPeriod'] = df['Date'].dt.to_period('M').apply(lambda r: r.start_time)
    else:
        raise ValueError("frequency must be 'weekly' or 'monthly'")

    latest_periods = df['FreqPeriod'].drop_duplicates().nlargest(5)
    df = df[df['FreqPeriod'].isin(latest_periods)]

    if metric == "Sales (Total)":
        agg_df = df.groupby('Clean_Location', as_index=False)['Total Amount'].sum().rename(columns={'Total Amount':'Value'})
    elif metric == "Number of Customers":
        agg_df = df.groupby('Clean_Location', as_index=False)['Customer Name'].nunique().rename(columns={'Customer Name':'Value'})
    elif metric == "Sales per Customer":
        temp = df.groupby('Clean_Location', as_index=False).agg(
            Total_Sales=('Total Amount','sum'),
            Num_Customers=('Customer Name','nunique')
        )
        temp['Value'] = temp['Total_Sales']/temp['Num_Customers']
        agg_df = temp[['Clean_Location','Value']]
    else:
        raise ValueError("Invalid metric")

    return agg_df.sort_values('Value', ascending=False)

def display_comparative_chart_location(df: pd.DataFrame, frequency: str):
    theme_base = st.get_option("theme.base")
    text_color = "black" if theme_base == "dark" else "white"
    n_locs = len(df['Location'].dropna().unique())

    # INLINE RADIO + SHOW ALL
    col_radio, col_checkbox = st.columns([0.7, 0.3])
    with col_radio:
        metric_key = f"metric_loc_{frequency}_{hash(df.shape)}"
        metric = st.radio(
            "Metric:",
            ["Sales (Total)", "Number of Customers", "Sales per Customer"],
            horizontal=True,
            key=metric_key
        )
    with col_checkbox:
        show_all = False
        if n_locs > 10:
            show_key = f"show_all_loc_{frequency}_{hash(df.shape)}"
            show_all = st.checkbox("Show all", key=show_key)

    st.markdown(f"#### Location (Aggregated over Last 5 {frequency.capitalize()}s)")

    agg_df = prepare_aggregated_data_location(df, frequency, metric)
    n_locs = len(agg_df)

    if show_all or n_locs <= 10:
        subset_df = agg_df
    else:
        top_df = agg_df.head(10).copy()
        others_sum = agg_df['Value'].iloc[10:].sum()
        if others_sum > 0:
            top_df.loc[len(top_df)] = ['Others', others_sum]
        subset_df = top_df

    order = subset_df['Clean_Location'].tolist()
    if 'Others' in order:
        order.remove('Others')
        order.append('Others')

    chart_height = 40*len(subset_df)

    bar = (
        alt.Chart(subset_df, height=chart_height)
        .mark_bar(size=16)
        .encode(
            x=alt.X('Value:Q', title=metric),
            y=alt.Y('Clean_Location:N', sort=order, title=None),
            color=alt.Color('Clean_Location:N', legend=None),
            tooltip=[alt.Tooltip('Clean_Location:N', title='Location'), alt.Tooltip('Value:Q', format=',.0f', title=metric)]
        )
    )

    text = (
        alt.Chart(subset_df, height=chart_height)
        .mark_text(baseline='middle', dx=5, align='left', color=text_color)
        .encode(
            x='Value:Q',
            y=alt.Y('Clean_Location:N', sort=order),
            text=alt.Text('Value:Q', format=',.0f')
        )
    )

    st.altair_chart(bar + text, use_container_width=True)

##################
# OVERVIEW CHARTS
##################

@st.cache_data
def prepare_overview_aggregated_data(df: pd.DataFrame, metric: str):
    df = df.copy()
    df['Type'] = df['Type'].fillna("Unknown")

    # Customer Type
    if metric == "Sales (Total)":
        type_df = df.groupby('Type', as_index=False)['Total Amount'].sum().rename(columns={'Total Amount':'Value'})
    elif metric == "Number of Customers":
        type_df = df.groupby('Type', as_index=False)['Customer Name'].nunique().rename(columns={'Customer Name':'Value'})
    elif metric == "Sales per Customer":
        temp = df.groupby('Type', as_index=False).agg(
            Total_Sales=('Total Amount','sum'),
            Num_Customers=('Customer Name','nunique')
        )
        temp['Value'] = temp['Total_Sales']/temp['Num_Customers']
        type_df = temp[['Type','Value']]
    else:
        raise ValueError("Invalid metric")

    # Location
    def clean_location(loc):
        if pd.isna(loc) or str(loc).strip() == "":
            return "Unknown"
        parts = [p.strip() for p in str(loc).split(',')]
        return parts[-1] if len(parts) > 1 else parts[0]

    df['Clean_Location'] = df['Location'].apply(clean_location)

    if metric == "Sales (Total)":
        loc_df = df.groupby('Clean_Location', as_index=False)['Total Amount'].sum().rename(columns={'Total Amount':'Value'})
    elif metric == "Number of Customers":
        loc_df = df.groupby('Clean_Location', as_index=False)['Customer Name'].nunique().rename(columns={'Customer Name':'Value'})
    elif metric == "Sales per Customer":
        temp = df.groupby('Clean_Location', as_index=False).agg(
            Total_Sales=('Total Amount','sum'),
            Num_Customers=('Customer Name','nunique')
        )
        temp['Value'] = temp['Total_Sales']/temp['Num_Customers']
        loc_df = temp[['Clean_Location','Value']]
    else:
        raise ValueError("Invalid metric")

    return type_df.sort_values('Value', ascending=False), loc_df.sort_values('Value', ascending=False)


def display_overview_charts(df: pd.DataFrame):
    theme_base = st.get_option("theme.base")
    text_color = "black" if theme_base == "dark" else "white"

    # INLINE METRIC + SHOW ALL handled per chart
    metric_key = f"overview_metric_{hash(df.shape)}"
    metric = st.radio(
        "Metric:",
        ["Sales (Total)", "Number of Customers", "Sales per Customer"],
        horizontal=True,
        key=metric_key
    )

    type_df, loc_df = prepare_overview_aggregated_data(df, metric)

    col1, col2 = st.columns(2)

    # Customer Type Chart
    with col1:
        st.markdown("#### Customer Type")
        n_types = len(type_df)
        show_all_type = False
        if n_types > 10:
            show_key = f"overview_show_all_type_{hash(df.shape)}"
            show_all_type = st.checkbox("Show all", key=show_key)

        if show_all_type or n_types <= 10:
            subset = type_df
        else:
            top = type_df.head(10).copy()
            others_sum = type_df['Value'].iloc[10:].sum()
            if others_sum > 0:
                top.loc[len(top)] = ['Others', others_sum]
            subset = top

        order = subset['Type'].tolist()
        if 'Others' in order:
            order.remove('Others')
            order.append('Others')

        chart_height = 60*len(subset)
        bar = (
            alt.Chart(subset, height=chart_height)
            .mark_bar(size=16)
            .encode(
                x=alt.X('Value:Q', title=metric),
                y=alt.Y('Type:N', sort=order, title=None),
                color=alt.Color('Type:N', legend=None),
                tooltip=[alt.Tooltip('Type:N', title='Type'), alt.Tooltip('Value:Q', format=',.0f', title=metric)]
            )
        )
        text = (
            alt.Chart(subset, height=chart_height)
            .mark_text(baseline='middle', dx=5, align='left', color=text_color)
            .encode(
                x='Value:Q',
                y=alt.Y('Type:N', sort=order),
                text=alt.Text('Value:Q', format=',.0f')
            )
        )
        st.altair_chart(bar + text, use_container_width=True)

    # Location Chart
    with col2:
        st.markdown("#### Location")
        n_locs = len(loc_df)
        show_all_loc = False
        if n_locs > 10:
            show_key = f"overview_show_all_loc_{hash(df.shape)}"
            show_all_loc = st.checkbox("Show all", key=show_key)

        if show_all_loc or n_locs <= 10:
            subset = loc_df
        else:
            top = loc_df.head(10).copy()
            others_sum = loc_df['Value'].iloc[10:].sum()
            if others_sum > 0:
                top.loc[len(top)] = ['Others', others_sum]
            subset = top

        order = subset['Clean_Location'].tolist()
        if 'Others' in order:
            order.remove('Others')
            order.append('Others')

        chart_height = 40*len(subset)
        bar = (
            alt.Chart(subset, height=chart_height)
            .mark_bar(size=16)
            .encode(
                x=alt.X('Value:Q', title=metric),
                y=alt.Y('Clean_Location:N', sort=order, title=None),
                color=alt.Color('Clean_Location:N', legend=None),
                tooltip=[alt.Tooltip('Clean_Location:N', title='Location'), alt.Tooltip('Value:Q', format=',.0f', title=metric)]
            )
        )
        text = (
            alt.Chart(subset, height=chart_height)
            .mark_text(baseline='middle', dx=5, align='left', color=text_color)
            .encode(
                x='Value:Q',
                y=alt.Y('Clean_Location:N', sort=order),
                text=alt.Text('Value:Q', format=',.0f')
            )
        )
        st.altair_chart(bar + text, use_container_width=True)
