# 🧪 J. Chemie Business Intelligence Hub

**A secure, offline Analytics Dashboard for monitoring Sales, Inventory, and Customer Collections.**

![J. Chemie Dashboard](https://img.shields.io/badge/Status-Internship%20Final-success) ![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Built%20With-Streamlit-red)

## 📖 Overview

This repository contains the source code for the **J. Chemie BI Hub**, a standalone desktop application developed to modernize data reporting. It replaces manual Excel consolidation with automated dashboards that run 100% locally on company computers, ensuring data security.

### Key Features
* **🚫 Offline & Secure:** No cloud uploads. Data is processed in-memory and wiped upon closing.
* **📊 Three Core Modules:**
    1.  **Customer Insights:** Track churn risk and outstanding collections.
    2.  **Inventory Intelligence:** Automated "Velocity-Based" restocking alerts.
    3.  **Sales Performance:** Agent rankings and monthly revenue trends.
* **⚙️ Zero-Code Settings:** Adjustable safety stock thresholds via the sidebar interface.

---

## 🚀 Installation (Windows)

We have automated the setup process. You do not need to know Python to install this.

### Step 1: Download
1.  Click the green **Code** button above -> **Download ZIP**.
2.  Extract the ZIP file to a permanent location (e.g., `Documents/JCHEM_DASHBOARD`).

### Step 2: One-Click Install
1.  Open the folder and double-click **`SETUP_DASHBOARD.bat`**.
2.  Wait for the black window to finish installing the required libraries.
3.  Once complete, a shortcut named **"JCHEM Dashboard"** (with the company logo) will appear on your Desktop.

---

## 🕹️ How to Use

Double-click the desktop icon to launch the hub.

### 1. 🏠 Home & Login
* **Password:** `jchemie-'KJ57NAMcb5Pg~_oQ0):uye@Gq5[@e)`
* Select a dashboard from the sidebar menu.

### 2. 🏭 Inventory & Procurement
* **Goal:** See what to buy and what is overstocked.
* **Input:** Drag & Drop the master `raw mat.xlsx` file.
* **Settings:** Use the sidebar sliders to adjust "Fast Moving" vs "Slow Moving" trigger levels (e.g., Change 50 units to 100 units).

### 3. 👥 Customer Insights
* **Goal:** Track debts and customers at risk of leaving.
* **Input:** Upload Sales/Customer logs.
* **Logic:**
    * 🔴 **High Risk:** No purchase > 90 days.
    * 🟡 **At Risk:** No purchase > 60 days.

### 4. 📈 Sales Performance
* **Goal:** Monthly volume trends and agent performance.
* **Input:** Sales Order CSV/Excel.

---

## 📂 Project Structure

```text
JCHEMIE/
├── SETUP_DASHBOARD.bat      # One-time installer script
├── Jchemie/                 # Main Source Code
│   ├── runme.bat            # Application Launcher
│   ├── Home.py              # Entry Point (Landing Page)
│   ├── app_icon.ico         # Desktop Icon
│   ├── requirements.txt     # Python Dependencies
│   ├── project1_utility.py  # Logic for Customer Module
│   ├── project2_utility.py  # Logic for Inventory Module
│   ├── project3_utility.py  # Logic for Sales Module
│   └── pages/               # Dashboard Pages
│       ├── 1_Customer_Management.py
│       ├── 2_Inventory_Procurement.py
│       └── 3_Sales_Performance.py
