import pandas as pd


def load_data(filepath= "ecommerce_sales_data.csv"):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(filepath)
    # Convert Order Date from text to datetime for time-based analysis
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df


def get_sales_summary(df):
    # Calculate overall business metrics (Changed 'Sales Amount' to 'Sales')
    total_orders = len(df)
    total_revenue = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    avg_order_value = df["Sales"].mean()
    profit_margin = (total_profit / total_revenue) * 100

    # Format everything into a readable summary string
    return (
        f"Sales Summary:\n"
        f"- Total Orders: {total_orders:,}\n"
        f"- Total Revenue: ${total_revenue:,.2f}\n"
        f"- Total Profit: ${total_profit:,.2f}\n"
        f"- Average Order Value: ${avg_order_value:,.2f}\n"
        f"- Overall Profit Margin: {profit_margin:.1f}%"
    )


def get_revenue_by_region(df):
    # Group orders by region and calculate aggregate stats (Changed 'Sales Amount' to 'Sales')
    region_stats = df.groupby("Region").agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Sales", "count"),
    ).sort_values("Revenue", ascending=False)

    # Build a formatted string with one line per region
    lines = ["Revenue by Region:"]
    for region, row in region_stats.iterrows():
        margin = (row["Profit"] / row["Revenue"]) * 100
        lines.append(
            f"- {region}: Revenue=${row['Revenue']:,.2f}, "
            f"Profit=${row['Profit']:,.2f}, "
            f"Orders={row['Orders']:,}, "
            f"Margin={margin:.1f}%"
        )
    return "\n".join(lines)


def get_top_products(df, n=5):
    # Group by product and rank by total revenue (Changed 'Sales Amount' to 'Sales')
    product_stats = df.groupby("Product Name").agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum"),
    ).sort_values("Revenue", ascending=False).head(n)

    # Format a numbered list of top products
    lines = [f"Top {n} Products by Revenue:"]
    for i, (product, row) in enumerate(product_stats.iterrows(), 1):
        lines.append(
            f"{i}. {product}: Revenue=${row['Revenue']:,.2f}, "
            f"Profit=${row['Profit']:,.2f}, "
            f"Units Sold={row['Quantity']:,}"
        )
    return "\n".join(lines)


def get_category_performance(df):
    # Group by category and calculate comprehensive metrics (Changed 'Sales Amount' to 'Sales')
    cat_stats = df.groupby("Category").agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Sales", "count"),
        Avg_Quantity=("Quantity", "mean"),
    ).sort_values("Revenue", ascending=False)

    # Format each category's performance into a readable line
    lines = ["Category Performance:"]
    for category, row in cat_stats.iterrows():
        margin = (row["Profit"] / row["Revenue"]) * 100
        lines.append(
            f"- {category}: Revenue=${row['Revenue']:,.2f}, "
            f"Profit=${row['Profit']:,.2f}, "
            f"Margin={margin:.1f}%, "
            f"Orders={row['Orders']:,}, "
            f"Avg Qty/Order={row['Avg_Quantity']:.1f}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df)} orders\n")
    print(get_sales_summary(df))
    print()
    print(get_revenue_by_region(df))
    print()
    print(get_top_products(df))
    print()
    print(get_category_performance(df))