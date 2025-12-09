import streamlit as st

st.set_page_config(
    page_title="JCHEM Home",
    page_icon="🏠",
    layout="wide"
)

# --- HEADER SECTION ---
st.write("# Welcome to JCHEM Business Intelligence Hub! 👋")

st.markdown("""
This application centralizes your business data into three easy-to-use dashboards. 
**No data is stored online.** Everything runs locally on your machine using the files you upload.
""")

st.markdown("---")

# --- INSTRUCTION CARDS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 1️⃣ Customer Insights")
    st.markdown("**Goal:** Track collection rates, debts, and churn risk.")
    st.markdown("**Required Files:**")
    st.code("Sales/Customer Data (CSV/Excel)\n(Must contain: Customer Name, Date, Amount, Status)")
    st.markdown("👉 *Go here to see who owes money and who stopped buying.*")

with col2:
    st.info("### 2️⃣ Inventory & Procurement")
    st.markdown("**Goal:** Monitor stock health and automate reorders.")
    st.markdown("**Required Files:**")
    st.code("1. Inventory List (Sheet 3)\n2. PO Logs (Sheet 1 & 2)")
    st.markdown("👉 *Go here to see what to buy and supplier delays.*")

with col3:
    st.info("### 3️⃣ Sales Performance")
    st.markdown("**Goal:** Analyze revenue trends and agent performance.")
    st.markdown("**Required Files:**")
    st.code("Sales Order Data (CSV/Excel)\n(Must contain: Date, Amount, Agent, Region)")
    st.markdown("👉 *Go here to see monthly volume and top agents.*")

st.markdown("---")

# --- HOW TO USE SECTION ---
st.subheader("📝 How to Use This Tool")

st.markdown("""
1.  **Select a Dashboard:** Click on the page names in the **sidebar (left)**.
2.  **Upload Data:** Once on the page, look for the **"📂 Data Source"** section in the sidebar.
3.  **Drag & Drop:** Drag your Excel or CSV files from your folder into the box.
4.  **Analyze:** The dashboard will automatically calculate KPIs and generate charts.
""")

st.warning("""
**🔒 Privacy Note:** This tool operates in **Offline Mode**. The files you upload are processed in your computer's temporary memory and are wiped as soon as you close the tab. 
""")