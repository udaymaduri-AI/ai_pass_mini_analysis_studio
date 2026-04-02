import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import warnings

warnings.filterwarnings('ignore')

# ------------------ FIX: JSON SAFE CONVERSION ------------------
def make_json_safe(df):
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(float)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
        else:
            df[col] = df[col].astype(str)
    return df

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="AI-Pass Analysis Studio",
    layout="wide"
)

# ------------------ SESSION ------------------
if "data" not in st.session_state:
    st.session_state.data = None

# ------------------ HOME ------------------
def render_home():
    st.title("📊 AI-Pass Analysis Studio")

    uploaded = st.file_uploader("Upload CSV", type="csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        df = df.convert_dtypes()
        df = make_json_safe(df)

        st.session_state.data = df
        st.success("Uploaded successfully!")

    if st.session_state.data is not None:
        df = st.session_state.data
        st.dataframe(df.head())

# ------------------ PROFILING ------------------
def render_profiling():
    df = st.session_state.data
    if df is None:
        st.warning("Upload data first")
        return

    st.title("📊 Data Profiling")

    # Missing values
    missing_data = pd.DataFrame({
        'Column': df.columns.astype(str),
        'Missing Count': df.isnull().sum().astype(int),
        'Missing %': (df.isnull().sum() / len(df) * 100).astype(float)
    }).reset_index(drop=True)

    missing_data = make_json_safe(missing_data)

    fig = px.bar(
        missing_data,
        x='Column',
        y='Missing %',
        title="Missing Values"
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------ ANALYSIS ------------------
def render_analysis():
    df = st.session_state.data
    if df is None:
        st.warning("Upload data first")
        return

    st.title("📈 Analysis")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) >= 1:
        col = st.selectbox("Select column", numeric_cols)

        fig = px.histogram(df, x=col)
        st.plotly_chart(fig, use_container_width=True)

# ------------------ EXPORT ------------------
def render_export():
    df = st.session_state.data
    if df is None:
        st.warning("Upload data first")
        return

    st.title("📥 Export")

    csv = df.to_csv(index=False)

    st.download_button(
        "Download CSV",
        csv,
        file_name="data.csv",
        mime="text/csv"
    )

# ------------------ MAIN ------------------
def main():
    menu = st.sidebar.radio(
        "Navigation",
        ["Home", "Profiling", "Analysis", "Export"]
    )

    if menu == "Home":
        render_home()
    elif menu == "Profiling":
        render_profiling()
    elif menu == "Analysis":
        render_analysis()
    elif menu == "Export":
        render_export()

if __name__ == "__main__":
    main()
