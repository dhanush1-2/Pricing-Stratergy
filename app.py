import io
import numpy as np
import pandas as pd
import streamlit as st
import statsmodels.api as sm
import plotly.graph_objects as go

st.set_page_config(page_title="Pricing Optimizer (Regression + Profit)", layout="wide")

st.title("Pricing Optimizer (Excel-style Simulation)")
st.caption(
    "Upload historical Price & Sales → fit demand using regression → simulate profit across many prices → choose the best price."
)

REQUIRED_COLUMNS = {"price", "sales"}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(list(missing))}. "
            f"Your file must contain columns named Price and Sales (case-insensitive)."
        )

    df = df[["price", "sales"]].copy()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    df = df.dropna()

    df = df[(df["price"] > 0) & (df["sales"] >= 0)]
    if len(df) < 8:
        raise ValueError("Not enough valid rows after cleaning. Provide at least ~8+ rows with numeric Price>0 and Sales>=0.")
    return df

def fit_linear_demand(df: pd.DataFrame):
    # Sales = a + b*Price
    X = sm.add_constant(df["price"])
    y = df["sales"]
    model = sm.OLS(y, X).fit()
    a = float(model.params["const"])
    b = float(model.params["price"])
    return model, a, b

def fit_loglog_demand(df: pd.DataFrame):
    # ln(Sales) = a + b*ln(Price)  (requires Sales>0)
    d = df[df["sales"] > 0].copy()
    if len(d) < 8:
        raise ValueError("Not enough rows with Sales>0 to fit the log-log model.")
    d["ln_sales"] = np.log(d["sales"])
    d["ln_price"] = np.log(d["price"])
    X = sm.add_constant(d["ln_price"])
    y = d["ln_sales"]
    model = sm.OLS(y, X).fit()
    a = float(model.params["const"])
    b = float(model.params["ln_price"])
    return model, a, b

def predict_sales(model_type: str, a: float, b: float, prices: np.ndarray) -> np.ndarray:
    if model_type == "Linear":
        q = a + b * prices
        return np.clip(q, 0, None)
    # Log-Log: Sales = exp(a) * Price^b
    q = np.exp(a) * np.power(prices, b)
    return np.clip(q, 0, None)
    #Update demand Function

def simulate_profit_over_prices(
    model_type: str,
    a: float,
    b: float,
    unit_cost: float,
    fixed_cost: float,
    p_min: float,
    p_max: float,
    grid_n: int
):
    prices = np.linspace(p_min, p_max, grid_n)
    qhat = predict_sales(model_type, a, b, prices)
    profit = qhat * (prices - unit_cost) - fixed_cost

    idx = int(np.nanargmax(profit))
    return pd.DataFrame({
        "price": prices,
        "predicted_sales": qhat,
        "profit": profit
    }), idx

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("1) Upload data")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) or CSV", type=["xlsx", "csv"])

st.sidebar.header("2) Demand model")
model_type = st.sidebar.selectbox("Choose model", ["Linear", "Log-Log"], index=0)

st.sidebar.header("3) Costs (for profit calculation)")
unit_cost = st.sidebar.number_input("Unit variable cost (c)", min_value=0.0, value=0.0, step=0.5)
fixed_cost = st.sidebar.number_input("Fixed cost (F)", min_value=0.0, value=0.0, step=100.0)

st.sidebar.header("4) Simulation settings (Excel-style)")
use_data_range = st.sidebar.checkbox("Use price range from uploaded data", value=True)
buffer_pct = st.sidebar.slider("Range buffer (%)", 0, 50, 10, 5)
grid_n = st.sidebar.slider("How many candidate prices to test?", 50, 2000, 300, 50)

show_advanced = st.sidebar.checkbox("Show regression summary (advanced)", value=False)

if not uploaded:
    st.info("Upload an Excel or CSV with columns: **Price** and **Sales**.")
    st.stop()

# ----------------------------
# Load + clean
# ----------------------------
try:
    if uploaded.name.lower().endswith(".csv"):
        df_raw = pd.read_csv(uploaded)
    else:
        df_raw = pd.read_excel(uploaded)

    df = validate_data(df_raw)
except Exception as e:
    st.error(f"Data issue: {e}")
    st.stop()

# Overview
left, right = st.columns([1.2, 1])
with left:
    st.subheader("Uploaded data (cleaned)")
    st.dataframe(df.head(25), use_container_width=True)
with right:
    st.subheader("Quick summary")
    st.write(f"Rows: **{len(df)}**")
    st.write(f"Price range: **{df['price'].min():.3g} → {df['price'].max():.3g}**")
    st.write(f"Sales range: **{df['sales'].min():.3g} → {df['sales'].max():.3g}**")

# ----------------------------
# Fit model
# ----------------------------
try:
    if model_type == "Linear":
        model, a, b = fit_linear_demand(df)
    else:
        model, a, b = fit_loglog_demand(df)
except Exception as e:
    st.error(f"Model fitting issue: {e}")
    st.stop()

# ----------------------------
# Choose simulation range
# ----------------------------
data_min = float(df["price"].min())
data_max = float(df["price"].max())

if use_data_range:
    buf = buffer_pct / 100.0
    p_min = max(0.0001, data_min * (1 - buf))
    p_max = data_max * (1 + buf)
else:
    p_min = st.sidebar.number_input("Min price", min_value=0.0001, value=max(0.0001, data_min * 0.9))
    p_max = st.sidebar.number_input("Max price", min_value=p_min + 0.0001, value=data_max * 1.1)

# ----------------------------
# Excel-style simulation to find optimal price
# ----------------------------
sim_table, best_idx = simulate_profit_over_prices(
    model_type=model_type,
    a=a,
    b=b,
    unit_cost=unit_cost,
    fixed_cost=fixed_cost,
    p_min=p_min,
    p_max=p_max,
    grid_n=grid_n
)

p_star = float(sim_table.loc[best_idx, "price"])
q_star = float(sim_table.loc[best_idx, "predicted_sales"])
profit_star = float(sim_table.loc[best_idx, "profit"])

st.markdown("---")

# ----------------------------
# Display Demand Function & Elasticity
# ----------------------------
st.subheader("Demand Function (from regression)")

if model_type == "Linear":
    # Display: Sales = a + b × Price
    sign = "+" if b >= 0 else "−"
    st.latex(rf"Q = {a:.4g} {sign} {abs(b):.4g} \times P")

    # Elasticity for linear model varies: E = b × (P/Q)
    # Calculate at optimal price point
    elasticity_at_optimal = b * (p_star / q_star) if q_star > 0 else float('nan')
    st.write(f"**Elasticity formula (Linear):** E = b × (P / Q) = {b:.4g} × (P / Q)")
    st.write(f"**Elasticity at optimal price (P = {p_star:.4g}):** E = {elasticity_at_optimal:.4g}")
else:
    # Log-Log: Sales = exp(a) × Price^b
    exp_a = np.exp(a)
    st.latex(rf"Q = {exp_a:.4g} \times P^{{{b:.4g}}}")
    st.write(f"*(Equivalent to: ln(Q) = {a:.4g} + {b:.4g} × ln(P))*")

    # Elasticity for log-log is constant = b
    elasticity_at_optimal = b
    st.write(f"**Elasticity (Log-Log):** E = {b:.4g} *(constant at all prices)*")

# Interpret elasticity
if not np.isnan(elasticity_at_optimal):
    if elasticity_at_optimal < -1:
        elasticity_type = "**Elastic** (E < -1): Sales are highly sensitive to price changes"
    elif elasticity_at_optimal > -1 and elasticity_at_optimal < 0:
        elasticity_type = "**Inelastic** (-1 < E < 0): Sales are less sensitive to price changes"
    elif elasticity_at_optimal == -1:
        elasticity_type = "**Unit Elastic** (E = -1): % change in sales equals % change in price"
    else:
        elasticity_type = "**Positive elasticity**: Unusual - demand increases with price (Giffen/Veblen good or data issue)"
    st.info(f"Elasticity Interpretation: {elasticity_type}")

st.markdown("---")
st.subheader("Optimal price (chosen by simulation, not calculus)")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Optimal price", f"{p_star:.4g}")
k2.metric("Expected sales at optimal price", f"{q_star:.4g}")
k3.metric("Expected profit at optimal price", f"{profit_star:.4g}")
k4.metric("Tested prices", f"{grid_n}")

# ----------------------------
# Charts
# ----------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Demand curve (estimated from regression)")
    prices_line = np.linspace(p_min, p_max, 200)
    q_line = predict_sales(model_type, a, b, prices_line)

    fig_d = go.Figure()
    fig_d.add_trace(go.Scatter(x=df["price"], y=df["sales"], mode="markers", name="Observed"))
    fig_d.add_trace(go.Scatter(x=prices_line, y=q_line, mode="lines", name="Predicted"))
    fig_d.add_vline(x=p_star)
    fig_d.update_layout(xaxis_title="Price", yaxis_title="Sales", height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_d, use_container_width=True)

with c2:
    st.subheader("Profit vs. Price (the decision chart)")
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=sim_table["price"], y=sim_table["profit"], mode="lines", name="Profit"))
    fig_p.add_vline(x=p_star)
    fig_p.update_layout(xaxis_title="Price", yaxis_title="Profit", height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_p, use_container_width=True)

# Teaching box
with st.expander("How the app finds the optimal price (Excel-style)"):
    st.write(
        "1) Fit a demand model using regression (Sales depends on Price).\n"
        "2) Create a list of many candidate prices across a range.\n"
        "3) For each candidate price:\n"
        "   - Predict sales using the regression model\n"
        "   - Compute profit = PredictedSales × (Price − UnitCost) − FixedCost\n"
        "4) Choose the price with the **highest profit**.\n"
        "\nThis is exactly what managers do in Excel using a table + MAX()."
    )

# ----------------------------
# Simulation table + export
# ----------------------------
st.markdown("---")
st.subheader("Simulation table (like an Excel sheet)")
st.dataframe(sim_table, use_container_width=True)

buf = io.BytesIO()
sim_table.to_excel(buf, index=False)
st.download_button(
    "Download simulation table (Excel)",
    data=buf.getvalue(),
    file_name="profit_simulation.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

if show_advanced:
    st.markdown("---")
    st.subheader("Regression output (advanced)")
    st.text(model.summary())

# Warnings
warnings = []
if model_type == "Linear" and b >= 0:
    warnings.append("Estimated slope (b) is non-negative. This dataset may not show demand decreasing with price.")
if p_star <= unit_cost:
    warnings.append("Optimal price is at/below unit cost within the tested range. Consider costs or expand the price range.")
if warnings:
    st.warning(" | ".join(warnings))
