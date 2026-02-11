# Pricing Optimizer

A Streamlit application for optimizing product pricing using regression-based demand modeling and profit simulation.

## Features

- Upload historical price and sales data (Excel or CSV)
- Fit demand models using Linear or Log-Log regression
- Simulate profit across a range of candidate prices
- Visualize demand curves and profit optimization charts
- Export simulation results to Excel

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Data Requirements

Your input file must contain two columns:
- **Price**: Product price (must be > 0)
- **Sales**: Units sold (must be >= 0)

Minimum 8 valid rows required for model fitting.
