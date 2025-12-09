import pandas as pd
import math
import os
from rapidfuzz import process, fuzz
import re
from io import BytesIO

def normalize(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()

def convert_sales_file_to_df(path):
    if hasattr(path, "read"):
        data = BytesIO(path.read())
        df = pd.read_excel(data, header=None, engine="xlrd")
    else:
        df = pd.read_excel(path, header=None, engine="xlrd")

    raw=df

    def row_matches(row):
        cells = [normalize(v) for v in row[:20]]

        if cells[0] != "Date":
            return False
        if cells[1] != "SO  #":
            return False
        if cells[2] != "Customer Name":
            return False

        i = 3
        while i < len(cells) and cells[i] == "":
            i += 1

        if i >= len(cells):
            return False

        return cells[i] == "Total Amount"

    matches = raw.index[raw.apply(row_matches, axis=1)].tolist()
    if not matches:
        raise ValueError("Header row not found")

    header_row = matches[0]

    df = pd.read_excel(path, header=header_row)

    df = df[[c for c in df.columns if normalize(c) != ""]]

    df = df[["Date", "SO  #", "Customer Name", "Total Amount"]]

    all_nan_mask = df.isna().all(axis=1)
    first_nan_idx_list = all_nan_mask.to_numpy().nonzero()[0]

    if first_nan_idx_list.size > 0:
        first_nan_idx = first_nan_idx_list[0]
        df = df.iloc[:first_nan_idx]
    
    # Clean the customer names
    df['Customer Name'] = df['Customer Name'].str.replace(
        r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
    ).str.strip()


    customers = pd.read_csv("data/CUSTOMERS_LIST.csv")
    customers["Business Name"] = customers["Business Name"].str.upper()

    # Fuzzy match function
    def fuzzy_match(name):
        match, score, _ = process.extractOne(name, customers["Business Name"], scorer=fuzz.ratio)
        return match if score >= 80 else None  # adjust threshold as needed

    # Merge using fuzzy matching
    df["Matched Name"] = df["Customer Name"].apply(fuzzy_match)
    df = pd.merge(df, customers, left_on="Matched Name", right_on="Business Name", how="left") \
        .drop(columns=["Business Name", "Matched Name"])
 
    return df


import pandas as pd

def convert_collections_to_df(file_path):
    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, header=None, engine="xlrd")
    else:
        df = pd.read_excel(file_path, header=None, engine="xlrd")

    required = {'Date', 'Type', 'OR #', 'Customer Name', 'PM', 'Amount', 'Check Amount'}

    for i, row in df.iterrows():
        clean_row = [str(x).strip() for x in row]

        if required.issubset(clean_row):
            df.columns = clean_row
            df = df.loc[:, ~df.columns.duplicated()]  # keep first instance only
            df = df.iloc[i + 1:]
            df = df.dropna(subset=['OR #', 'Amount'])

            df['Customer Name'] = df['Customer Name'].str.replace(
                r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
            ).str.strip()

            df = df[["Date", "Type", "OR #", "Customer Name", "PM", "Check Amount"]]

            return df.dropna(subset=['Type', 'OR #'])

    raise ValueError("Target headers not found in file")


def convert_receivables_to_df(file_path):
    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, header=None, engine="xlrd")
    else:
        df = pd.read_excel(file_path, header=None, engine="xlrd")

    required = {'Date', 'Type', 'SI #', 'Customer Name', 'Amount Due', 'Paid Amount', 'Balance'}

    for i, row in df.iterrows():
        clean_row = [str(x).strip() for x in row]

        if required.issubset(clean_row):
            df.columns = clean_row
            df = df.loc[:, ~df.columns.duplicated()]  # keep first instance only
            df = df.iloc[i + 1:]


            df['Customer Name'] = df['Customer Name'].str.replace(
                r'^(?:\s*(?:-+|\*|\d+\s*-\s*)*)|(?:-+\s*)$', '', regex=True
            ).str.strip()

            df = df[["Date", "Type", "SI #", "Customer Name", "Amount Due", "Paid Amount", "Balance"]]
            
            return df.dropna(subset=['SI #', 'Customer Name'])

    raise ValueError("Target headers not found in file")

def convert_summary_to_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=None, header=None, engine="xlrd")
    else:
        df = pd.read_excel(file_path, sheet_name=None, header=None, engine="xlrd")

    # Read ALL sheets (sheet_name=None). 
    # Use header=None to manually find the correct header row later.
    all_sheets = df
    
    processed_dfs = []

    for sheet_name, raw_df in all_sheets.items():
        # 1. Find the header row by looking for "Product Code" in the values
        # We loop through rows until we find the identifier
        header_idx = None
        for idx, row in raw_df.iterrows():
            # Convert row to string to search for key column name
            if "Product Code" in row.astype(str).values:
                header_idx = idx
                break
        
        # If this sheet doesn't have the header, skip it
        if header_idx is None:
            continue

        # 2. Slice the dataframe: Data starts 1 row after header_idx
        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = raw_df.iloc[header_idx]

        # 3. Clean the data
        # Drop rows where Product Code is empty (blank lines)
        df = df.dropna(subset=['Product Code'])
        
        # Remove the 'GRAND TOTAL' row
        df = df[~df['Product Code'].astype(str).str.contains('GRAND TOTAL', case=False, na=False)]

        # 4. Add Month-Year column
        # Convert sheet name (e.g. "January 2025") to datetime
        # This defaults to the 1st of the month automatically for "Month Year" strings
        df['Month-Year'] = pd.to_datetime(sheet_name)

        processed_dfs.append(df)

    # 5. Combine all sheets
    return pd.concat(processed_dfs, ignore_index=True)

import pandas as pd

def convert_customer_masterlist_to_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=None, header=None, engine="xlrd")
    else:
        df = pd.read_excel(file_path, sheet_name=None, header=None, engine="xlrd")

    # Read ALL sheets, no header initially
    all_sheets = df
    
    processed_dfs = []

    for sheet_name, raw_df in all_sheets.items():
        # 1. Extract "Type" from Cell A2 (Row 1, Col 0)
        # We grab this before finding the header.
        # If the sheet is too small, use a placeholder.
        if raw_df.shape[0] > 1:
            customer_type = raw_df.iloc[1, 0]
        else:
            customer_type = "Unknown"

        # 2. Find the header row dynamically
        header_idx = None
        for idx, row in raw_df.iterrows():
            if "Customer's Name" in row.astype(str).values:
                header_idx = idx
                break
        
        if header_idx is None:
            continue

        # 3. Slice and set header
        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = raw_df.iloc[header_idx]

        # 4. Clean Data
        df = df.dropna(subset=["Customer's Name"])

        # 5. Add Metadata Columns
        df['Account'] = sheet_name       # Sheet Name -> Account
        df['Type'] = customer_type       # Cell A2 -> Type
        
        processed_dfs.append(df)

    # 6. Combine
    return pd.concat(processed_dfs, ignore_index=True)


def process_raw_materials_stock_df(file_path):

    if hasattr(file_path, "read"):
        data = BytesIO(file_path.read())
        df = pd.read_excel(data, sheet_name=0, header=None, engine="xlrd")
    else:
        df = pd.read_excel(file_path, sheet_name=0, header=None, engine="xlrd")

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

    # 2. Find the header row dynamically
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

    # 3. Slice and set header
    df = raw_df.iloc[header_idx + 1:].copy()
    df.columns = raw_df.iloc[header_idx]

    # 4. Clean Data
    df = df.dropna(subset=[key_col])
    df = df[~df[key_col].astype(str).str.contains('GRAND TOTAL', case=False, na=False)]

    # 5. Category Header Logic
    check_col = 'Unit' if 'Unit' in df.columns else 'UNIT'
    
    if check_col in df.columns:
        # Identify headers: Key exists, but Unit is NaN
        is_cat_header = df[check_col].isna()
        
        # Create Category column from header rows
        df['Category'] = df[key_col].where(is_cat_header)
        
        # Forward fill the category name down to items
        df['Category'] = df['Category'].ffill()
        
        # Fill any remaining NaNs (items before the first header) with "OTHERS"
        df['Category'] = df['Category'].fillna('OTHERS')
        
        # Remove the header rows themselves
        df = df[~is_cat_header]
    else:
        # If we can't detect categories via Unit column, label all as OTHERS
        df['Category'] = 'OTHERS'

    # 6. Add Inventory Date
    df['Inventory Date'] = inventory_date
    
    return df