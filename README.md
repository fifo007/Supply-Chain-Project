# APL Logistics Profitability Intelligence

An interactive Streamlit dashboard for analysing APL Logistics sales, profit, customers, products, discounts, markets, and category performance.

## Features

- Filter results by customer segment, market, category, product, and discount rate.
- Review key performance indicators for revenue, profit, profit margin, and average discount.
- Compare top and bottom customers by profit and assess customer-segment contribution.
- Analyse product-level margins, category profitability, and a category-by-market profitability heatmap.
- Explore the relationship between discount rates and profit margins, identify high-discount loss-making line items, and test what-if discount scenarios.

## Project structure

```
.
├── APL_Logistics.csv   # Source dataset
├── app.py              # Streamlit dashboard
├── APL_Logistics_Research_Paper.docx  # EDA, insights, and recommendations
├── build_research_paper.py             # Rebuilds the research paper from the dataset
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

### Discount scenario assumptions

The what-if calculator estimates the impact of a uniform proposed discount rate for the currently filtered order lines. It estimates undiscounted sales from each line's current discount and holds the observed cost per line constant. It is a planning aid, not a forecast of customer demand or future costs.

## Technologies

- Python
- Streamlit
- Pandas
- Plotly

## Requirements

Python 3.9 or later is recommended. Dependencies are listed in `requirements.txt`.
