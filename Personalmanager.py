# Import the necessary libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as px
from datetime import datetime
import os

# --- Data Persistence ---
# Define the filename for the financial data
DATA_FILE = 'financial_data.csv'

def load_data():
    """Loads financial data from a CSV file. Creates a new file if it doesn't exist."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Convert date columns to datetime objects for proper sorting and filtering
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        # Create an empty DataFrame with the required columns
        df = pd.DataFrame(columns=[
            'Date', 'Type', 'Category', 'Description', 'Amount', 'Source'
        ])
        df.to_csv(DATA_FILE, index=False)  # Save the empty DataFrame
        return df

def save_data(df):
    """Saves the DataFrame back to the CSV file."""
    df.to_csv(DATA_FILE, index=False)

# Load the initial data
df_data = load_data()

# --- Page Setup and Sidebar ---
st.set_page_config(page_title="Personal Financial Dashboard", layout="wide")

# Use a container to create a clean-looking sidebar for data input
with st.sidebar:
    st.header("Add New Entry")
    # Using st.form allows all widgets to be batched and submitted with a single button click
    with st.form("data_form", clear_on_submit=True):
        entry_date = st.date_input("Date", datetime.now())
        entry_type = st.selectbox("Entry Type", ["Income", "Expense", "Asset", "Liability"])
        entry_source = st.selectbox("Source/Account", ["Cash", "Checking", "Savings", "Credit Card", "Loan", "Investment", "Other"])
        entry_category = st.text_input("Category (e.g., Salary, Rent, Food, Car Loan)")
        entry_description = st.text_input("Description")
        entry_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Entry")

        # Handle the form submission
        if submitted:
            # Create a new row of data
            new_row = pd.DataFrame([{
                'Date': pd.to_datetime(entry_date),
                'Type': entry_type,
                'Category': entry_category,
                'Description': entry_description,
                'Amount': entry_amount,
                'Source': entry_source
            }])
            # Append the new row to the main DataFrame
            df_data = pd.concat([df_data, new_row], ignore_index=True)
            save_data(df_data) # Save the updated data
            st.success("Entry added successfully!")

# --- Main Dashboard Section ---
st.title("💰 Personal Financial Statement Dashboard")
st.write("Track your financial position and cash flow in real time.")

# --- Financial Calculations ---
# Calculate Net Worth (Assets - Liabilities)
def calculate_net_worth(df):
    """Calculates the current Net Worth."""
    assets = df[(df['Type'] == 'Asset')]['Amount'].sum()
    liabilities = df[(df['Type'] == 'Liability')]['Amount'].sum()
    return assets - liabilities

# Calculate Net Income (Income - Expenses)
def calculate_net_income(df, start_date=None, end_date=None):
    """Calculates Net Income for a given date range."""
    df_filtered = df[(df['Type'] == 'Income') | (df['Type'] == 'Expense')].copy()

    if start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['Date'] >= start_date) & (df_filtered['Date'] <= end_date)
        ]

    total_income = df_filtered[df_filtered['Type'] == 'Income']['Amount'].sum()
    total_expenses = df_filtered[df_filtered['Type'] == 'Expense']['Amount'].sum()
    return total_income, total_expenses, total_income - total_expenses

# Calculate current metrics
current_net_worth = calculate_net_worth(df_data)
total_income_all_time, total_expenses_all_time, net_income_all_time = calculate_net_income(df_data)

# --- Display Key Metrics ---
st.header("📊 Key Financial Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Net Worth", f"${current_net_worth:,.2f}")
with col2:
    st.metric("Total Income (All Time)", f"${total_income_all_time:,.2f}")
with col3:
    st.metric("Total Expenses (All Time)", f"${total_expenses_all_time:,.2f}")

st.markdown("---")

# --- Interactive Visualizations ---
st.header("📈 Financial Trends")

if not df_data.empty:
    # --- Net Income Over Time (Monthly Cash Flow) ---
    df_income_expenses = df_data[(df_data['Type'] == 'Income') | (df_data['Type'] == 'Expense')].copy()
    if not df_income_expenses.empty:
        df_income_expenses['Month'] = df_income_expenses['Date'].dt.to_period('M').astype(str)
        monthly_summary = df_income_expenses.groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
        monthly_summary.index = pd.to_datetime(monthly_summary.index)
        monthly_summary = monthly_summary.sort_index()
        fig_cashflow = px.bar(monthly_summary,
                              x=monthly_summary.index.strftime('%Y-%m'),
                              y=['Income', 'Expense'],
                              barmode='group',
                              title='Monthly Cash Flow (Income vs. Expenses)',
                              labels={'value': 'Amount ($)', 'x': 'Month'})
        fig_cashflow.update_layout(xaxis_title="Month", yaxis_title="Amount ($)")
        st.plotly_chart(fig_cashflow, use_container_width=True)
    else:
        st.info("No income or expense data to display for cash flow trends.")

    st.markdown("---")

    # --- Expense Breakdown (Pie Chart) ---
    df_expenses = df_data[df_data['Type'] == 'Expense'].copy()
    if not df_expenses.empty:
        expense_summary = df_expenses.groupby('Category')['Amount'].sum().reset_index()
        fig_expenses = px.pie(expense_summary,
                              values='Amount',
                              names='Category',
                              title='Expense Breakdown by Category',
                              hole=0.3)
        st.plotly_chart(fig_expenses, use_container_width=True)
    else:
        st.info("No expense data to display the breakdown.")
    
    st.markdown("---")

    # --- Assets vs. Liabilities (Bar Chart) ---
    df_positions = df_data[(df_data['Type'] == 'Asset') | (df_data['Type'] == 'Liability')].copy()
    if not df_positions.empty:
        positions_summary = df_positions.groupby('Type')['Amount'].sum().reset_index()
        fig_positions = px.bar(positions_summary,
                                x='Type',
                                y='Amount',
                                title='Assets vs. Liabilities',
                                color='Type',
                                labels={'Amount': 'Amount ($)'})
        st.plotly_chart(fig_positions, use_container_width=True)
    else:
        st.info("No asset or liability data to display the financial position.")

else:
    st.info("Please add your first financial entry using the sidebar to see the dashboard.")

# --- Transaction History ---
st.markdown("---")
st.header("📚 Transaction History")
st.write("You can view and filter all your entries below.")

# Display a data editor for users to view and update data
st.dataframe(df_data, use_container_width=True)

# Add a button to save any edits made directly in the dataframe
if st.button("Save DataFrame Edits"):
    try:
        # Streamlit's data editor returns an updated DataFrame
        # For simplicity, we just reload and save
        updated_df = load_data()
        save_data(updated_df)
        st.success("Dataframe changes saved!")
    except Exception as e:

        st.error(f"Failed to save changes: {e}")
