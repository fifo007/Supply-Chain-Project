# APL Logistics Profitability Intelligence

An interactive Streamlit dashboard for analysing APL Logistics sales, profit, customer, product, discount, and delivery-performance data.

## Features

- Filter results by customer segment, market, category, and discount rate.
- Review key performance indicators for revenue, profit, margin, discounts, and late-delivery risk.
- Compare profitability across markets and shipping modes.
- Identify high-value customers, customer segments needing attention, profitable categories, and loss-making products.
- Explore the relationship between discount rates and profit margins, including high-discount loss-making orders.

## Project structure

```
.
├── APL_Logistics.csv   # Source dataset
├── app.py              # Streamlit dashboard
├── requirements.txt    # Python dependencies
└── README.md
```

## Getting started

1. Clone the repository and move into the project directory.

   ```bash
   git clone https://github.com/fifo007/Supply-Chain-Project.git
   cd Supply-Chain-Project
   ```

2. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Start the dashboard.

   ```bash
   streamlit run app.py
   ```

   Streamlit will open the dashboard in your browser, normally at `http://localhost:8501`.

## Data notes

The dashboard reads `APL_Logistics.csv` from the same folder as `app.py`. It loads the dataset with Latin-1 encoding and calculates the following analysis fields at runtime:

- Customer name
- Profit margin percentage
- Discount percentage and discount band

The source data has no order-date field, so the dashboard deliberately does not include a time-series revenue chart.

## Technologies

- Python
- Streamlit
- Pandas
- Plotly

## Requirements

Python 3.9 or later is recommended. Dependencies are listed in `requirements.txt`.
