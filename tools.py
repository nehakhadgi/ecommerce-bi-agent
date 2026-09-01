import pandas as pd
import matplotlib
# Force Matplotlib to use a headless backend for cloud deployments
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tempfile
import os

def load_data(filepath="ecommerce_sales_data.csv"):
    """Load the sales dataset and convert dates."""
    df = pd.read_csv(filepath)
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df

def get_sales_summary(df):
    """Get overall sales KPIs."""
    total_orders = len(df)
    total_revenue = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    avg_order_value = total_revenue / total_orders
    profit_margin = (total_profit / total_revenue) * 100
    
    return {
        "total_orders": int(total_orders),
        "total_revenue": float(total_revenue),
        "total_profit": float(total_profit),
        "avg_order_value": float(avg_order_value),
        "profit_margin": float(profit_margin)
    }

def get_revenue_by_region(df):
    """Calculate revenue and profit by geographic region."""
    summary = df.groupby("Region").agg(
        revenue=("Sales", "sum"),
        profit=("Profit", "sum"),
        orders=("Order ID", "count")
    ).reset_index()
    return summary

def get_top_products(df, n=5):
    """Get top N best-selling products."""
    top_products = df.groupby("Product Name").agg(
        revenue=("Sales", "sum"),
        orders=("Order ID", "count")
    ).sort_values(by="revenue", ascending=False).head(n).reset_index()
    return top_products

def get_category_performance(df):
    """Performance breakdown by product category."""
    category_perf = df.groupby("Category").agg(
        revenue=("Sales", "sum"),
        profit=("Profit", "sum"),
        orders=("Order ID", "count")
    ).reset_index()
    return category_perf

def generate_chart(df, chart_type, data_source):
    """Generate a matplotlib chart and return the temporary file path."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Build the chart based on data source and chart type
    if data_source == "region":
        # FIXED: Changed "Sales Amount" to "Sales"
        data = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        if chart_type == "bar":
            data.plot(kind="bar", ax=ax, color=["#2196F3", "#4CAF50", "#FF9800", "#F44336"])
        else:
            data.plot(kind="line", ax=ax, marker="o", color="#2196F3")
        ax.set_title("Revenue by Region", fontsize=16)
        ax.set_ylabel("Revenue ($)")
        
    elif data_source == "category":
        # FIXED: Changed "Sales Amount" to "Sales"
        data = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        if chart_type == "bar":
            data.plot(kind="bar", ax=ax, color=["#2196F3", "#4CAF50", "#FF9800"])
        else:
            data.plot(kind="line", ax=ax, marker="o", color="#2196F3")
        ax.set_title("Revenue by Category", fontsize=16)
        ax.set_ylabel("Revenue ($)")
        
    elif data_source == "monthly":
        # FIXED: Changed "Sales Amount" to "Sales"
        monthly = df.set_index("Order Date")["Sales"].resample("ME").sum()
        if chart_type == "line":
            monthly.plot(kind="line", ax=ax, marker="o", color="#2196F3")
        else:
            monthly.plot(kind="bar", ax=ax, color="#2196F3")
        ax.set_title("Monthly Sales Trend", fontsize=16)
        ax.set_ylabel("Revenue ($)")
        plt.xticks(rotation=45)
        
    ax.set_xlabel("")
    plt.tight_layout()
    
    # Save to a temporary file and return the path
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=100)
    plt.close(fig)
    return tmp.name
