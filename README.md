# AI-Pass Mini Analysis Studio

An opinionated mini analysis studio built with Streamlit that behaves like a simple data analyst + business analyst for energy or operational datasets.

## Features

- CSV upload plus bundled sample energy dataset (no setup required).
- Automatic data profiling (row/column counts, schema, missing values, descriptive statistics).
- Time-series trend analysis on an inferred metric.
- Z-score–based anomaly detection with adjustable sensitivity.
- Plain-language summaries, insights, and business recommendations.
- Interactive visualisations built with Plotly (trend, weekday comparison, anomaly highlighting).

## Dataset

The default dataset is a **synthetic daily energy consumption dataset** for one year.

- File: `sample_data/energy_sample_data.csv`
- Columns:
  - `date`: calendar date.
  - `total_energy_kwh`: aggregated daily energy usage.
  - `hvac_kwh`, `lighting_kwh`, `production_kwh`: component-level breakdowns.
- Behaviour: includes a slight upward trend, weekday/weekend patterns, random variation, and injected spikes/drops to act as anomalies.

Because this dataset is synthetic, it does **not** represent any real site or customer.

## Analysis approach

### Data profiling

On load, the app computes:

- Row and column counts.
- Column names and data types.
- Missing value counts per column.
- Descriptive statistics using `pandas.DataFrame.describe` (min, max, mean, standard deviation, quartiles, etc.).

### Time & metric detection

To reduce configuration friction, the app tries to automatically determine:

- **Time column**: the first column whose name contains `date` or `time`, otherwise it attempts to parse the first column as a datetime.
- **Metric column**: the first numeric column that contains energy-like keywords (`total`, `energy`, `consumption`, `kwh`, `load`, `power`) in its name, falling back to the first numeric column if none match.

If either cannot be identified, the app stops and shows a clear error instead of guessing incorrectly.

### Trend analysis

Once a time column and metric are identified, the app:

1. Sorts the data by time and aggregates to daily granularity when there are multiple records per day.
2. Fits a simple first-order polynomial (straight line) using `numpy.polyfit` over time.
3. Computes:
   - Start and end values.
   - Absolute and percentage change over the full period.
   - A qualitative direction label (`increasing`, `decreasing`, or `relatively stable`) based on the percentage change.

This information is fed into the natural-language summary and recommendations.

### Anomaly detection

Anomalies are detected using a **z-score** method on the selected metric:

1. Compute mean and standard deviation across the analysed period.
2. For each point, compute z-score = (value - mean) / standard deviation.
3. Flag an observation as an anomaly when the absolute z-score is greater than or equal to a configurable threshold (default 2.5).

This is a simple but effective approach for reasonably well-behaved series. The threshold can be adjusted in the sidebar to tune sensitivity.

### Insight generation

The current version uses **rule-based logic only** — it does **not** call external LLM APIs by default. Insights are built from:

- Dataset footprint (rows, columns, date range, average metric value).
- Trend direction and magnitude of change.
- Anomaly count, timing, and severity.
- Concentration of anomalies on particular weekdays if applicable.

These elements are combined into short, non-technical sentences (e.g., “Anomalies occur most often on Mondays, suggesting that operational patterns on this day may be driving unusual energy behaviour.”).

### Recommendations

Business recommendations are also rule-based and traceable:

- Upward trend with strong growth → focus on efficiency checks, equipment performance, and verifying that higher usage is intentional.
- Downward trend with strong reductions → encourage capturing and standardising the operational changes that produced savings.
- Stable trend → prioritise investigating specific anomalous days rather than making structural changes.
- Presence of anomalies → advise deeper investigation of anomaly days and setting up simple alerts.
- General → suggest combining this view with tariff information and other context for richer decisions.

## What is real vs. simplified

**Real logic:**

- Data ingestion and profiling, including descriptive statistics.
- Automatic detection of time and metric columns with sensible heuristics.
- Trend computation based on actual data (linear fit, absolute and percentage change).
- Z-score calculation and anomaly labelling, exposed in the UI and charts.
- All numbers shown in summaries, anomaly tables, and charts are computed directly from the dataset.

**Simplified / placeholder aspects:**

- Insight and recommendation text is rule-based template logic, not a full natural-language reasoning engine.
- No automatic root-cause analysis (e.g., weather, tariff, equipment logs) is performed.
- Only one metric is analysed at a time; multi-metric correlations are not explored.
- The anomaly method assumes a reasonably stationary distribution and may not be suitable for highly seasonal or regime-shifting data without further tuning.

## Running locally

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the Streamlit app from the repository root:

   ```bash
   streamlit run streamlit_app.py
   ```

4. Your browser should open automatically at `http://localhost:8501`. If not, navigate to that URL manually.

## Deployment on Streamlit Community Cloud

Assuming you have pushed this project to a public GitHub repository:

1. Go to https://streamlit.io and sign in.
2. Click **"Deploy an app"** and connect your GitHub account if prompted.
3. Select the repository containing this project.
4. For **Main file path**, enter:
