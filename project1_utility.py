import pandas as pd
import plotly.express as px
import datetime

def clean_data(file):
    """Loads and processes Customer/Sales data."""
    file.seek(0)
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception:
        return pd.DataFrame()

    # 1. Normalize Columns (Standardize variations)
    df.columns = df.columns.str.strip().str.upper()
    
    # Map common column names to standard internal names
    col_map = {
        'CUSTOMER NAME': 'CUSTOMER', 'CLIENT': 'CUSTOMER', 'CLIENT NAME': 'CUSTOMER',
        'TRANSACTION DATE': 'DATE', 'ORDER DATE': 'DATE', 'INVOICE DATE': 'DATE',
        'AMOUNT': 'AMOUNT', 'TOTAL': 'AMOUNT', 'SALES': 'AMOUNT', 'BALANCE': 'AMOUNT',
        'STATUS': 'STATUS', 'PAYMENT STATUS': 'STATUS', 'PAYMENT': 'STATUS'
    }
    df = df.rename(columns=col_map)

    # 2. Ensure required columns exist
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    else:
        df['DATE'] = datetime.datetime.now() # Fallback

    if 'AMOUNT' in df.columns:
        # Clean currency symbols
        df['AMOUNT'] = df['AMOUNT'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df['AMOUNT'] = pd.to_numeric(df['AMOUNT'], errors='coerce').fillna(0)
    else:
        df['AMOUNT'] = 0

    if 'STATUS' not in df.columns:
        df['STATUS'] = 'Unknown'

    if 'CUSTOMER' not in df.columns:
        df['CUSTOMER'] = 'Unknown'

    # 3. CALCULATE METRICS
    # Recency (Days since last purchase) to determine Churn Risk
    if not df.empty and 'DATE' in df.columns and 'CUSTOMER' in df.columns:
        now = datetime.datetime.now()
        recency = df.groupby('CUSTOMER')['DATE'].max().reset_index()
        recency['Days_Since_Last'] = (now - recency['DATE']).dt.days
        
        # Merge back to main df
        df = pd.merge(df, recency[['CUSTOMER', 'Days_Since_Last']], on='CUSTOMER', how='left')
        
        # Logic: >90 Days = High Risk, >60 Days = At Risk
        def get_risk(days):
            if days > 90: return "High Risk 🔴"
            if days > 60: return "At Risk 🟡"
            return "Active 🟢"
            
        df['Risk_Status'] = df['Days_Since_Last'].apply(get_risk)
    else:
        df['Risk_Status'] = "Unknown"

    return df

def get_churn_chart(df):
    if df.empty or 'Risk_Status' not in df.columns: return None
    
    # Count customers by risk level
    risk_counts = df.groupby('Risk_Status')['CUSTOMER'].nunique().reset_index()
    
    if risk_counts.empty: return None

    fig = px.pie(
        risk_counts, 
        names='Risk_Status', 
        values='CUSTOMER', 
        title="Customer Retention Health", 
        color='Risk_Status',
        color_discrete_map={'High Risk 🔴':'#FF4B4B', 'At Risk 🟡':'#FFAA00', 'Active 🟢':'#00CC96', 'Unknown':'grey'},
        hole=0.4
    )
    return fig

def get_collection_table(df):
    if df.empty or 'STATUS' not in df.columns: return None
    
    # Filter for unpaid statuses
    unpaid = df[df['STATUS'].str.contains('PENDING|UNPAID|DUE|OVERDUE', case=False, na=False)]
    
    if unpaid.empty: return None
    
    # Summarize debt by customer
    summary = unpaid.groupby('CUSTOMER')['AMOUNT'].sum().reset_index().sort_values('AMOUNT', ascending=False)
    return summary