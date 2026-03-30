import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import os

st.set_page_config(
    page_title="Employee Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Global */
body {
    background-color: #0e1117;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.kpi-title {
    font-size: 14px;
    color: #9ca3af;
}

.kpi-value {
    font-size: 28px;
    font-weight: bold;
    color: #22c55e;
}

/* Section Headers */
.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
}

/* Sidebar */
.css-1d391kg {
    background-color: #111827;
}

/* Table */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1234")
DB_NAME = os.getenv("DB_NAME", "etl_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin123")
TABLE_NAME = os.getenv("TABLE_NAME", "employees")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@st.cache_data(ttl=60)
def load_data():
    engine = create_engine(DATABASE_URL)
    return pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)

df = load_data()

st.sidebar.title("📊 Dashboard")
page = st.sidebar.radio("Navigate", ["Overview", "Analytics", "Data Explorer"])

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

search = st.sidebar.text_input("Search Name")

team_filter = st.sidebar.multiselect("Team", df["team"].dropna().unique())
gender_filter = st.sidebar.multiselect("Gender", df["gender"].dropna().unique())

salary_min, salary_max = int(df.salary.min()), int(df.salary.max())
salary_range = st.sidebar.slider("Salary Range", salary_min, salary_max, (salary_min, salary_max))

# Apply filters
filtered = df.copy()

if search:
    filtered = filtered[filtered["first_name"].str.contains(search, case=False, na=False)]

if team_filter:
    filtered = filtered[filtered["team"].isin(team_filter)]

if gender_filter:
    filtered = filtered[filtered["gender"].isin(gender_filter)]

filtered = filtered[
    (filtered["salary"] >= salary_range[0]) &
    (filtered["salary"] <= salary_range[1])
]

st.markdown("""
<h1 style='text-align: center;'>🚀 Employee Analytics Platform</h1>
<p style='text-align: center; color: gray;'>Modern Data Dashboard powered by Airflow + PostgreSQL</p>
""", unsafe_allow_html=True)

if page == "Overview":

    col1, col2, col3, col4 = st.columns(4)

    def kpi(title, value):
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        kpi("Total Employees", len(filtered))
    with col2:
        kpi("Avg Salary", f"${filtered.salary.mean():,.0f}")
    with col3:
        kpi("Total Compensation", f"${filtered.total_compensation.sum():,.0f}")
    with col4:
        kpi("Managers", filtered.senior_management.sum())

    st.markdown("<div class='section-title'>📊 Insights</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(filtered, x="salary", nbins=30, title="Salary Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        team_avg = filtered.groupby("team")["salary"].mean().reset_index()
        fig = px.bar(team_avg, x="team", y="salary", title="Avg Salary by Team")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Analytics":

    st.markdown("### 📈 Advanced Analytics")

    tab1, tab2, tab3 = st.tabs(["Salary", "Bonus", "Management"])

    with tab1:
        fig = px.box(filtered, x="team", y="salary", title="Salary Spread by Team")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.scatter(
            filtered,
            x="salary",
            y="bonus_amount",
            color="team",
            title="Salary vs Bonus"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        mgmt = filtered["senior_management"].value_counts().reset_index(name="count").rename(columns={"senior_management": "status"})
        fig = px.pie(mgmt, names="status", values="count", title="Management Ratio")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Data Explorer":

    st.markdown("### 📄 Data Explorer")

    with st.expander("⚙️ Customize Columns"):
        columns = st.multiselect("Select columns", df.columns, default=df.columns)

    display_df = filtered[columns]

    st.dataframe(display_df, use_container_width=True)

    st.download_button(
        "⬇ Download CSV",
        display_df.to_csv(index=False),
        file_name="filtered_data.csv"
    )