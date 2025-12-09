import pandas as pd
import plotly.express as px

# --- 1. ROBUST DATA LOADING ---
def find_header_and_read(file, keyword):
    """Scans file for a keyword to find the correct header row."""
    file.seek(0)
    # Try Excel
    try:
        xl = pd.ExcelFile(file)
        for sheet in xl.sheet_names:
            df_preview = pd.read_excel(file, sheet_name=sheet, header=None, nrows=20)
            for i, row in df_preview.iterrows():
                if row.astype(str).str.contains(keyword, case=False).any():
                    file.seek(0)
                    return pd.read_excel(file, sheet_name=sheet, header=i)
    except:
        pass 
    # Try CSV
    try:
        file.seek(0)
        df_preview = pd.read_csv(file, header=None, nrows=20)
        for i, row in df_preview.iterrows():
            if row.astype(str).str.contains(keyword, case=False).any():
                file.seek(0)
                return pd.read_csv(file, header=i)
    except:
        pass
    return pd.DataFrame() 

def clean_data(stock_file, po_files):
    # A. LOAD STOCK
    df_stock = find_header_and_read(stock_file, "ON HAND STOCK")
    
    # Fail-safe: Create columns if missing
    for col in ['Product Description', 'ON HAND STOCK', 'Total_Value', 'Clean_Price']:
        if col not in df_stock.columns:
            df_stock[col] = 0 if col != 'Product Description' else 'Unknown'
            
    # Clean Price
    if 'UNIT PRICE/Kg' in df_stock.columns:
        df_stock['Clean_Price'] = df_stock['UNIT PRICE/Kg'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df_stock['Clean_Price'] = pd.to_numeric(df_stock['Clean_Price'], errors='coerce').fillna(0)
        df_stock['Total_Value'] = df_stock['ON HAND STOCK'] * df_stock['Clean_Price']
    else:
        df_stock['Total_Value'] = 0

    # B. LOAD PO LOGS
    po_frames = []
    for f in po_files:
        df = find_header_and_read(f, "RAWMATERIALS")
        if not df.empty: po_frames.append(df)
    
    if po_frames:
        df_po = pd.concat(po_frames, ignore_index=True)
        # Clean Dates
        for col in ['DATE REQUEST', 'DELIVERY DATE']:
            if col in df_po.columns: 
                df_po.rename(columns={col: col.replace('\n', ' ')}, inplace=True)
        
        if 'DATE REQUEST' in df_po.columns and 'DELIVERY DATE' in df_po.columns:
            df_po['DATE REQUEST'] = pd.to_datetime(df_po['DATE REQUEST'], errors='coerce')
            df_po['DELIVERY DATE'] = pd.to_datetime(df_po['DELIVERY DATE'], errors='coerce')
            df_po['Lead_Time'] = (df_po['DELIVERY DATE'] - df_po['DATE REQUEST']).dt.days
        else:
            df_po['Lead_Time'] = 0

        # Clean Amount
        target = 'AMMOUNT' if 'AMMOUNT' in df_po.columns else ('AMOUNT' if 'AMOUNT' in df_po.columns else None)
        if target:
             df_po['Clean_Amount'] = df_po[target].astype(str).str.replace(r'[^\d.]', '', regex=True)
             df_po['Clean_Amount'] = pd.to_numeric(df_po['Clean_Amount'], errors='coerce').fillna(0)
        else:
             df_po['Clean_Amount'] = 0
             
        if 'STATUS' not in df_po.columns: df_po['STATUS'] = 'Unknown'
    else:
        df_po = pd.DataFrame(columns=['Clean_Amount', 'STATUS', 'Lead_Time', 'SUPPLIER', 'RAWMATERIALS'])

    # C. CLASSIFY ITEMS (Logic: Fast vs Slow)
    if not df_po.empty and 'RAWMATERIALS' in df_po.columns:
        demand = df_po['RAWMATERIALS'].value_counts().reset_index()
        demand.columns = ['Product Description', 'Order_Count']
        
        if 'Product Description' in df_stock.columns:
            df_stock = pd.merge(df_stock, demand, on='Product Description', how='left')
            df_stock['Order_Count'] = df_stock['Order_Count'].fillna(0)
            
            # Logic: If ordered 2+ times, Safety Stock is 50. Else 10.
            def get_status(row):
                thresh = 50 if row['Order_Count'] >= 2 else 10
                if row['ON HAND STOCK'] <= thresh: return "Restock Needed 🔴"
                if row['Order_Count'] == 0 and row['ON HAND STOCK'] > 0: return "Slow Moving 🐢"
                return "Healthy 🟢"

            df_stock['Status'] = df_stock.apply(get_status, axis=1)
            df_stock['Safety_Threshold'] = df_stock['Order_Count'].apply(lambda x: 50 if x >= 2 else 10)
        else:
             df_stock['Status'] = "Unknown"
    else:
        df_stock['Status'] = "Unknown"

    return df_stock, df_po

# --- 2. CHART FUNCTIONS ---
def get_stock_bar(df):
    if df.empty or 'Total_Value' not in df.columns: return None
    df_top = df.sort_values('Total_Value', ascending=False).head(10)
    fig = px.bar(
        df_top, 
        x='Total_Value', 
        y='Product Description', 
        orientation='h', 
        title="Top 10 High Value Items", 
        text_auto='.2s', 
        color='Total_Value'
    )
    fig.update_layout(yaxis_title="", xaxis_title="PHP")
    return fig

def get_lead_bar(df_po):
    if df_po.empty or 'SUPPLIER' not in df_po.columns or 'Lead_Time' not in df_po.columns: return None
    valid = df_po[df_po['Lead_Time'] > 0]
    if valid.empty: return None
    avg = valid.groupby('SUPPLIER')['Lead_Time'].mean().sort_values().head(10)
    fig = px.bar(
        avg, 
        orientation='h', 
        title="Avg Delivery Time (Days)", 
        text_auto='.0f'
    )
    fig.update_layout(yaxis_title="", xaxis_title="Days")
    return fig