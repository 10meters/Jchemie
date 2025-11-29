import pandas as pd
import math
import os
from rapidfuzz import process, fuzz

def normalize(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()

def convert_sales_file_to_df(path):
    raw = pd.read_excel(path, header=None, dtype=object)

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
