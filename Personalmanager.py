import streamlit as st
import pandas as pd 
import plotly.express as px
from datetime import datetime
import os


DATA_FILE = 'financial_data.csv'

def load_data():
    """ load fianacial data from a CSV. Create a new file if it doesn't exist."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)

        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        df=pd.DataFrame(columns=[
            'Date','Type','Category','Description','Amount','Source'
        ])
        df.to_csv(DATA_FILE, index=False)
        return df
    
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df_data=load_data()

st.set_page_config(page_title="Personal Financial Dashboard",layout="wide")



with st.sidebar:
    st.header("Add New Entry")

    with st.form("data_form", clear_on_submit=True):
        entry_date = st.date_input("Date", datetime.now())
        entry_type = st.selectbox("Entry Type", ["Income","Expense","Asset","Liability"])
        entry_source = st.selectbox("Source/Account",["Cash","Mobile Money","Saving","Credit Card","Loan","Investment(Crypto)","Others"])
        entry_category= st.selectbox("Category",[ "Saving", "Rent","Food", "Toilaries","Car expenses","loan", "Utilities","Other expenses"])
        entry_description= st.text_input("Description")
        entry_amount = st.number_input("Amount (Ghc)", min_value=0.0,format="%.2f")
        submitted= st.form_submit_button("Add Entry")


        if submitted:

            new_row = pd.DataFrame([{
                'Date':pd.to_datetime(entry_date),
                'Type' : entry_type,
                'Category': entry_category,
                'Description': entry_description,
                'Amount': entry_amount,
                'Source': entry_source
            }])

            df_data=pd.concat([df_data, new_row], ignore_index=True)
            save_data(df_data)
            st.success("Entry added successfully!")



#--- Main Dashboard Section ---
st.title("💰 Personal Financial Statement Dashboard 💸")
st.write("Track your financial position and cash flow in real time. ⏳")


#--- Financial Calculations ---
# Calculate Net Wealth (Assests - Liabilities)
def calculate_net_worth(df):
    """Calculate the current Net Wealth"""
    assets = df[(df['Type']=='Asset')]['Amount'].sum()
    liabilities= df[(df['Type']=='Liability')]['Amount'].sum()
    net_worth= assets-liabilities
    return net_worth

# Calculate the Net Income (Income-Expenses)
def calculate_net_income(df, start_date=None, end_date=None):
    df_filtered = df[(df['Type']=='Income') | (df['Type'] == 'Expense')].copy()

    if start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['Date']>= start_date) & (df_filtered['Date'<= end_date])
        ] 
    total_income = df_filtered[df_filtered['Type']== 'Income']['Amount'].sum()
    total_expense =df_filtered[df_filtered['Type']=='Expense']['Amount'].sum()
    return total_income, total_expense, total_income-total_expense


# Calculate current metrics
current_net_worth=calculate_net_worth(df_data)
total_income_all_time, total_expenses_all_time, net_income_all_time =calculate_net_income(df_data)


#--- Display Key Metrics ---
st.header("📊 Key Financial Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Net Worth", f"${current_net_worth:,.2f}")
with col2:
    st.metric("Total Income (All Time)", f"${total_income_all_time:,.2f}")
with col1:
    st.metric("Total Expense (All Time)", f"${total_expenses_all_time:,.2f}")

st.markdown("---")

# --- Interactive Visualizations ---
st.header("📈 Financial Trends")

if not df_data.empty:
    # --- Net Income Over Time (Monthly Cash Flow) ---
    df_income_expenses = df_data[(df_data['Type']=='Income') | (df_data['Type']== 'Expense')].copy()
    if not df_income_expenses.empty:
        df_income_expenses['Month']= df_income_expenses['Date'].dt.to_period('M').astype(str)
        monthly_summary = df_income_expenses.groupby(['Month','Type'])['Amount'].sum().unstack(fill_value=0)
        monthly_summary.index=pd.to_datetime(monthly_summary.index)
        monthly_summary = monthly_summary.sort_index()
        fig_cashflow = px.bar(monthly_summary,
                            x= monthly_summary.index.strftime('%Y-%m'),
                            y=['Income','Expense'],
                            barmode='group',
                            title='Monthly Cash Flow (Income vs. Expenses)',
                            labels={'value': 'Amount ($)','x':'Month'})
        fig_cashflow.update_layout(xaxis_title="Month",yaxis_title="Amount ($)")
        st.plotly_chart(fig_cashflow, use_container_width=True)
    else:
        st.info("No income or expense data to display for cash flow trends.")

    st.markdown("---")


    #--- Expense Breakdown (Pie Chart) ---
    df_expenses = df_data[df_data['Type']=='Expense'].copy()
    if not df_expenses.empty:
        expense_summary = df_expenses.groupby('Category')['Amount'].sum().reset_index()
        fig_expenses= px.pie(expense_summary,
                             values='Amount',
                             names='Category',
                             title='Expense Breakdown by Category',
                             hole=0.5)
        st.plotly_chart(fig_expenses, use_container_width=True)
    else:
        st.info("no expenses data to display the breakdown.")

    st.markdown("---")

#--- Assets vs. Liabilities (Bar chart) ---
df_positions= df_data[(df_data['Type']== 'Asset') | (df_data['Type']== 'Liability')].copy()
if not df_positions.empty:
    position_summary = df_positions.groupby('Type')['Amount'].sum().reset_index()
    fig_postions = px.bar(position_summary,
                          x='Type',
                          y='Amount',
                          title='Assets vs. liabilities',
                          color='Type',
                          labels={'Amount': 'Amount($)'})
    st.plotly_chart(fig_postions, use_container_width=True)
else:
    st.info("Please add your first financial entry using the sidebar to see the dashboard")



#--- Transaction History ---
st.markdown("---")
st.header("📚 Transaction History")
st.write("You can view and filter all your entries below")

# Display a data editor for users to view and update data
st.dataframe(df_data, use_container_width=True)


#Add a button to save any edits made directly in the dataframe
if st.button("Save DataFrame Edits"):
    try:
        update_df= load_data()
        save_data(update_df)
        st.success("Dataframe changes saved!")
    except Exception as e:
        st.error(f"Failed to save changes: {e}")