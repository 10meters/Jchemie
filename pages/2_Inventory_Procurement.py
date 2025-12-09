import streamlit as st
import pandas as pd
import altair as alt

# Set page config
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Callback function to check password
def check_password():
    if st.session_state.pw_input == st.secrets["APP_PASSWORD"]:
        st.session_state.logged_in = True
    else:
        st.session_state.logged_in = False
        st.error("Incorrect password")

# Show login only if not logged in
if not st.session_state.logged_in:
    st.text_input(
        "Enter password:",
        type="password",
        key="pw_input",
        on_change=check_password
    )
    if not st.session_state.logged_in:
        st.stop()

@st.cache_data
def load_data():
    # Load data from the 'data' folder
    try:
        stock_df = pd.read_csv('data/STOCK LEVELS.csv')
        summary_df = pd.read_csv('data/SUMMARY PER ITEM.csv')
    except FileNotFoundError:
        st.error("Data files not found in 'data/' directory. Please ensure 'data/STOCK LEVELS.csv' and 'data/SUMMARY PER ITEM.csv' exist.")
        return pd.DataFrame(), pd.DataFrame()
    
    # 1. CLEANING STRING COLUMNS
    str_cols_stock = ['Product Code', 'Product Description', 'Category', 'Unit']
    for col in str_cols_stock:
        if col in stock_df.columns:
            stock_df[col] = stock_df[col].astype(str).str.strip()

    str_cols_summary = ['Product Code', 'Item Description', 'Unit', 'Month-Year']
    for col in str_cols_summary:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].astype(str).str.strip()

    # 2. DATE CONVERSION
    stock_df['Inventory Date'] = pd.to_datetime(stock_df['Inventory Date'], errors='coerce')
    summary_df['Month-Year'] = pd.to_datetime(summary_df['Month-Year'], errors='coerce')

    # 3. CALCULATE ESTIMATED UNIT COST & SALES
    summary_df['Calculated_Unit_Cost'] = summary_df.apply(
        lambda row: row['Cost'] / row['Qty'] if row['Qty'] != 0 else 0, axis=1
    )
    
    price_list = summary_df.groupby('Product Code')['Calculated_Unit_Cost'].mean().reset_index()
    stock_df = pd.merge(stock_df, price_list, on='Product Code', how='left')
    stock_df['Total Stock Value'] = stock_df['Qty'] * stock_df['Calculated_Unit_Cost']
    
    # 4. ENRICH SUMMARY WITH CATEGORY (for Aggregated View)
    # Create a map of Product Code -> Category from stock_df
    category_map = stock_df[['Product Code', 'Category']].drop_duplicates(subset='Product Code')
    summary_df = pd.merge(summary_df, category_map, on='Product Code', how='left')
    summary_df['Category'] = summary_df['Category'].fillna('Unknown') # Handle items in summary but not in stock list

    return stock_df, summary_df

try:
    stock_df, summary_df = load_data()
    
    if not stock_df.empty:
        # --- SIDEBAR ---
        st.sidebar.title("Configuration")
        
        options = ["Aggregated Sales Dashboard"]
        categories = sorted(stock_df['Category'].dropna().unique().tolist())
        options.extend(categories)
        
        # Helper for item selection
        stock_df['Display_Name'] = "Item: " + stock_df['Product Description'] + " (" + stock_df['Product Code'] + ")"
        item_options = sorted(stock_df['Display_Name'].unique().tolist())
        options.extend(item_options)
        
        selected_option = st.selectbox("Select View:", options)

        # --- MAIN LOGIC ---

        # 1. AGGREGATED VIEW (SALES FOCUSED)
        if selected_option == "Aggregated Sales Dashboard":
            st.title("📈 Executive Sales Dashboard")
            
            # --- DATE FILTER ---
            # Extract unique months formatted as YYYY-MM
            month_list = sorted(summary_df['Month-Year'].dt.strftime('%Y-%m').unique().tolist())
            month_options = ["All Months"] + month_list
            
            col_filter, col_empty = st.columns([1, 3])
            with col_filter:
                selected_month_str = st.selectbox("Focus on Month:", month_options)
            
            # Filter Data based on selection
            if selected_month_str != "All Months":
                dashboard_df = summary_df[summary_df['Month-Year'].dt.strftime('%Y-%m') == selected_month_str]
                period_label = f"({selected_month_str})"
            else:
                dashboard_df = summary_df
                period_label = "(All Time)"

            # --- KPIs ---
            total_revenue = dashboard_df['Amount'].sum()
            total_cost = dashboard_df['Cost'].sum()
            total_profit = total_revenue - total_cost
            total_qty_sold = dashboard_df['Qty'].sum()
            profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # KPI Calculations for averages (adjust based on selection)
            num_months = dashboard_df['Month-Year'].nunique()
            avg_revenue = total_revenue / num_months if num_months > 0 else 0
            
            # Find Zero Movers (Items in Stock but NOT in Dashboard DF Sales)
            all_stock_items = set(stock_df['Product Code'].unique())
            sold_items = set(dashboard_df['Product Code'].unique())
            zero_movers_count = len(all_stock_items - sold_items)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric(f"Total Revenue {period_label}", f"${total_revenue:,.2f}")
            kpi2.metric("Gross Profit", f"${total_profit:,.2f}", f"{profit_margin:.1f}% Margin")
            kpi3.metric("Total Units Sold", f"{total_qty_sold:,.0f}")
            kpi4.metric("Zero Mover Items", f"{zero_movers_count}", help="Items in stock that had 0 sales in this period.")

            st.divider()

            # --- MONTHLY TREND (Always show full history for context) ---
            st.subheader("Monthly Sales Trend (Historical Context)")
            
            monthly_trend = summary_df.groupby('Month-Year')[['Amount', 'Cost']].sum().reset_index()
            monthly_trend['Profit'] = monthly_trend['Amount'] - monthly_trend['Cost']
            
            trend_melted = monthly_trend.melt('Month-Year', value_vars=['Amount', 'Profit'], var_name='Metric', value_name='Value')
            
            chart_trend = alt.Chart(trend_melted).mark_line(point=True).encode(
                x='Month-Year',
                y='Value',
                color='Metric',
                tooltip=['Month-Year', 'Metric', 'Value']
            ).interactive()
            
            st.altair_chart(chart_trend, use_container_width=True)

            # --- NEW: ITEM BREAKDOWN FOR SELECTED MONTH ---
            st.subheader(f"📊 Top Sales Contributors (Item Breakdown) {period_label}")
            
            # Aggregate sales by item for the current selection
            breakdown_data = dashboard_df.groupby('Item Description')['Amount'].sum().reset_index()
            
            if not breakdown_data.empty:
                # Show top 20 to avoid overcrowding the chart
                top_breakdown = breakdown_data.nlargest(20, 'Amount')
                
                chart_breakdown = alt.Chart(top_breakdown).mark_bar().encode(
                    x=alt.X('Amount', title='Revenue ($)'),
                    y=alt.Y('Item Description', sort='-x', title=None),
                    tooltip=['Item Description', 'Amount'],
                    color=alt.value('#4c78a8')
                ).interactive()
                
                st.altair_chart(chart_breakdown, use_container_width=True)
            else:
                st.info("No data available for breakdown.")

            st.divider()

            # --- TOP & WORST PERFORMERS ---
            st.subheader(f"🏆 Top vs. Worst Performers (By Volume) {period_label}")
            
            col_top, col_worst = st.columns(2)

            # Aggregate by Item using filtered data
            item_performance = dashboard_df.groupby(['Product Code', 'Item Description'])[['Qty', 'Amount']].sum().reset_index()
            
            with col_top:
                st.markdown("##### 🚀 Top 10 High Volume Items")
                if not item_performance.empty:
                    top_qty = item_performance.nlargest(10, 'Qty')
                    chart_top_qty = alt.Chart(top_qty).mark_bar().encode(
                        x=alt.X('Qty', title='Units Sold'),
                        y=alt.Y('Item Description', sort='-x', title=None),
                        color=alt.value('green'), 
                        tooltip=['Item Description', 'Qty', 'Amount']
                    ).interactive()
                    st.altair_chart(chart_top_qty, use_container_width=True)
                else:
                    st.info("No sales data.")

            with col_worst:
                st.markdown("##### 🐢 Bottom 10 Low Volume Items (Active)")
                if not item_performance.empty:
                    # Filter for items that had at least some movement (>0) to avoid cluttering with returns or 0s
                    active_items = item_performance[item_performance['Qty'] > 0]
                    slow_movers = active_items.nsmallest(10, 'Qty')
                    
                    chart_slow = alt.Chart(slow_movers).mark_bar().encode(
                        x=alt.X('Qty', title='Units Sold'),
                        y=alt.Y('Item Description', sort='x', title=None), # sort ascending
                        color=alt.value('grey'), 
                        tooltip=['Item Description', 'Qty', 'Amount']
                    ).interactive()
                    st.altair_chart(chart_slow, use_container_width=True)
                else:
                    st.info("No sales data.")

        # 2. CATEGORY VIEW
        elif selected_option in categories:
            category = selected_option
            st.title(f"📂 Category: {category}")
            
            # Filter Data
            cat_stock = stock_df[stock_df['Category'] == category].copy()
            cat_codes = cat_stock['Product Code'].unique()
            cat_summary = summary_df[summary_df['Product Code'].isin(cat_codes)]
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Category Value", f"${cat_stock['Total Stock Value'].sum():,.2f}")
            col2.metric("Category Sales", f"${cat_summary['Amount'].sum():,.2f}")
            col3.metric("Low Stock Items", f"{cat_stock[cat_stock['Qty'] <= cat_stock['Min Level']].shape[0]}")
            
            # --- REPLENISHMENT STATUS (DATA EDITOR WITH PROGRESS BARS) ---
            st.subheader("⚠️ Replenishment Urgency (Sorted by Criticality)")
            
            # Calculate Percentage (Ratio)
            cat_stock['Min Level Safe'] = cat_stock['Min Level'].replace(0, 0.0001) # Avoid div by zero
            cat_stock['Stock Health'] = cat_stock['Qty'] / cat_stock['Min Level Safe']
            
            # Cap the visual ratio at 1.0 (100%) for the progress bar
            cat_stock['Visual_Progress'] = cat_stock['Stock Health'].clip(0, 1)
            
            # Sort: Items with lowest Health (most urgent) at top
            cat_stock_sorted = cat_stock.sort_values(by='Stock Health', ascending=True)
            
            # Select columns for display
            display_df = cat_stock_sorted[['Product Description', 'Qty', 'Min Level', 'Visual_Progress', 'Unit']]
            
            st.data_editor(
                display_df,
                column_config={
                    "Visual_Progress": st.column_config.ProgressColumn(
                        "Stock Status",
                        help="Stock Level vs Minimum Level",
                        format="%.1f%%", 
                        min_value=0,
                        max_value=1,
                    ),
                    "Product Description": st.column_config.TextColumn("Item Name", width="large"),
                    "Qty": st.column_config.NumberColumn("Current Qty"),
                    "Min Level": st.column_config.NumberColumn("Min Required"),
                },
                hide_index=True,
                use_container_width=True,
                disabled=True
            )

            # --- SALES TREND ---
            st.subheader("Category Sales Trend")
            if not cat_summary.empty:
                cat_trend = cat_summary.groupby('Month-Year')['Amount'].sum().reset_index()
                chart_cat_trend = alt.Chart(cat_trend).mark_line(point=True).encode(
                    x='Month-Year',
                    y='Amount',
                    tooltip=['Month-Year', 'Amount']
                ).interactive()
                st.altair_chart(chart_cat_trend, use_container_width=True)

        # 3. ITEM VIEW
        else:
            code_extracted = selected_option.split('(')[-1].strip(')')
            st.title(f"📦 Item: {code_extracted}")
            
            item_stock = stock_df[stock_df['Product Code'] == code_extracted]
            item_summary = summary_df[summary_df['Product Code'] == code_extracted]
            
            if not item_stock.empty:
                item_data = item_stock.iloc[0]
                st.header(item_data['Product Description'])
                
                # Metrics
                c1, c2, c3 = st.columns(3)
                qty = item_data['Qty']
                min_lvl = item_data['Min Level']
                
                c1.metric("Current Stock", f"{qty} {item_data['Unit']}")
                c2.metric("Min Level", f"{min_lvl} {item_data['Unit']}")
                c3.metric("Category", item_data['Category'])
                
                # Stock Status Progress Bar (Single Item)
                st.subheader("Stock Status")
                
                if min_lvl > 0:
                    ratio = qty / min_lvl
                    clamped_ratio = min(max(ratio, 0.0), 1.0)
                    percent_text = f"{ratio:.1%}"
                    
                    # Color logic for label
                    if ratio < 0.5:
                        color = "red"
                        status_msg = "CRITICAL LOW"
                    elif ratio < 1.0:
                        color = "orange"
                        status_msg = "BELOW MIN LEVEL"
                    else:
                        color = "green"
                        status_msg = "HEALTHY"
                        
                    st.markdown(f"**Status:** :{color}[{status_msg}] ({percent_text} of Min Level)")
                    st.progress(clamped_ratio)
                else:
                    st.info("No Minimum Level set for this item.")
                
                # Historical Sales
                if not item_summary.empty:
                    st.subheader("Historical Sales")
                    
                    chart_hist = alt.Chart(item_summary).mark_line(point=True).encode(
                        x='Month-Year',
                        y=alt.Y('Qty', title='Sales Qty'),
                        tooltip=['Month-Year', 'Qty', 'Amount']
                    ).interactive()
                    
                    st.altair_chart(chart_hist, use_container_width=True)
                else:
                    st.warning("No sales history.")

except Exception as e:
    st.error(f"An error occurred: {e}")