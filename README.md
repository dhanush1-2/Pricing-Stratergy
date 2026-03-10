# Pricing Optimizer

A Streamlit web application for data-driven product pricing decisions. Upload historical price and sales data, fit a statistical demand model, simulate profit across price points, and identify the optimal price that maximizes profit.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Data Requirements](#data-requirements)
- [How It Works](#how-it-works)
- [Demand Models](#demand-models)
- [Outputs](#outputs)
- [Sample Data](#sample-data)
- [Dependencies](#dependencies)

---

## Overview

The Pricing Optimizer helps managers and analysts answer one key question:
**"What price maximizes our profit?"**

Rather than guessing or using intuition, the tool fits a demand model to your historical data and simulates profit across hundreds of candidate price points — surfacing the optimal price automatically.

---

## Features

- **Data Upload** — Accepts `.csv` or `.xlsx` files; auto-normalizes column names
- **Data Validation** — Enforces minimum quality standards before modeling
- **Two Demand Models** — Choose between Linear and Log-Log (constant elasticity) regression
- **Profit Simulation** — Grid-searches over candidate prices to find the profit-maximizing point
- **Price Elasticity** — Calculates and interprets demand elasticity at the optimal price
- **Interactive Charts** — Plotly demand curve and profit-vs-price visualization
- **Excel Export** — Download full simulation results as `.xlsx`
- **Cost Inputs** — Configurable unit variable cost and fixed cost
- **Regression Summary** — Optional advanced OLS output for technical users
- **Warning System** — Flags unusual model results (positive demand slope, price below cost)

---

## Project Structure

```
Pricing Stratergy/
├── app.py                    # Main Streamlit application
├── preprocessing.ipynb       # Data exploration and preparation notebook
├── preprocessr.ipynb         # Alternative preprocessing notebook (experimental)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── data/
    ├── retail_price.csv      # Raw retail dataset (676 rows, 30 columns)
    ├── consoles_pricing.csv  # Extracted consoles data — ready for app use
    └── sample_data.csv       # Synthetic sample data for testing/demos
```

### Key Files

| File | Description |
|------|-------------|
| [app.py](app.py) | Streamlit app — validation, modeling, simulation, UI |
| [preprocessing.ipynb](preprocessing.ipynb) | EDA notebook — category analysis, correlation study, data extraction |
| [data/consoles_pricing.csv](data/consoles_pricing.csv) | 22-row clean dataset (price vs. sales for gaming consoles) |
| [data/sample_data.csv](data/sample_data.csv) | 32-row synthetic dataset for quick demos |

---

## Installation

**1. Clone the repository**

```bash
git clone <repo-url>
cd "Pricing Stratergy"
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
streamlit run app.py
```

Then open the URL shown in your terminal (usually `http://localhost:8501`).

**Quick start with sample data:**
- Upload `data/consoles_pricing.csv` or `data/sample_data.csv`
- Adjust unit cost and fixed cost in the sidebar
- Select a demand model and click through the results

---

## Data Requirements

Your input file must contain at minimum two columns:

| Column | Type | Constraint |
|--------|------|------------|
| `price` | Numeric | Must be > 0 |
| `sales` | Numeric | Must be >= 0 |

- Column names are **case-insensitive** (e.g., `Price`, `PRICE`, `price` all work)
- **Minimum 8 valid rows** required for model fitting
- Rows with missing, zero, or negative prices are automatically excluded
- Accepts `.csv` and `.xlsx` formats

---

## How It Works

```
1. Upload CSV/Excel
        ↓
2. Validate & Clean Data
   - Normalize column names
   - Remove invalid rows (NaN, Price ≤ 0)
   - Enforce minimum 8 rows
        ↓
3. Fit Demand Model (OLS Regression)
   - Linear:   Sales = a + b × Price
   - Log-Log:  ln(Sales) = a + b × ln(Price)
        ↓
4. Simulate Profit Over Price Grid
   - Generate N candidate prices (default: 300)
   - Predict sales at each price
   - Calculate: Profit = Sales × (Price − UnitCost) − FixedCost
   - Identify price with maximum profit
        ↓
5. Calculate Price Elasticity
   - Linear:   E = b × (OptimalPrice / OptimalSales)
   - Log-Log:  E = b  (constant)
   - Classify: Elastic (|E| > 1) / Inelastic (|E| < 1)
        ↓
6. Visualize & Export
   - Demand curve chart
   - Profit vs. price chart
   - Simulation table
   - Excel download
```

---

## Demand Models

### Linear Demand
```
Sales = a + b × Price
```
- `b` is the slope (expected to be negative — higher price → lower sales)
- Elasticity varies with price: `E = b × (Price / Sales)`
- Best when the price-sales relationship is roughly linear

### Log-Log (Constant Elasticity) Demand
```
ln(Sales) = a + b × ln(Price)
```
- `b` is the price elasticity of demand (constant across all prices)
- Commonly used in economics and retail pricing research
- Best when percentage changes in price drive percentage changes in sales

### Elasticity Interpretation

| Value | Classification | Meaning |
|-------|---------------|---------|
| \|E\| > 1 | Elastic | Demand is sensitive to price changes |
| \|E\| = 1 | Unit Elastic | Proportional response |
| \|E\| < 1 | Inelastic | Demand is relatively insensitive to price |

---

## Outputs

| Output | Description |
|--------|-------------|
| Demand function | Equation with fitted coefficients |
| Price elasticity | Value and business interpretation |
| Optimal price | Price point with highest simulated profit |
| Expected sales | Predicted units sold at optimal price |
| Expected profit | Profit at optimal price |
| Demand curve chart | Observed data points vs. fitted demand curve |
| Profit curve chart | Profit across all simulated price points |
| Simulation table | Full grid of prices, predicted sales, and profit |
| Excel export | Downloadable `.xlsx` with all simulation data |

---

## Sample Data

Two ready-to-use datasets are included:

### `data/consoles_pricing.csv`
- **Source**: Extracted from a Brazilian retail dataset (May 2017 – Jul 2018)
- **Category**: Gaming consoles
- **Rows**: 22
- **Price range**: $19.90 – $36.20
- **Price-sales correlation**: -0.57 (strong inverse relationship — well-suited for demand modeling)

### `data/sample_data.csv`
- **Source**: Synthetic data generated for demonstration
- **Rows**: 32
- **Price range**: $9.99 – $39.99
- **Note**: Designed to show a clear, clean inverse demand relationship

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | >=1.31 | Web application framework |
| pandas | >=2.0 | Data loading and manipulation |
| numpy | >=1.24 | Numerical operations |
| statsmodels | >=0.14 | OLS regression modeling |
| plotly | >=5.18 | Interactive charts |
| openpyxl | >=3.1 | Excel file read/write |

Install all with:
```bash
pip install -r requirements.txt
```

---

## Data Background

The raw dataset (`retail_price.csv`) comes from a Brazilian e-commerce platform and contains 676 records across 9 product categories (garden, health, watches, computers, beds, cooling, furniture, perfumery, consoles). The preprocessing notebook identifies **consoles** as having the strongest price-demand relationship and extracts it as a clean dataset for use in the app.

Category-level price-sales correlations from the raw data:

| Category | Correlation |
|----------|-------------|
| consoles | -0.57 |
| garden | -0.30 |
| health | -0.18 |
| watches | -0.10 |
| perfumery | -0.09 |
| cool | +0.06 |
| computers | +0.07 |
| furniture | +0.10 |
| bed | +0.37 |
