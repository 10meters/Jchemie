import pandas as pd
import math
import re
from rapidfuzz import process, fuzz
from io import BytesIO
import streamlit as st

# -------------------------------
# Helper Functions
# -------------------------------

def normalize(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()

def read_session_csv(file_path):
    """
    Reads a CSV from session memory (BytesIO) if it exists.
    Otherwise returns empty DataFrame.
    """
    if 'session_files' in st.session_state and file_path in st.session_state.session_files:
        buf = st.session_state.session_files[file_path]
        buf.seek(0)
        return pd.read_csv(buf)
    return pd.DataFrame()

def read_excel_file(file_path_or_obj, **kwargs):
    """
    Reads an Excel file from file-like object or path.
    Preserves engine usage as in original code (xlrd).
    """
    if hasattr(file_path_or_obj, "read"):
        buf = BytesIO(file_path_or_obj.read())
        return pd.read_excel(buf, engine="xlrd", **kwargs)
    else:
        return pd.read_excel(file_path_or_obj, engine="xlrd", **kwargs)

# -------------------------------
# Core Conversion Functions
# -------------------------------

def convert_sales_file_to_df(path):

    if hasattr(path, "read"):
        data = BytesIO(path.read())
        df = pd.read_excel(data, header=None)
    else:
        df = pd.read_excel(path, header=None)

    df_raw = df

    def row_matches(row):
        cells = [normalize(v) for v in row[:20]]
        if cells[0] != "Date" or cells[1] != "SO  #" or cells[2] != "Customer Name":
            return False
        i = 3
        while i < len(cells) and cells[i] == "":
            i += 1
        return i < len(cells) and cells[i] == "Total Amount"

    matches = df_raw.index[df_raw.apply(row_matches, axis=1)].tolist()
    if not matches:
        raise ValueError("Header row not found")
    header_row = matches[0]

    df = read_excel_file(path, header=header_row)
    df = df[[c for c in df.columns if normalize(c) != ""]]
    df = df[["Date", "SO  #", "Customer Name", "Total Amount"]]

    all_nan_idx = df.isna().all(axis=1).to_numpy().nonzero()[0]
    if all_nan_idx.size > 0:
        df = df.iloc[:all_nan_idx[0]]

    df['Customer Name'] = df['Customer Name'].str.replace(
        r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
    ).str.strip()

    customers = read_session_csv("data/CUSTOMERS_LIST.csv")
    if not customers.empty:
        customers["Business Name"] = customers["Business Name"].str.upper()

        def fuzzy_match(name):
            match, score, _ = process.extractOne(name, customers["Business Name"], scorer=fuzz.ratio)
            return match if score >= 80 else None

        df["Matched Name"] = df["Customer Name"].apply(fuzzy_match)
        df = pd.merge(df, customers, left_on="Matched Name", right_on="Business Name", how="left") \
               .drop(columns=["Business Name", "Matched Name"])
    return df

def convert_collections_to_df(file_path):
    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, header=None)
    else:
        df = pd.read_excel(file_path, header=None)

    df_raw = df

    required = {'Date', 'Type', 'OR #', 'Customer Name', 'PM', 'Amount', 'Check Amount'}

    for i, row in df_raw.iterrows():
        clean_row = [str(x).strip() for x in row]
        if required.issubset(clean_row):
            df_raw.columns = clean_row
            df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
            df_raw = df_raw.iloc[i + 1:]
            df_raw = df_raw.dropna(subset=['OR #', 'Amount'])
            df_raw['Customer Name'] = df_raw['Customer Name'].str.replace(
                r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
            ).str.strip()
            df_raw = df_raw[["Date", "Type", "OR #", "Customer Name", "PM", "Check Amount"]]
            return df_raw.dropna(subset=['Type', 'OR #'])
    raise ValueError("Target headers not found in file")

def convert_receivables_to_df(file_path):
    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, header=None)
    else:
        df = pd.read_excel(file_path, header=None)
    
    df_raw = df

    required = {'Date', 'Type', 'SI #', 'Customer Name', 'Amount Due', 'Paid Amount', 'Balance'}

    for i, row in df_raw.iterrows():
        clean_row = [str(x).strip() for x in row]
        if required.issubset(clean_row):
            df_raw.columns = clean_row
            df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
            df_raw = df_raw.iloc[i + 1:]
            df_raw['Customer Name'] = df_raw['Customer Name'].str.replace(
                r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
            ).str.strip()
            df_raw = df_raw[["Date", "Type", "SI #", "Customer Name", "Amount Due", "Paid Amount", "Balance"]]
            return df_raw.dropna(subset=['SI #', 'Customer Name'])
    raise ValueError("Target headers not found in file")

def convert_summary_to_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=None, header=None)
    else:
        df = pd.read_excel(file_path, sheet_name=None, header=None)

    # Read ALL sheets (sheet_name=None). 
    # Use header=None to manually find the correct header row later.
    all_sheets = df
    
    processed_dfs = []

    for sheet_name, raw_df in all_sheets.items():
        header_idx = None
        for idx, row in raw_df.iterrows():
            if "Product Code" in row.astype(str).values:
                header_idx = idx
                break
        if header_idx is None:
            continue
        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = raw_df.iloc[header_idx]
        df = df.dropna(subset=['Product Code'])
        df = df[~df['Product Code'].astype(str).str.contains('GRAND TOTAL', case=False, na=False)]
        df['Month-Year'] = pd.to_datetime(sheet_name)
        processed_dfs.append(df)

    return pd.concat(processed_dfs, ignore_index=True)

def convert_customer_masterlist_to_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=None, header=None)
    else:
        df = pd.read_excel(file_path, sheet_name=None, header=None)

    # Read ALL sheets, no header initially
    all_sheets = df
    
    processed_dfs = []

    for sheet_name, raw_df in all_sheets.items():
        customer_type = raw_df.iloc[1, 0] if raw_df.shape[0] > 1 else "Unknown"
        header_idx = None
        for idx, row in raw_df.iterrows():
            if "Customer's Name" in row.astype(str).values:
                header_idx = idx
                break
        if header_idx is None:
            continue
        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = raw_df.iloc[header_idx]
        df = df.dropna(subset=["Customer's Name"])
        df['Account'] = sheet_name
        df['Type'] = customer_type
        processed_dfs.append(df)

    return pd.concat(processed_dfs, ignore_index=True)

def process_raw_materials_stock_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=0, header=None)
    else:
        df = pd.read_excel(file_path, sheet_name=0, header=None)

    # Read ONLY the first sheet
    raw_df = df
    
    # 1. Extract "Inventory Date" from metadata
    inventory_date = None

    for idx, row in raw_df.iloc[:20].iterrows():
        row_text = " ".join([str(val) for val in row if pd.notna(val)])
        if "Running Inventory as of" in row_text:
            match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_text)
            if match:
                inventory_date = pd.to_datetime(match.group(1))
            break

    if inventory_date is None:
        inventory_date = pd.to_datetime('today').normalize()

    header_idx = None
    key_col = "Product Code"

    for idx, row in raw_df.iterrows():
        row_str = row.astype(str).values
        if "Product Code" in row_str:
            header_idx = idx
            key_col = "Product Code"
            break
        elif "ITEM" in row_str:
            header_idx = idx
            key_col = "ITEM"
            break

    if header_idx is None:
        return pd.DataFrame()

    df = raw_df.iloc[header_idx + 1:].copy()
    df.columns = raw_df.iloc[header_idx]
    df = df.dropna(subset=[key_col])
    df = df[~df[key_col].astype(str).str.contains('GRAND TOTAL', case=False, na=False)]

    check_col = 'Unit' if 'Unit' in df.columns else 'UNIT'
    if check_col in df.columns:
        is_cat_header = df[check_col].isna()
        df['Category'] = df[key_col].where(is_cat_header)
        df['Category'] = df['Category'].ffill().fillna('OTHERS')
        df = df[~is_cat_header]
    else:
        df['Category'] = 'OTHERS'

    df['Inventory Date'] = inventory_date
    return df
