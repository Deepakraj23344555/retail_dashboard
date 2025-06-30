import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import plotly.express as px

# -------------------- DATABASE SETUP --------------------
engine = sqlalchemy.create_engine('sqlite:///sales.db')
Session = sessionmaker(bind=engine)
session = Session()

# -------------------- HELPER FUNCTIONS --------------------
def save_to_db(df):
    try:
        df['date'] = pd.to_datetime(df['date'])
        df.to_sql('sales', engine, if_exists='append', index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to DB: {e}")
        return False

def load_data():
    query = "SELECT * FROM sales"
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception:
        return pd.DataFrame()

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide")
st.title("🛒 Retail Sales Analytics Dashboard")

menu = ["Upload Data", "View Data", "Dashboard"]
choice = st.sidebar.selectbox("Navigate", menu)

# -------------------- PAGE 1: UPLOAD --------------------
if choice == "Upload Data":
    st.subheader("Upload Sales CSV File")

    with st.expander("📌 CSV Format Example"):
        st.markdown("""
        | date       | product     | region  | units_sold | revenue |
        |------------|-------------|---------|------------|---------|
        | 2024-06-01 | Widget A    | East    | 10         | 100     |
        | 2024-06-02 | Widget B    | West    | 5          | 50      |
        """)

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        try:
            df = pd.read_csv(file, encoding='latin1')  # Fixed encoding issue
            st.write("✅ Preview of uploaded data:")
            st.dataframe(df)

            if st.button("Save to Database"):
                success = save_to_db(df)
                if success:
                    st.success("✅ Data saved to database!")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# -------------------- PAGE 2: VIEW DATA --------------------
elif choice == "View Data":
    st.subheader("📑 View Stored Sales Data")
    data = load_data()
    if data.empty:
        st.warning("⚠️ No data found. Please upload some CSVs first.")
    else:
        st.dataframe(data)

# -------------------- PAGE 3: DASHBOARD --------------------
elif choice == "Dashboard":
    st.subheader("📊 Sales Dashboard")

    data = load_data()
    if data.empty:
        st.warning("⚠️ No data found. Please upload some CSVs first.")
    else:
        # Sidebar filters
        st.sidebar.header("🔎 Filter Data")
        region = st.sidebar.selectbox("Region", ["All"] + sorted(data['region'].unique()))
        product = st.sidebar.selectbox("Product", ["All"] + sorted(data['product'].unique()))

        # Apply filters
        if region != "All":
            data = data[data['region'] == region]
        if product != "All":
            data = data[data['product'] == product]

        # KPIs
        st.markdown("### 📈 Key Performance Indicators")
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue", f"${data['revenue'].sum():,.2f}")
        col2.metric("Total Units Sold", f"{data['units_sold'].sum():,.0f}")

        # Trends over time
        data['date'] = pd.to_datetime(data['date'])
        daily = data.groupby('date').agg({'revenue': 'sum', 'units_sold': 'sum'}).reset_index()

        st.markdown("### 📅 Revenue Over Time")
        fig1 = px.line(daily, x='date', y='revenue', markers=True)
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### 📅 Units Sold Over Time")
        fig2 = px.line(daily, x='date', y='units_sold', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Top products
        top_products = data.groupby('product').agg({'revenue': 'sum'}).reset_index().sort_values(by='revenue', ascending=False)
        st.markdown("### 🥇 Top Selling Products")
        fig3 = px.bar(top_products, x='product', y='revenue', text_auto=True)
        st.plotly_chart(fig3, use_container_width=True)
