"""APL Logistics profitability dashboard.

Run with: streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="APL Logistics | Profitability Intelligence",
    page_icon="📦",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("APL_Logistics.csv")
PROFIT_COLUMN = "Order Profit Per Order"


@st.cache_data(show_spinner="Loading logistics data...")
def load_data(path: str) -> pd.DataFrame:
    """Load the CSV and add only the fields needed for analysis."""
    # This source file is encoded in Latin-1 (for example, it contains names
    # such as "Cortés").  Pandas otherwise assumes UTF-8 and raises a decode
    # error before the dashboard can load.
    data = pd.read_csv(path, encoding="latin-1", low_memory=False)

    numeric_columns = [
        "Sales",
        PROFIT_COLUMN,
        "Order Item Discount Rate",
        "Order Item Quantity",
        "Days for shipping (real)",
        "Days for shipment (scheduled)",
        "Late_delivery_risk",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Customer Name"] = (
        data["Customer Fname"].fillna("").astype(str).str.strip()
        + " "
        + data["Customer Lname"].fillna("").astype(str).str.strip()
    ).str.strip()
    data["Profit Margin %"] = (
        data[PROFIT_COLUMN].div(data["Sales"].replace(0, pd.NA)).mul(100)
    )
    data["Discount %"] = data["Order Item Discount Rate"].mul(100)
    data["Discount Band"] = pd.cut(
        data["Discount %"],
        bins=[-0.01, 0, 10, 20, 100],
        labels=["No discount", "1–10%", "11–20%", ">20%"],
    )
    return data


def currency(value: float) -> str:
    """Format an amount for a compact KPI card."""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def empty_chart(message: str) -> None:
    st.info(message)


if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE.name}. Put it in the same folder as app.py.")
    st.stop()

df = load_data(str(DATA_FILE))

st.title("📦 APL Logistics Profitability Intelligence")
st.caption(
    "Explore revenue, profit, customers, products, discounts, and delivery performance. "
    "Each row in this dataset is treated as an order line item."
)

# Sidebar filters
st.sidebar.header("Dashboard filters")
segments = sorted(df["Customer Segment"].dropna().unique())
markets = sorted(df["Market"].dropna().unique())
categories = sorted(df["Category Name"].dropna().unique())
products = sorted(df["Product Name"].dropna().unique())

selected_segments = st.sidebar.multiselect("Customer segment", segments, default=segments)
selected_markets = st.sidebar.multiselect("Market / region", markets, default=markets)
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
selected_products = st.sidebar.multiselect("Product", products, default=products)

maximum_discount = float(df["Discount %"].max())
discount_range = st.sidebar.slider(
    "Discount rate (%)",
    min_value=0.0,
    max_value=max(1.0, maximum_discount),
    value=(0.0, max(1.0, maximum_discount)),
    step=1.0,
)

filtered = df[
    df["Customer Segment"].isin(selected_segments)
    & df["Market"].isin(selected_markets)
    & df["Category Name"].isin(selected_categories)
    & df["Product Name"].isin(selected_products)
    & df["Discount %"].between(*discount_range)
].copy()

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
    st.stop()

revenue = filtered["Sales"].sum()
profit = filtered[PROFIT_COLUMN].sum()
profit_margin = profit / revenue * 100 if revenue else 0
average_discount = filtered["Discount %"].mean()
late_rate = filtered["Late_delivery_risk"].mean() * 100

tab_overview, tab_customers, tab_products, tab_discounts = st.tabs(
    ["Revenue & Profit", "Customers", "Products & Categories", "Discount Impact"]
)

with tab_overview:
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total revenue", currency(revenue))
    kpi2.metric("Total profit", currency(profit))
    kpi3.metric("Profit margin", f"{profit_margin:.1f}%")
    kpi4.metric("Average discount", f"{average_discount:.1f}%")
    kpi5.metric("Late-delivery risk", f"{late_rate:.1f}%")

    left, right = st.columns(2)
    market_summary = (
        filtered.groupby("Market", as_index=False)
        .agg(Revenue=("Sales", "sum"), Profit=(PROFIT_COLUMN, "sum"))
        .sort_values("Profit", ascending=False)
    )
    with left:
        fig = px.bar(
            market_summary,
            x="Market",
            y="Revenue",
            color="Profit",
            color_continuous_scale="RdYlGn",
            title="Revenue by market (colour = profit)",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Revenue", coloraxis_colorbar_title="Profit")
        st.plotly_chart(fig, use_container_width=True)

    shipping_summary = (
        filtered.groupby("Shipping Mode", as_index=False)
        .agg(
            Revenue=("Sales", "sum"),
            Profit=(PROFIT_COLUMN, "sum"),
            Late_Risk=("Late_delivery_risk", "mean"),
        )
    )
    with right:
        fig = px.bar(
            shipping_summary,
            x="Shipping Mode",
            y="Late_Risk",
            color="Profit",
            text_auto=".1%",
            color_continuous_scale="RdYlGn",
            title="Late-delivery risk by shipping mode",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Late-delivery risk", yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Note: this CSV contains no order-date field, so a time-series revenue chart is intentionally excluded."
    )

with tab_customers:
    customer_summary = (
        filtered.groupby(["Customer Id", "Customer Name", "Customer Segment"], as_index=False)
        .agg(
            Revenue=("Sales", "sum"),
            Profit=(PROFIT_COLUMN, "sum"),
            Average_Discount=("Discount %", "mean"),
            Line_Items=("Sales", "size"),
        )
    )
    customer_summary["Profit Margin %"] = (
        customer_summary["Profit"].div(customer_summary["Revenue"].replace(0, pd.NA)).mul(100)
    )
    left, middle, right = st.columns(3)
    with left:
        top_customers = customer_summary.nlargest(10, "Profit").sort_values("Profit")
        fig = px.bar(
            top_customers,
            x="Profit",
            y="Customer Name",
            orientation="h",
            color="Customer Segment",
            title="Top 10 customers by profit",
        )
        st.plotly_chart(fig, use_container_width=True)
    with middle:
        bottom_customers = customer_summary.nsmallest(10, "Profit").sort_values("Profit", ascending=False)
        fig = px.bar(
            bottom_customers,
            x="Profit",
            y="Customer Name",
            orientation="h",
            color="Customer Segment",
            title="Bottom 10 customers by profit",
        )
        fig.update_layout(yaxis_title="", xaxis_title="Profit")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        segment_summary = (
            customer_summary.groupby("Customer Segment", as_index=False)
            .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Customers=("Customer Id", "nunique"))
        )
        fig = px.scatter(
            segment_summary,
            x="Revenue",
            y="Profit",
            size="Customers",
            color="Customer Segment",
            title="Customer segment value",
            hover_data=["Customers"],
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customers needing attention")
    attention = customer_summary[
        (customer_summary["Revenue"] >= customer_summary["Revenue"].median())
        & (customer_summary["Profit Margin %"] < 10)
    ].sort_values("Profit Margin %")
    st.dataframe(
        attention[["Customer Name", "Customer Segment", "Revenue", "Profit", "Profit Margin %", "Average_Discount"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%,.0f"),
            "Profit": st.column_config.NumberColumn(format="$%,.0f"),
            "Profit Margin %": st.column_config.NumberColumn(format="%.1f%%"),
            "Average_Discount": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

with tab_products:
    category_summary = (
        filtered.groupby("Category Name", as_index=False)
        .agg(Revenue=("Sales", "sum"), Profit=(PROFIT_COLUMN, "sum"), Quantity=("Order Item Quantity", "sum"))
    )
    category_summary["Profit Margin %"] = (
        category_summary["Profit"].div(category_summary["Revenue"].replace(0, pd.NA)).mul(100)
    )
    left, right = st.columns(2)
    with left:
        fig = px.bar(
            category_summary.sort_values("Profit"),
            x="Profit",
            y="Category Name",
            orientation="h",
            color="Profit",
            color_continuous_scale="RdYlGn",
            title="Category profitability",
        )
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Profit")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        product_summary = (
            filtered.groupby(["Product Name", "Category Name"], as_index=False)
            .agg(Revenue=("Sales", "sum"), Profit=(PROFIT_COLUMN, "sum"), Discount=("Discount %", "mean"))
        )
        product_summary["Profit Margin %"] = (
            product_summary["Profit"].div(product_summary["Revenue"].replace(0, pd.NA)).mul(100)
        )
        low_margin_products = (
            product_summary[product_summary["Revenue"] >= 1_000]
            .nsmallest(12, "Profit Margin %")
        )
        fig = px.bar(
            low_margin_products.sort_values("Profit Margin %"),
            x="Profit Margin %",
            y="Product Name",
            color="Category Name",
            orientation="h",
            title="Product-level margin analysis (lowest margins)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Category profitability heatmap")
    heatmap_data = (
        filtered.groupby(["Category Name", "Market"], as_index=False)
        .agg(Profit=(PROFIT_COLUMN, "sum"))
    )
    top_categories = (
        heatmap_data.groupby("Category Name", as_index=False)["Profit"]
        .sum()
        .nlargest(15, "Profit")["Category Name"]
    )
    fig = px.density_heatmap(
        heatmap_data[heatmap_data["Category Name"].isin(top_categories)],
        x="Market",
        y="Category Name",
        z="Profit",
        histfunc="sum",
        color_continuous_scale="RdYlGn",
        labels={"Market": "Market", "Category Name": "Category", "color": "Profit"},
        title="Profit by category and market (top 15 categories)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Category performance table")
    st.dataframe(
        category_summary.sort_values("Profit", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%,.0f"),
            "Profit": st.column_config.NumberColumn(format="$%,.0f"),
            "Profit Margin %": st.column_config.NumberColumn(format="%.1f%%"),
            "Quantity": st.column_config.NumberColumn(format="%,.0f"),
        },
    )

with tab_discounts:
    discount_summary = (
        filtered.groupby("Discount Band", observed=False, as_index=False)
        .agg(Revenue=("Sales", "sum"), Profit=(PROFIT_COLUMN, "sum"), Margin=("Profit Margin %", "mean"), Records=("Sales", "size"))
        .dropna(subset=["Discount Band"])
    )
    left, right = st.columns(2)
    with left:
        fig = px.bar(
            discount_summary,
            x="Discount Band",
            y="Margin",
            color="Profit",
            color_continuous_scale="RdYlGn",
            title="Average margin by discount band",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Average profit margin (%)")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        sample = filtered.sample(min(4_000, len(filtered)), random_state=42)
        fig = px.scatter(
            sample,
            x="Discount %",
            y="Profit Margin %",
            color="Category Name",
            opacity=0.45,
            render_mode="svg",
            title="Discount rate versus profit margin",
            hover_data=["Product Name", "Sales"],
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    high_discount_loss = filtered[
        (filtered["Discount %"] >= 20) & (filtered[PROFIT_COLUMN] < 0)
    ]
    st.subheader("High-discount loss-making line items")
    st.metric("Records requiring review", f"{len(high_discount_loss):,}")
    st.dataframe(
        high_discount_loss[["Product Name", "Category Name", "Market", "Sales", PROFIT_COLUMN, "Discount %"]]
        .sort_values(PROFIT_COLUMN)
        .head(100),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sales": st.column_config.NumberColumn(format="$%,.2f"),
            PROFIT_COLUMN: st.column_config.NumberColumn("Profit", format="$%,.2f"),
            "Discount %": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    st.subheader("What-if discount scenario")
    scenario_discount = st.slider(
        "Proposed uniform discount rate (%)",
        min_value=0.0,
        max_value=50.0,
        value=float(min(50, round(average_discount))),
        step=1.0,
        help="Estimates results if the displayed order lines used one discount rate. Product cost is assumed unchanged.",
    )
    base_sales = filtered["Sales"].div(1 - filtered["Order Item Discount Rate"].clip(upper=0.99))
    estimated_sales = (base_sales * (1 - scenario_discount / 100)).sum()
    estimated_cost = (filtered["Sales"] - filtered[PROFIT_COLUMN]).sum()
    estimated_profit = estimated_sales - estimated_cost
    estimated_margin = estimated_profit / estimated_sales * 100 if estimated_sales else 0
    scenario1, scenario2, scenario3 = st.columns(3)
    scenario1.metric("Estimated sales", currency(estimated_sales), delta=currency(estimated_sales - revenue))
    scenario2.metric("Estimated profit", currency(estimated_profit), delta=currency(estimated_profit - profit))
    scenario3.metric("Estimated margin", f"{estimated_margin:.1f}%", delta=f"{estimated_margin - profit_margin:.1f} pp")
    st.caption("Scenario calculation: undiscounted sales are estimated from the current discount rate; cost per order line is held constant. This is a planning estimate, not a forecast.")

st.divider()
st.caption("Built for APL Logistics • Data source: APL_Logistics.csv")
