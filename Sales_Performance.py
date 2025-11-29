import streamlit as st
import pandas as pd
import os
import project3_utility as util


st.set_page_config(page_title="Sales Overview", page_icon="🏠")
st.set_page_config(layout="wide")

# Change working directory to the folder where this script is located
cwd = os.path.dirname(os.path.abspath(__file__))
os.chdir(cwd)

# Make wide
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide",  # makes the app span the full width
    initial_sidebar_state="expanded"
)

# TITLE + Frequency dropdown
title_col, freq_col = st.columns([3, 1])

with title_col:
    st.title("Sales Performance Dashboard")


# Load data
df = pd.read_csv("data/SALES ORDER.csv").dropna(axis=1, how='all')
df = util.clean_data(df)


r1c1, gap, r1c2 = st.columns([2, 0.1, 2])

with r1c1:
    # Show monthly sales volume
    volume, breakdown = st.tabs(["Yearly Volume", "Yearly Customer Breakdown"])
    with volume:
        st.subheader("Overall Sales Volume")
        monthly_sales = util.compute_monthly_sales(df)
        monthly_sales_linechart = util.show_monthly_sales_volume(monthly_sales)
        st.altair_chart(monthly_sales_linechart, use_container_width=True)
    
    with breakdown:
        util.display_overview_charts(df)
    
    st.subheader("Customer Loyalty KPIs")
    # Create 3 KPI columns
    kpi1, kpi2, kpi3 = st.columns([1,1,3])

    with kpi1:
        active_count = util.count_active_customers(df)
        st.markdown(f"""
        <b>Active Customers</b> 
        <h2 style='margin:0; line-height:0.1'>{active_count}</h2>
        <p style='margin:0; color:gray; line-height:1'>customers</p>
        <br/>
        """, unsafe_allow_html=True)


    with kpi2:
        mean_reorder_time = util.reorder_time_stats(df)
        q1 = mean_reorder_time['q1']
        q3 = mean_reorder_time['q3']
        st.markdown(f"""
        <b>Reorder Time</b>  
        <h2 style='margin:0; line-height:0.1''>{q1:.0f} - {q3:.0f}</h2>
        <p style='margin:0; color:gray; line-height:1'>days</p>
        <br/>
        """, unsafe_allow_html=True)

    with kpi3:
        avg_value_transaction = util.show_median_transaction_value(df)
        st.markdown(f"""
        <b>Median Transaction Value</b>  
        <h2 style='margin:0; line-height:0.1''>₱ {avg_value_transaction:,.2f}</h2>
        <p style='margin:0; color:gray; line-height:1'>Pesos</p>
        <br/>
        """, unsafe_allow_html=True)

    util.show_churn_bento(df)

with r1c2:
    weekly, monthly = st.tabs(["Weekly Sales", "Monthly Sales"])

    with weekly:
        st.subheader("Weekly Overview")
        util.show_sales_bento(df, frequency="weekly")
        util.show_customers_bento(df, frequency="weekly")
        customer, region = st.tabs(["By Customer", "By Region"])
    
        with customer:
            util.display_comparative_chart(df, frequency="weekly")
        with region:
            util.display_comparative_chart_location(df, frequency="weekly")
            

    with monthly:
        st.subheader("Monthly Overview")
        util.show_sales_bento(df, frequency="monthly")
        util.show_customers_bento(df, frequency="monthly")

        customer, region, custom = st.tabs(["By Customer", "By Region", "Year Overview"])
    
        with customer:
            util.display_comparative_chart(df, frequency="monthly")
        with region:
            util.display_comparative_chart_location(df, frequency="monthly")
