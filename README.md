# AI-Pass Analysis Studio

**AI-Powered Business Data Analysis Tool**

A Streamlit-based analysis studio that lets users upload data, automatically profile it, detect anomalies, generate insights, and receive business recommendations — all through an interactive web interface.

Built by **Uday** as part of the 24-Hour Technical Challenge (Data Analytics / ML / Data Engineering).

---

## Live Demo

> **Live App**: _[Add your Streamlit Cloud URL here after deployment]_
>
> **GitHub Repo**: _[Add your GitHub repo URL here]_

---

## Dataset Used

The app ships with a **sample energy dataset** (`data/sample_energy_data.csv`) containing 731 daily records from January 2023 to December 2024.

**Columns:**
| Column | Description |
|--------|-------------|
| `date` | Daily timestamp (2023-01-01 to 2024-12-31) |
| `energy_consumption_kwh` | Daily energy consumption in kWh |
| `cost_usd` | Daily operating cost in USD |
| `temperature_f` | Ambient temperature in Fahrenheit |
| `humidity_percent` | Relative humidity (%) |
| `occupancy` | Building occupancy count |
| `production_output_units` | Daily production output |
| `equipment_efficiency_percent` | Equipment efficiency rating (%) |

The dataset includes realistic seasonal patterns (higher energy use in winter/summer), weekday/weekend occupancy patterns, and intentionally injected anomalies (energy spikes, cost surges, efficiency drops) to test detection capabilities.

**Note:** The app also accepts any user-uploaded CSV file — it is not limited to energy data.

---

## Analysis Approach

The system follows a structured pipeline:

1. **Data Ingestion** — Upload CSV or load built-in dataset. Automatic date column detection and type inference.
2. **Data Profiling** — Row/column counts, missing value analysis, data type breakdown, descriptive statistics, and correlation heatmap.
3. **Analysis Engine** — Trend analysis, anomaly detection, key metric extraction, and time-based aggregations.
4. **Insight Generation** — Rule-based logic analyzes trends, volatility, correlations, and anomaly patterns to produce human-readable findings.
5. **Recommendations** — Business-oriented suggestions with priority levels (High/Medium/Low) based on detected patterns.
6. **Visualization** — Interactive Plotly charts: trend lines, comparison bars, anomaly highlights, distributions, and correlation heatmaps.
7. **Export** — Downloadable structured report (TXT) and data export (CSV).

---

## Anomaly Detection Method

Two complementary statistical methods are used:

**IQR (Interquartile Range) Method:**
- Computes Q1 (25th percentile) and Q3 (75th percentile) for each numeric column
- Flags values below `Q1 - 1.5 * IQR` or above `Q3 + 1.5 * IQR`
- Good for detecting extreme outliers in skewed distributions

**Z-Score Method:**
- Calculates the number of standard deviations from the mean using `scipy.stats.zscore`
- Flags values with `|z| > 3` (more than 3 standard deviations from mean)
- Good for symmetric distributions and identifying statistically rare events

Both methods run on all numeric columns. Detected anomalies are displayed in a table with the date, column name, value, and detection method. They are also highlighted in red on scatter plots.

---

## Insights Logic

Insights are generated using rule-based analysis (no external AI API required):

- **Trend Detection**: Fits `sklearn.linear_model.LinearRegression` on numeric columns over time. Reports whether metrics are increasing/decreasing and the percentage change.
- **Volatility Analysis**: Computes coefficient of variation (std/mean). Flags columns with high relative volatility.
- **Correlation Analysis**: Computes Pearson correlation matrix. Reports strong correlations (|r| > 0.7) between column pairs — useful for identifying linked metrics.
- **Anomaly Clustering**: Groups detected anomalies by time period to identify systemic issues vs. isolated events.

Recommendations are derived from these insights with priority levels:
- **High**: Upward cost/consumption trends, efficiency drops, clustered anomalies
- **Medium**: Strong correlations suggesting optimization opportunities, moderate volatility
- **Low**: Data quality suggestions, monitoring recommendations

---

## What is Real vs. Simplified

| Aspect | Status | Notes |
|--------|--------|-------|
| Data ingestion & preview | Real | Handles any CSV with automatic type detection |
| Data profiling | Real | Full descriptive statistics, missing value analysis |
| Anomaly detection (IQR + Z-score) | Real | Standard statistical methods used in production |
| Trend analysis (Linear Regression) | Real | Proper sklearn regression with slope and R-squared |
| Correlation analysis | Real | Pearson correlation with configurable threshold |
| Insight generation | Simplified | Rule-based logic, not NLP/LLM-powered |
| Recommendations | Simplified | Template-based from detected patterns |
| Visualizations | Real | Interactive Plotly charts with proper axes/labels |
| Export/Report | Real | Structured downloadable output |

The AI layer uses rule-based logic rather than an LLM API. This keeps the app self-contained with zero external API dependencies, making deployment simpler and the system fully testable offline.

---

## Next Improvements

- **LLM Integration**: Connect OpenAI/Gemini API for natural language insight summaries and conversational data Q&A
- **Time-Series Forecasting**: Add Prophet or ARIMA-based forecasting for future trend prediction
- **Streaming Simulation**: Real-time data ingestion with live-updating dashboards
- **Multiple Dataset Comparison**: Side-by-side analysis of different time periods or datasets
- **PDF Report Export**: Generate formatted PDF reports with charts embedded
- **Database Connectors**: Support PostgreSQL, MySQL, and API data sources beyond CSV
- **User Authentication**: Add login for multi-user environments
- **Custom Anomaly Thresholds**: Let users configure IQR multiplier and Z-score cutoff

---

## Tech Stack

- **Python 3.8+**
- **Streamlit** — Web framework and UI
- **Pandas / NumPy** — Data manipulation and computation
- **Plotly** — Interactive visualizations
- **Seaborn / Matplotlib** — Static charts and heatmaps
- **Scikit-learn** — Linear regression for trend analysis
- **SciPy** — Z-score calculations

---

## Project Structure

```
AI-pass_Uday/
├── app.py                        # Main Streamlit application
├── data/
│   └── sample_energy_data.csv    # Sample energy dataset (731 records)
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── config.toml               # Streamlit configuration
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---

## Local Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/AI-pass-Analysis-Studio.git
cd AI-pass-Analysis-Studio

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deployment

Deployed on **Streamlit Community Cloud**. See `DEPLOYMENT_GUIDE.md` for step-by-step instructions.

---

Built by **Uday** | AI-Pass Analysis Studio | 2026
