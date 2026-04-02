import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import io
import warnings

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="AI-Pass Analysis Studio",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .insight-high {
            background-color: #fee;
            border-left: 4px solid #d32f2f;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        .insight-medium {
            background-color: #fff3e0;
            border-left: 4px solid #f57c00;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        .insight-low {
            background-color: #e8f5e9;
            border-left: 4px solid #388e3c;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
        }
        .badge-high {
            background-color: #d32f2f;
            color: white;
        }
        .badge-medium {
            background-color: #f57c00;
            color: white;
        }
        .badge-low {
            background-color: #388e3c;
            color: white;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            color: #888;
            font-size: 0.85em;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = None
if "original_data" not in st.session_state:
    st.session_state.original_data = None
if "date_column" not in st.session_state:
    st.session_state.date_column = None


@st.cache_data
def load_sample_data():
    """Load sample energy dataset (file OR fallback synthetic data)"""
    import os

    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'sample_energy_data.csv'),
        os.path.join('.', 'data', 'sample_energy_data.csv'),
        os.path.join(os.getcwd(), 'data', 'sample_energy_data.csv'),
        'data/sample_energy_data.csv',
    ]

    # Try loading from file
    for csv_path in possible_paths:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                return df
            except Exception:
                continue

    # ✅ FALLBACK (IMPORTANT FIX)
    st.warning("Sample file not found. Using generated dataset instead.")

    # Generate synthetic energy dataset
    dates = pd.date_range(start="2023-01-01", periods=100)
    energy = np.random.normal(loc=100, scale=15, size=100)

    df = pd.DataFrame({
        "date": dates,
        "energy_consumption": energy
    })

    return df


def detect_date_column(df):
    """Automatically detect date column"""
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            return col
        if col.lower() in ['date', 'timestamp', 'time', 'datetime']:
            try:
                pd.to_datetime(df[col])
                return col
            except:
                pass
    return None


def calculate_trend(x, y):
    """Calculate linear regression trend"""
    valid_idx = ~(np.isnan(x) | np.isnan(y))
    if valid_idx.sum() < 2:
        return None, None, None

    x_clean = x[valid_idx].reshape(-1, 1)
    y_clean = y[valid_idx]

    try:
        model = LinearRegression()
        model.fit(x_clean, y_clean)
        slope = model.coef_[0]
        r_squared = model.score(x_clean, y_clean)
        return model, slope, r_squared
    except:
        return None, None, None


def detect_anomalies_iqr(data, column):
    """Detect anomalies using IQR method"""
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    anomalies = (data[column] < lower_bound) | (data[column] > upper_bound)
    return anomalies, lower_bound, upper_bound


def detect_anomalies_zscore(data, column, threshold=3):
    """Detect anomalies using Z-score method"""
    z_scores = np.abs(stats.zscore(data[column].dropna()))
    return z_scores > threshold


def generate_insights(df, date_col):
    """Generate insights from the data"""
    insights = []
    recommendations = []

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Trend analysis
    if date_col and len(numeric_cols) > 0:
        if isinstance(df[date_col].iloc[0], str):
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col])
        else:
            df_temp = df.copy()

        x_numeric = np.arange(len(df_temp))

        for col in numeric_cols[:3]:  # Analyze top 3 numeric columns
            try:
                y = df_temp[col].values
                if np.isnan(y).sum() < len(y) * 0.5:  # If less than 50% missing
                    y_clean = np.nan_to_num(y, nan=np.nanmean(y))
                    model, slope, r2 = calculate_trend(x_numeric, y_clean)

                    if slope is not None:
                        if slope > 0:
                            pct_change = (slope / np.mean(y_clean[~np.isnan(y)])) * 100 if np.mean(y_clean[~np.isnan(y)]) != 0 else 0
                            insights.append({
                                'type': 'trend',
                                'column': col,
                                'direction': 'upward',
                                'strength': f"{pct_change:.2f}%",
                                'priority': 'High' if pct_change > 5 else 'Medium'
                            })
                        elif slope < 0:
                            pct_change = (slope / np.mean(y_clean[~np.isnan(y)])) * 100 if np.mean(y_clean[~np.isnan(y)]) != 0 else 0
                            insights.append({
                                'type': 'trend',
                                'column': col,
                                'direction': 'downward',
                                'strength': f"{abs(pct_change):.2f}%",
                                'priority': 'High' if abs(pct_change) > 5 else 'Medium'
                            })
            except:
                pass

    # Volatility analysis
    for col in numeric_cols:
        try:
            mean_val = df[col].mean()
            std_val = df[col].std()
            cv = (std_val / mean_val * 100) if mean_val != 0 else 0

            if cv > 30:
                insights.append({
                    'type': 'volatility',
                    'column': col,
                    'cv': f"{cv:.2f}%",
                    'priority': 'Medium'
                })
        except:
            pass

    # Correlation analysis
    try:
        corr_matrix = df[numeric_cols].corr()
        strong_corrs = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    strong_corrs.append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'corr': corr_val
                    })

        for corr in strong_corrs[:3]:  # Top 3 correlations
            insights.append({
                'type': 'correlation',
                'col1': corr['col1'],
                'col2': corr['col2'],
                'strength': f"{corr['corr']:.2f}",
                'priority': 'Medium'
            })
    except:
        pass

    return insights


def generate_recommendations(df, insights, date_col):
    """Generate business recommendations based on insights"""
    recommendations = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Recommendations based on trends
    for insight in insights:
        if insight['type'] == 'trend':
            col = insight['column']
            direction = insight['direction']
            strength = insight['strength']

            if 'energy' in col.lower() or 'consumption' in col.lower():
                if direction == 'upward':
                    recommendations.append({
                        'text': f"Energy consumption shows an upward trend of {strength}. Investigate potential inefficiencies, HVAC settings, or equipment issues.",
                        'priority': 'High'
                    })
                elif direction == 'downward' and float(strength.replace('%', '')) > 5:
                    recommendations.append({
                        'text': f"Energy consumption decreased by {strength}. Verify if this is due to operational changes or equipment upgrades.",
                        'priority': 'Low'
                    })

            elif 'efficiency' in col.lower():
                if direction == 'downward':
                    recommendations.append({
                        'text': f"Equipment efficiency declining by {strength}. Schedule maintenance review to prevent further degradation.",
                        'priority': 'High'
                    })

        elif insight['type'] == 'volatility':
            col = insight['column']
            cv = insight['cv']

            recommendations.append({
                'text': f"{col} shows high volatility (CV: {cv}). Consider implementing monitoring systems to track variations.",
                'priority': 'Medium'
            })

        elif insight['type'] == 'correlation':
            col1, col2, strength = insight['col1'], insight['col2'], insight['strength']

            if ('temperature' in col1.lower() or 'temperature' in col2.lower()) and \
               ('energy' in col1.lower() or 'energy' in col2.lower()):
                recommendations.append({
                    'text': f"Strong correlation ({strength}) between temperature and energy usage suggests HVAC optimization opportunity.",
                    'priority': 'Medium'
                })

    # Anomaly-based recommendations
    anomaly_count = 0
    for col in numeric_cols:
        try:
            anomalies, _, _ = detect_anomalies_iqr(df, col)
            anomaly_count += anomalies.sum()
        except:
            pass

    if anomaly_count > 0:
        recommendations.append({
            'text': f"{anomaly_count} anomalies detected across the dataset. Investigate and address outlier events.",
            'priority': 'High'
        })

    # Missing data recommendations
    missing_pct = (df.isnull().sum() / len(df) * 100).sum()
    if missing_pct > 5:
        recommendations.append({
            'text': f"Data quality: {missing_pct:.1f}% of cells are missing. Improve data collection or handle missing values appropriately.",
            'priority': 'Medium'
        })

    # Remove duplicates and sort by priority
    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec['text'] not in seen:
            seen.add(rec['text'])
            unique_recs.append(rec)

    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    unique_recs.sort(key=lambda x: priority_order.get(x['priority'], 3))

    return unique_recs[:5]  # Return top 5


def render_home_section():
    """Render Home/Upload section"""
    st.title("🏠 AI-Pass Analysis Studio")
    st.subheader("AI-Powered Data Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)

                # Auto-detect date columns
                for col in df.columns:
                    if col.lower() in ['date', 'timestamp', 'time', 'datetime']:
                        df[col] = pd.to_datetime(df[col], errors='coerce')

                st.session_state.data = df
                st.session_state.original_data = df.copy()
                st.session_state.date_column = detect_date_column(df)
                st.success("✓ File uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    with col2:
        st.markdown("### Use Sample Data")
        if st.button("📊 Load Energy Dataset", use_container_width=True):
            df = load_sample_data()
            if df is not None:
                st.session_state.data = df
                st.session_state.original_data = df.copy()
                st.session_state.date_column = detect_date_column(df)
                st.success("✓ Sample energy dataset loaded!")

    # Data preview
    if st.session_state.data is not None:
        st.markdown("---")
        st.markdown("### 📋 Data Preview")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(st.session_state.data))
        with col2:
            st.metric("Total Columns", len(st.session_state.data.columns))
        with col3:
            st.metric("Missing Values", st.session_state.data.isnull().sum().sum())

        st.dataframe(st.session_state.data.head(10), use_container_width=True)

        st.markdown("### 📌 Column Information")
        col_info = pd.DataFrame({
            'Column': st.session_state.data.columns,
            'Type': st.session_state.data.dtypes,
            'Non-Null Count': st.session_state.data.count(),
            'Null Count': st.session_state.data.isnull().sum()
        })
        st.dataframe(col_info, use_container_width=True)


def render_profiling_section():
    """Render Data Profiling section"""
    if st.session_state.data is None:
        st.warning("⚠️ Please upload or load data first (Home section)")
        return

    df = st.session_state.data
    st.title("📊 Data Profiling")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Numeric Columns", len(df.select_dtypes(include=[np.number]).columns))
    with col4:
        st.metric("Missing Values", df.isnull().sum().sum())

    st.markdown("---")

    # Missing values analysis
    st.markdown("### Missing Values per Column")
    missing_data = pd.DataFrame({
        'Column': df.columns,
        'Missing Count': df.isnull().sum(),
        'Missing %': (df.isnull().sum() / len(df) * 100).round(2)
    }).sort_values('Missing Count', ascending=False)

    missing_data = missing_data[missing_data['Missing Count'] > 0]

    if len(missing_data) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(missing_data, use_container_width=True)
        with col2:
            fig = px.bar(missing_data, x='Column', y='Missing %',
                        title="Missing Values %", color='Missing %',
                        color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("✓ No missing values detected in the dataset!")

    st.markdown("---")

    # Data types
    st.markdown("### Data Types")
    dtype_counts = df.dtypes.value_counts()
    dtype_names = [str(d) for d in dtype_counts.index]
    dtype_vals = [int(v) for v in dtype_counts.values]
    fig = px.pie(values=dtype_vals, names=dtype_names,
                title="Data Type Distribution")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(pd.DataFrame({
            'Data Type': dtype_names,
            'Count': dtype_vals
        }), use_container_width=True)

    st.markdown("---")

    # Descriptive statistics
    st.markdown("### Descriptive Statistics")
    numeric_df = df.select_dtypes(include=[np.number])

    if len(numeric_df.columns) > 0:
        st.dataframe(numeric_df.describe().T, use_container_width=True)
    else:
        st.info("No numeric columns found for statistics")

    st.markdown("---")

    # Correlation heatmap
    st.markdown("### Correlation Heatmap")
    if len(numeric_df.columns) > 1:
        fig, ax = plt.subplots(figsize=(12, 8))
        corr_matrix = numeric_df.corr()
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                   center=0, ax=ax, cbar_kws={'label': 'Correlation'})
        st.pyplot(fig)
    else:
        st.info("Need at least 2 numeric columns for correlation analysis")


def render_analysis_section():
    """Render Analysis Engine section"""
    if st.session_state.data is None:
        st.warning("⚠️ Please upload or load data first (Home section)")
        return

    df = st.session_state.data
    st.title("🔍 Analysis Engine")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_col = st.session_state.date_column

    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Trend Analysis", "Anomaly Detection", "Key Metrics", "Summary Statistics"])

    # Trend Analysis
    with tab1:
        st.markdown("### 📈 Trend Analysis")

        if date_col and len(numeric_cols) > 0:
            selected_cols = st.multiselect(
                "Select columns for trend analysis",
                numeric_cols,
                default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols
            )

            if selected_cols:
                df_sorted = df.sort_values(by=date_col)

                fig = go.Figure()

                for col in selected_cols:
                    fig.add_trace(go.Scatter(
                        x=df_sorted[date_col],
                        y=df_sorted[col],
                        mode='lines+markers',
                        name=col,
                        line=dict(width=2)
                    ))

                fig.update_layout(
                    title="Metric Trends Over Time",
                    xaxis_title="Date",
                    yaxis_title="Value",
                    hovermode='x unified',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need a date column and numeric data for trend analysis")

    # Anomaly Detection
    with tab2:
        st.markdown("### 🚨 Anomaly Detection")

        if len(numeric_cols) > 0:
            selected_col = st.selectbox("Select column for anomaly detection", numeric_cols)

            if selected_col:
                anomalies_iqr, lower_bound, upper_bound = detect_anomalies_iqr(df, selected_col)

                st.markdown(f"**IQR Method Results for {selected_col}:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Lower Bound", f"{lower_bound:.2f}")
                with col2:
                    st.metric("Upper Bound", f"{upper_bound:.2f}")
                with col3:
                    st.metric("Anomalies Found", int(anomalies_iqr.sum()))
                with col4:
                    st.metric("Anomaly %", f"{(anomalies_iqr.sum() / len(df) * 100):.2f}%")

                # Display anomalies table
                if anomalies_iqr.sum() > 0:
                    anomaly_indices = df[anomalies_iqr].index
                    anomaly_data = df.loc[anomaly_indices, [date_col if date_col else df.columns[0], selected_col]].copy()
                    anomaly_data['Type'] = anomaly_data[selected_col].apply(
                        lambda x: 'Above Threshold' if x > upper_bound else 'Below Threshold'
                    )
                    anomaly_data['Deviation'] = abs(anomaly_data[selected_col] - df[selected_col].mean())

                    st.markdown("**Detected Anomalies:**")
                    st.dataframe(anomaly_data.sort_values('Deviation', ascending=False), use_container_width=True)
                else:
                    st.success("✓ No anomalies detected using IQR method")

                # Visualization
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[selected_col],
                    mode='lines',
                    name='Value',
                    line=dict(color='blue', width=2)
                ))

                fig.add_hline(y=upper_bound, line_dash="dash",
                             annotation_text="Upper Bound", line_color="orange")
                fig.add_hline(y=lower_bound, line_dash="dash",
                             annotation_text="Lower Bound", line_color="orange")

                if anomalies_iqr.sum() > 0:
                    fig.add_trace(go.Scatter(
                        x=df[anomalies_iqr].index,
                        y=df[anomalies_iqr][selected_col],
                        mode='markers',
                        name='Anomalies',
                        marker=dict(color='red', size=10, symbol='circle-open', line=dict(width=2))
                    ))

                fig.update_layout(
                    title=f"Anomaly Detection: {selected_col}",
                    xaxis_title="Index",
                    yaxis_title="Value",
                    height=500,
                    hovermode='closest'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns found")

    # Key Metrics
    with tab3:
        st.markdown("### 📌 Key Metrics")

        if len(numeric_cols) > 0:
            cols = st.columns(len(numeric_cols) if len(numeric_cols) <= 4 else 4)

            for idx, col in enumerate(numeric_cols[:len(cols)]):
                with cols[idx % len(cols)]:
                    st.metric(f"Max {col}", f"{df[col].max():.2f}")
                    st.metric(f"Min {col}", f"{df[col].min():.2f}")
                    st.metric(f"Avg {col}", f"{df[col].mean():.2f}")
                    st.metric(f"Std {col}", f"{df[col].std():.2f}")
        else:
            st.info("No numeric columns found")

    # Summary Statistics
    with tab4:
        st.markdown("### 📊 Summary Statistics")

        if date_col:
            df_temp = df.sort_values(by=date_col)

            # Monthly aggregation
            try:
                df_temp['YearMonth'] = pd.to_datetime(df_temp[date_col]).dt.to_period('M')

                monthly_stats = df_temp.groupby('YearMonth')[numeric_cols].mean()

                if len(numeric_cols) > 0:
                    st.markdown("**Monthly Averages:**")
                    display_stats = monthly_stats.copy()
                    display_stats.index = display_stats.index.astype(str)
                    st.dataframe(display_stats, use_container_width=True)

                    # Monthly trend chart
                    plot_df = monthly_stats.reset_index()
                    plot_df['YearMonth'] = plot_df['YearMonth'].astype(str)
                    fig = px.line(plot_df,
                                 x='YearMonth', y=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols,
                                 title="Monthly Trends",
                                 markers=True)
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("Could not create monthly aggregations")
        else:
            st.info("Date column needed for time-based aggregations")


def render_insights_section():
    """Render Insights & Recommendations section"""
    if st.session_state.data is None:
        st.warning("⚠️ Please upload or load data first (Home section)")
        return

    df = st.session_state.data
    st.title("💡 Insights & Recommendations")

    date_col = st.session_state.date_column

    # Generate insights
    insights = generate_insights(df, date_col)
    recommendations = generate_recommendations(df, insights, date_col)

    # Display insights
    st.markdown("### Auto-Generated Insights")

    if insights:
        for idx, insight in enumerate(insights[:5]):
            with st.expander(f"📌 Insight {idx + 1}: {insight.get('column', insight.get('col1', 'Analysis'))}",
                           expanded=(idx == 0)):

                if insight['type'] == 'trend':
                    st.markdown(f"""
                    **Column:** {insight['column']}
                    **Direction:** {insight['direction'].upper()}
                    **Strength:** {insight['strength']}
                    **Priority:** {insight['priority']}
                    """)

                elif insight['type'] == 'volatility':
                    st.markdown(f"""
                    **Column:** {insight['column']}
                    **Coefficient of Variation:** {insight['cv']}
                    **Assessment:** High variability detected
                    **Priority:** {insight['priority']}
                    """)

                elif insight['type'] == 'correlation':
                    st.markdown(f"""
                    **Columns:** {insight['col1']} ↔ {insight['col2']}
                    **Correlation Coefficient:** {insight['strength']}
                    **Strength:** Strong
                    **Priority:** {insight['priority']}
                    """)
    else:
        st.info("No significant insights detected in the data")

    st.markdown("---")

    # Display recommendations
    st.markdown("### 🎯 Business Recommendations")

    if recommendations:
        for idx, rec in enumerate(recommendations):
            priority = rec['priority']
            badge_class = f"badge badge-{priority.lower()}"

            st.markdown(f"""
            <div class="insight-{priority.lower()}">
                <span class="{badge_class}">{priority}</span>
                <strong>{rec['text']}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recommendations at this time")

    st.markdown("---")

    # Summary section
    st.markdown("### 📋 Analysis Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        st.metric("Numeric Columns", len(numeric_cols))

    with col2:
        total_anomalies = 0
        for col in numeric_cols:
            try:
                anomalies, _, _ = detect_anomalies_iqr(df, col)
                total_anomalies += anomalies.sum()
            except:
                pass
        st.metric("Total Anomalies", int(total_anomalies))

    with col3:
        st.metric("Data Quality Score", f"{100 - (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100):.1f}%")


def render_visualizations_section():
    """Render Visualizations Dashboard section"""
    if st.session_state.data is None:
        st.warning("⚠️ Please upload or load data first (Home section)")
        return

    df = st.session_state.data
    st.title("📈 Visualizations Dashboard")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_col = st.session_state.date_column

    # Column selection
    selected_cols = st.multiselect(
        "Select columns to visualize",
        numeric_cols,
        default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols
    )

    if not selected_cols:
        st.warning("Please select at least one column")
        return

    col1, col2 = st.columns(2)

    # Trend Chart
    with col1:
        if date_col:
            df_sorted = df.sort_values(by=date_col)
            fig = px.line(df_sorted, x=date_col, y=selected_cols[:2],
                         title="Trend Chart",
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Date column required for trend chart")

    # Distribution Chart
    with col2:
        if len(selected_cols) > 0:
            fig = px.histogram(df, x=selected_cols[0],
                             title=f"Distribution: {selected_cols[0]}",
                             nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    # Comparison Chart
    st.markdown("---")
    if len(selected_cols) >= 2:
        fig = px.bar(df[selected_cols].describe().T,
                    x=df[selected_cols].describe().T.index,
                    y=['mean', '50%'],
                    title="Comparison Chart: Mean vs Median",
                    labels={'value': 'Value', 'variable': 'Statistic'})
        st.plotly_chart(fig, use_container_width=True)

    # Anomaly Highlight Chart
    st.markdown("---")
    st.markdown("### Anomaly Highlight Chart")
    col_for_anomaly = st.selectbox("Select column for anomaly highlighting", numeric_cols)

    if col_for_anomaly:
        anomalies, lower, upper = detect_anomalies_iqr(df, col_for_anomaly)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col_for_anomaly],
            mode='markers',
            name='Normal',
            marker=dict(color='blue', size=6)
        ))

        if anomalies.sum() > 0:
            fig.add_trace(go.Scatter(
                x=df[anomalies].index,
                y=df[anomalies][col_for_anomaly],
                mode='markers',
                name='Anomalies',
                marker=dict(color='red', size=10, symbol='diamond')
            ))

        fig.add_hline(y=upper, line_dash="dash", line_color="orange",
                     annotation_text="Upper Bound")
        fig.add_hline(y=lower, line_dash="dash", line_color="orange",
                     annotation_text="Lower Bound")

        fig.update_layout(
            title=f"Anomaly Detection: {col_for_anomaly}",
            xaxis_title="Index",
            yaxis_title="Value",
            height=500,
            hovermode='closest'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap
    st.markdown("---")
    st.markdown("### Correlation Heatmap")
    if len(selected_cols) > 1:
        fig, ax = plt.subplots(figsize=(10, 8))
        corr = df[selected_cols].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0, ax=ax)
        st.pyplot(fig)
    else:
        st.info("Select at least 2 columns for heatmap")


def render_export_section():
    """Render Export/Report section"""
    if st.session_state.data is None:
        st.warning("⚠️ Please upload or load data first (Home section)")
        return

    df = st.session_state.data
    st.title("📥 Export & Report")

    # Generate report
    date_col = st.session_state.date_column
    insights = generate_insights(df, date_col)
    recommendations = generate_recommendations(df, insights, date_col)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    report = f"""
================================================================================
                    AI-PASS ANALYSIS STUDIO - DATA REPORT
================================================================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
1. DATASET OVERVIEW
================================================================================

Total Rows: {len(df)}
Total Columns: {len(df.columns)}
Date Range: {df[date_col].min() if date_col and date_col in df.columns else 'N/A'} to {df[date_col].max() if date_col and date_col in df.columns else 'N/A'}
Missing Values: {df.isnull().sum().sum()} ({(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100):.2f}%)
Data Quality Score: {100 - (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100):.1f}%

Columns: {', '.join(df.columns)}

================================================================================
2. DESCRIPTIVE STATISTICS
================================================================================
"""

    if len(numeric_cols) > 0:
        stats_df = df[numeric_cols].describe()
        report += stats_df.to_string()

    report += f"""

================================================================================
3. KEY FINDINGS
================================================================================

"""

    # Anomalies
    total_anomalies = 0
    for col in numeric_cols:
        try:
            anomalies, _, _ = detect_anomalies_iqr(df, col)
            total_anomalies += anomalies.sum()
        except:
            pass

    report += f"Total Anomalies Detected: {total_anomalies}\n\n"

    if total_anomalies > 0:
        report += "Anomaly Details:\n"
        for col in numeric_cols:
            try:
                anomalies, lower, upper = detect_anomalies_iqr(df, col)
                if anomalies.sum() > 0:
                    report += f"  - {col}: {anomalies.sum()} anomalies (Bounds: {lower:.2f} to {upper:.2f})\n"
            except:
                pass

    report += f"""

================================================================================
4. INSIGHTS
================================================================================

"""

    if insights:
        for idx, insight in enumerate(insights[:5], 1):
            if insight['type'] == 'trend':
                report += f"{idx}. Trend: {insight['column']} is trending {insight['direction']} by {insight['strength']} (Priority: {insight['priority']})\n"
            elif insight['type'] == 'volatility':
                report += f"{idx}. Volatility: {insight['column']} shows high variability (CV: {insight['cv']}) (Priority: {insight['priority']})\n"
            elif insight['type'] == 'correlation':
                report += f"{idx}. Correlation: {insight['col1']} and {insight['col2']} are correlated at {insight['strength']} (Priority: {insight['priority']})\n"
    else:
        report += "No significant insights detected.\n"

    report += f"""

================================================================================
5. RECOMMENDATIONS
================================================================================

"""

    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            report += f"{idx}. [{rec['priority']}] {rec['text']}\n\n"
    else:
        report += "No recommendations at this time.\n"

    report += f"""
================================================================================
                            END OF REPORT
================================================================================
Built by Uday | AI-Pass Analysis Studio | 2026
"""

    # Display report
    st.markdown("### 📄 Generated Report Preview")
    st.text(report)

    # Download button
    st.markdown("---")
    st.download_button(
        label="📥 Download Report as TXT",
        data=report,
        file_name=f"AI-Pass-Report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )

    # CSV Export
    st.markdown("---")
    st.markdown("### 📊 Export Data")

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="📥 Download Data as CSV",
        data=csv_data,
        file_name=f"AI-Pass-Data-{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )


# Main app
def main():
    # Sidebar navigation
    st.sidebar.title("📊 AI-Pass Analysis Studio")
    st.sidebar.markdown("---")

    section = st.sidebar.radio(
        "Select Section",
        ["Home / Upload", "Data Profiling", "Analysis Engine",
         "Insights & Recommendations", "Visualizations", "Export & Report"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📌 Quick Guide
    1. **Home**: Upload CSV or load sample data
    2. **Profiling**: Analyze data structure & quality
    3. **Analysis**: Trends, anomalies, key metrics
    4. **Insights**: Auto-generated findings & recommendations
    5. **Visualizations**: Interactive charts & dashboards
    6. **Export**: Generate reports & download data
    """)

    # Render sections
    if section == "Home / Upload":
        render_home_section()
    elif section == "Data Profiling":
        render_profiling_section()
    elif section == "Analysis Engine":
        render_analysis_section()
    elif section == "Insights & Recommendations":
        render_insights_section()
    elif section == "Visualizations":
        render_visualizations_section()
    elif section == "Export & Report":
        render_export_section()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
    <p>Built by Uday | AI-Pass Analysis Studio | 2026</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
