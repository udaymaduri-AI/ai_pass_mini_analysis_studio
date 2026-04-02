import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="AI-Pass Mini Analysis Studio", layout="wide")

st.title("AI-Pass Mini Analysis Studio")
st.caption("An automated data & business analysis companion for energy and operations data.")

@st.cache_data
def load_sample_data():
    return pd.read_csv("sample_data/energy_sample_data.csv", parse_dates=["date"])

@st.cache_data
def load_uploaded_data(file):
    return pd.read_csv(file)

def profile_data(df: pd.DataFrame):
    profiling = {}
    profiling["row_count"] = len(df)
    profiling["column_count"] = len(df.columns)
    profiling["columns"] = list(df.columns)
    profiling["dtypes"] = df.dtypes.astype(str).to_dict()
    profiling["missing_values"] = df.isna().sum().to_dict()
    profiling["describe"] = df.describe(include="all", datetime_is_numeric=True).T
    return profiling

def detect_time_and_metric(df: pd.DataFrame):
    time_col = None
    metric_col = None

    # Try to infer a time column
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            time_col = col
            break

    # If not obvious, try to parse first column as datetime
    if time_col is None:
        first_col = df.columns[0]
        try:
            pd.to_datetime(df[first_col])
            time_col = first_col
        except Exception:
            time_col = None

    # Choose first numeric column as metric
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        # Prefer total/energy/power-like columns
        preferred = [
            c
            for c in numeric_cols
            if any(k in c.lower() for k in ["total", "energy", "consumption", "kwh", "load", "power"])
        ]
        metric_col = preferred[0] if preferred else numeric_cols[0]

    return time_col, metric_col

def compute_trend_summary(df: pd.DataFrame, time_col: str, metric_col: str):
    data = df[[time_col, metric_col]].dropna().copy()
    data[time_col] = pd.to_datetime(data[time_col])
    data = data.sort_values(time_col)

    # Aggregate by day if needed
    if data[time_col].dt.floor("D").nunique() < len(data):
        data = data.groupby(data[time_col].dt.floor("D"))[metric_col].mean().reset_index(name=metric_col)
        data.rename(columns={time_col: "date"}, inplace(True))
        time_col = "date"

    x = (data[time_col] - data[time_col].min()).dt.total_seconds() / 86400.0
    y = data[metric_col].values

    if len(data) > 1 and np.std(y) > 0:
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
    else:
        slope = 0.0

    start_val = y[0]
    end_val = y[-1]
    change_abs = end_val - start_val
    change_pct = (change_abs / start_val * 100) if start_val != 0 else 0

    if abs(change_pct) < 5:
        direction = "relatively stable"
    elif change_pct > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return {
        "data": data,
        "slope": slope,
        "start_val": start_val,
        "end_val": end_val,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "direction": direction,
        "time_col": time_col,
        "metric_col": metric_col,
    }

def detect_anomalies_zscore(df: pd.DataFrame, metric_col: str, threshold: float = 2.5):
    series = df[metric_col].astype(float)
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        df_anom = df.copy()
        df_anom["z_score"] = 0.0
        df_anom["is_anomaly"] = False
        return df_anom, []

    z_scores = (series - mean) / std
    df_anom = df.copy()
    df_anom["z_score"] = z_scores
    df_anom["is_anomaly"] = z_scores.abs() >= threshold

    anomalies = df_anom[df_anom["is_anomaly"]].copy()
    return df_anom, anomalies

def generate_plain_summary(df: pd.DataFrame, time_col: str, metric_col: str, trend_info: dict):
    row_count = len(df)
    col_count = len(df.columns)
    date_min = pd.to_datetime(df[time_col]).min()
    date_max = pd.to_datetime(df[time_col]).max()
    avg_val = df[metric_col].mean()

    summary = f"The dataset contains {row_count:,} rows and {col_count} columns. "
    summary += f"It covers the period from {date_min.date()} to {date_max.date()} with '{metric_col}' as the primary metric. "
    summary += f"Average {metric_col} over this period is approximately {avg_val:,.1f}. "
    summary += (
        f"Overall, {metric_col} is {trend_info['direction']} with a total change of "
        f"{trend_info['change_abs']:,.1f} (about {trend_info['change_pct']:.1f}% over the full period)."
    )
    return summary

def generate_anomaly_insights(anomalies: pd.DataFrame, time_col: str, metric_col: str):
    if anomalies.empty:
        return [
            "No strong anomalies were detected for the chosen threshold. The metric behaves consistently over time."
        ]

    texts = []
    count = len(anomalies)
    max_anom = anomalies.iloc[anomalies["z_score"].abs().argmax()]
    when = pd.to_datetime(max_anom[time_col]).date()
    val = max_anom[metric_col]
    z = max_anom["z_score"]

    texts.append(
        f"{count} anomalous points were detected where {metric_col} deviated strongly from its usual pattern. "
        f"The most pronounced anomaly occurs on {when} with a value of {val:,.1f}, "
        f"corresponding to a z-score of {z:.2f}."
    )

    # Weekday vs weekend pattern for anomalies
    try:
        dt = pd.to_datetime(anomalies[time_col])
        weekday_counts = dt.dt.weekday.value_counts().sort_index()
        if not weekday_counts.empty:
            weekday_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dominant_idx = weekday_counts.idxmax()
            dominant_day = weekday_labels[dominant_idx]
            texts.append(
                f"Anomalies occur most often on {dominant_day}s, suggesting that operational patterns "
                f"on this day may be driving unusual energy behaviour."
            )
    except Exception:
        pass

    return texts

def generate_business_recommendations(trend_info: dict, anomalies: pd.DataFrame, metric_col: str):
    recs = []

    direction = trend_info["direction"]
    change_pct = trend_info["change_pct"]

    if direction == "increasing" and change_pct > 8:
        recs.append(
            f"{metric_col} shows a clear upward trend over the period (around {change_pct:.1f}% growth). "
            f"Review equipment efficiency and production schedules to ensure this growth is "
            f"intentional rather than driven by leaks or inefficiencies."
        )
    elif direction == "decreasing" and change_pct < -8:
        recs.append(
            f"{metric_col} is decreasing over time (roughly {change_pct:.1f}% reduction). "
            f"Capture the operational changes that led to this improvement "
            f"(e.g., equipment upgrades, scheduling changes) and standardise them across the site."
        )
    else:
        recs.append(
            f"{metric_col} is relatively stable over the analysed period. "
            f"Focus on targeted improvements on specific anomalous days rather than broad structural changes."
        )

    if not anomalies.empty:
        recs.append(
            "Investigate the top anomaly days in more detail (e.g., by checking maintenance logs, "
            "production changes, weather, or special events) to understand what drove the spikes or drops."
        )
        recs.append(
            "Set up simple monitoring alerts that flag days where the metric exceeds typical bounds "
            "so that operations teams can react quickly."
        )
    else:
        recs.append(
            "Maintain current operating practices but establish periodic reviews (monthly or quarterly) "
            "to ensure the pattern remains efficient over time."
        )

    recs.append(
        "Consider complementing this analysis with tariff information to identify opportunities for "
        "shifting flexible loads to cheaper time windows."
    )

    return recs

# Sidebar: data selection
st.sidebar.header("1. Data Ingestion")

uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
use_sample = st.sidebar.button("Use Sample Energy Dataset")

st.sidebar.markdown("---")
st.sidebar.header("2. Analysis Settings")

z_threshold = st.sidebar.slider("Anomaly z-score threshold", min_value=1.5, max_value=4.0, value=2.5, step=0.1)

run_analysis = st.sidebar.button("Run Analysis")

# Load data based on user choice
data_source_label = None
df = None

if uploaded_file is not None:
    try:
        df = load_uploaded_data(uploaded_file)
        data_source_label = f"Uploaded file: {uploaded_file.name}"
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")

if use_sample or (df is None and uploaded_file is None):
    df = load_sample_data()
    data_source_label = "Bundled sample energy dataset"

if df is not None:
    st.subheader("Loaded Data Preview")
    st.write(f"**Data source:** {data_source_label}")
    st.dataframe(df.head())

    if run_analysis:
        st.markdown("---")
        st.header("Automated Analysis Results")

        # Data profiling
        st.subheader("Data Profiling")
        profiling = profile_data(df)

        cols1, cols2, cols3 = st.columns(3)
        with cols1:
            st.metric("Row count", f"{profiling['row_count']:,}")
            st.metric("Column count", profiling["column_count"])
        with cols2:
            st.write("**Column names**")
            st.write(profiling["columns"])
        with cols3:
            st.write("**Missing values per column**")
            st.write(profiling["missing_values"])

        st.write("**Data types**")
        st.json(profiling["dtypes"])

        st.write("**Descriptive statistics**")
        st.dataframe(profiling["describe"])

        # Detect time & metric columns
        time_col, metric_col = detect_time_and_metric(df)
        if time_col is None or metric_col is None:
            st.error(
                "Could not automatically identify a time column and a numeric metric column. "
                "Please ensure your dataset has a date/time column and at least one numeric column "
                "(e.g., energy_kwh)."
            )
        else:
            st.success(
                f"Using '{time_col}' as the time column and '{metric_col}' as the primary metric for analysis."
            )

            # Ensure datetime type
            df[time_col] = pd.to_datetime(df[time_col])
            df_sorted = df.sort_values(time_col)

            # Trend analysis
            trend_info = compute_trend_summary(df_sorted, time_col, metric_col)
            trend_df = trend_info["data"]

            # Anomaly detection
            df_with_anom, anomalies = detect_anomalies_zscore(
                trend_df, trend_info["metric_col"], threshold=z_threshold
            )

            # Visualizations
            st.subheader("Visualisations")

            # 1. Trend chart
            st.markdown("**Trend over time**")
            fig_trend = px.line(
                trend_df,
                x=trend_info["time_col"],
                y=trend_info["metric_col"],
                title=f"{metric_col} over time",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # 2. Comparison chart: average by weekday
            st.markdown("**Average by day of week**")
            tmp = trend_df.copy()
            tmp["weekday"] = pd.to_datetime(tmp[trend_info["time_col"]]).dt.day_name()
            weekday_avg = tmp.groupby("weekday")[trend_info["metric_col"]].mean().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            fig_weekday = px.bar(
                weekday_avg.reset_index(),
                x="weekday",
                y=trend_info["metric_col"],
                title=f"Average {metric_col} by day of week",
            )
            st.plotly_chart(fig_weekday, use_container_width=True)

            # 3. Anomaly highlight chart
            st.markdown("**Anomaly highlight chart**")
            fig_anom = px.line(
                df_with_anom,
                x=trend_info["time_col"],
                y=trend_info["metric_col"],
                title=f"{metric_col} with anomalies highlighted",
            )
            if not anomalies.empty:
                fig_anom.add_scatter(
                    x=anomalies[trend_info["time_col"]],
                    y=anomalies[trend_info["metric_col"]],
                    mode="markers",
                    name="Anomaly",
                    marker=dict(color="red", size=8, symbol="x"),
                )
            st.plotly_chart(fig_anom, use_container_width=True)

            # Structured output panel
            st.markdown("---")
            st.header("Structured Results Panel")

            # Summary
            st.subheader("1. Summary")
            summary_text = generate_plain_summary(
                trend_df, trend_info["time_col"], trend_info["metric_col"], trend_info
            )
            st.write(summary_text)

            # Anomalies
            st.subheader("2. Anomalies")
            if anomalies.empty:
                st.write(
                    "No anomalies were detected for the chosen threshold. "
                    "You can lower the threshold in the sidebar to make the detector more sensitive."
                )
            else:
                st.write(
                    f"Detected {len(anomalies)} anomalies based on a z-score threshold of {z_threshold}."
                )
                st.dataframe(
                    anomalies[
                        [trend_info["time_col"], trend_info["metric_col"], "z_score"]
                    ]
                )

            # Insights
            st.subheader("3. Insights")
            anomaly_insights = generate_anomaly_insights(
                anomalies, trend_info["time_col"], trend_info["metric_col"]
            )
            for txt in anomaly_insights:
                st.markdown(f"- {txt}")

            # Recommendations
            st.subheader("4. Recommendations")
            recs = generate_business_recommendations(
                trend_info, anomalies, trend_info["metric_col"]
            )
            for r in recs:
                st.markdown(f"- {r}")

else:
    st.info("Upload a CSV file or click 'Use Sample Energy Dataset' in the sidebar to get started.")