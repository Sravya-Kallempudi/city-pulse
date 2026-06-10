#  CITY PULSE — Streamlit Web App
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import warnings
warnings.filterwarnings("ignore")

# Global chart theme
pio.templates["city_pulse"] = go.layout.Template(
    layout=go.Layout(
        font=dict(color="#1A1A2E", size=12),
        xaxis=dict(tickfont=dict(color="#1A1A2E", size=11), title_font=dict(color="#1A1A2E", size=12)),
        yaxis=dict(tickfont=dict(color="#1A1A2E", size=11), title_font=dict(color="#1A1A2E", size=12)),
        title_font=dict(color="#1A1A2E", size=14),
    )
)
pio.templates.default = "plotly_white+city_pulse"

# Page config
st.set_page_config(
    page_title="City Pulse — Urban Analytics",
    page_icon="🏙️",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #F2F4F8; }
    .block-container { padding-top: 1rem; }
    h1 { color: #1A1A2E; font-size: 2.2rem !important; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #185FA5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .section-header {
        color: #185FA5;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #185FA5;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Traffic
    traffic = pd.read_csv('traffic.csv')
    traffic['DateTime'] = pd.to_datetime(traffic['DateTime'])
    traffic['Hour'] = traffic['DateTime'].dt.hour
    traffic['Day'] = traffic['DateTime'].dt.day_name()

    # Air Quality
    air = pd.read_csv('good_air_quality.csv')
    air['timestamp'] = pd.to_datetime(air['timestamp'])
    air['Hour'] = air['timestamp'].dt.hour

    # Weather 
    weather = pd.read_csv('weather.csv', skiprows=3)
    weather.columns = ['time', 'temperature', 'precipitation', 'wind_speed', 'humidity']
    weather['time'] = pd.to_datetime(weather['time'])
    weather['Month'] = weather['time'].dt.month
    weather['Month_Name'] = weather['time'].dt.strftime('%b')

    # Crime
    crime = pd.read_csv('crime_dataset_india.csv', encoding='utf-8-sig')
    crime.columns = crime.columns.str.strip()
    crime['Date of Occurrence'] = pd.to_datetime(
        crime['Date of Occurrence'], format='%d-%m-%Y %H:%M', errors='coerce'
    )
    crime['Hour'] = crime['Date of Occurrence'].dt.hour

    return traffic, air, weather, crime

traffic, air, weather, crime = load_data()

# Header
st.markdown("# 🏙️ City Pulse — Urban Analytics Dashboard")
st.markdown("*A multi-domain analytics platform covering traffic, air quality, weather and crime*")
st.markdown("---")

# Sidebar Filters
with st.sidebar:
    st.markdown("## 🔧 Filters")

    all_cities = sorted(air['city'].unique().tolist())
    selected_city = st.selectbox("🌆 Select City (Air Quality)", ["All Cities"] + all_cities)

    junctions = sorted(traffic['Junction'].unique().tolist())
    selected_junction = st.multiselect("🚗 Select Junction", junctions, default=junctions)

    years = sorted(traffic['DateTime'].dt.year.unique().tolist())
    selected_year = st.selectbox("📅 Select Year (Traffic)", ["All Years"] + [str(y) for y in years])

    crime_cities = sorted(crime['City'].unique().tolist())
    selected_crime_city = st.selectbox("🚨 Select City (Crime)", ["All Cities"] + crime_cities)

    st.markdown("---")
    st.markdown("**Built by Sravya**")
    st.markdown("Python | PostgreSQL | Power BI | Streamlit")

# Apply Filters
traffic_filtered = traffic[traffic['Junction'].isin(selected_junction)]
if selected_year != "All Years":
    traffic_filtered = traffic_filtered[traffic_filtered['DateTime'].dt.year == int(selected_year)]

air_filtered = air if selected_city == "All Cities" else air[air['city'] == selected_city]
crime_filtered = crime if selected_crime_city == "All Cities" else crime[crime['City'] == selected_crime_city]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🚗 Total Traffic Records", f"{len(traffic_filtered):,}")
with col2:
    st.metric("🌫️ Average AQI", f"{air_filtered['aqi'].mean():.0f}")
with col3:
    st.metric("🌡️ Avg Temperature", f"{weather['temperature'].mean():.1f} °C")
with col4:
    st.metric("🚨 Total Crime Incidents", f"{len(crime_filtered):,}")

st.markdown("---")


st.markdown('<p class="section-header">🚗 Traffic Analysis</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    hourly = traffic_filtered.groupby('Hour')['Vehicles'].mean().reset_index()
    peak = hourly.loc[hourly['Vehicles'].idxmax(), 'Hour']
    colors = ['#E24B4A' if h == peak else '#185FA5' for h in hourly['Hour']]
    fig = go.Figure(go.Bar(
        x=hourly['Hour'], y=hourly['Vehicles'],
        marker_color=colors
    ))
    fig.update_layout(
        title=f'Average Vehicles by Hour (Peak: {int(peak)}:00)',
        xaxis_title='Hour of Day', yaxis_title='Avg Vehicles', font=dict(color='#1A1A2E', size=12),
        plot_bgcolor='white', paper_bgcolor='white', height=320
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    junc_avg = traffic_filtered.groupby('Junction')['Vehicles'].mean().reset_index()
    fig2 = px.bar(
        junc_avg, x='Junction', y='Vehicles',
        title='Average Vehicles by Junction',
        color_discrete_sequence=['#185FA5']
    )
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown('<p class="section-header">🌫️ Air Quality Analysis</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    aqi_city = air_filtered.groupby('city')['aqi'].mean().sort_values(ascending=False).head(10).reset_index()
    fig3 = px.bar(
        aqi_city, x='aqi', y='city', orientation='h',
        title='Top 10 Cities by Average AQI',
        color_discrete_sequence=['#0F6E56']
    )
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12), yaxis={'categoryorder': 'total ascending', 'tickfont': {'color': '#1A1A2E'}})
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    aqi_hour = air_filtered.groupby('Hour')['aqi'].mean().reset_index()
    fig4 = px.line(
        aqi_hour, x='Hour', y='aqi',
        title='Average AQI by Hour of Day',
        color_discrete_sequence=['#0F6E56'],
        markers=True
    )
    fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12))
    fig4.update_traces(fill='tozeroy', fillcolor='rgba(15,110,86,0.1)')
    st.plotly_chart(fig4, use_container_width=True)


st.markdown('<p class="section-header">🌤️ Weather Analysis (Hyderabad 2023)</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
weather_monthly = weather.groupby(['Month', 'Month_Name'])[['temperature','precipitation','humidity']].mean().reset_index()
weather_monthly = weather_monthly.sort_values('Month')

with col1:
    fig5 = px.line(
        weather_monthly, x='Month_Name', y='temperature',
        title='Monthly Average Temperature (°C)',
        color_discrete_sequence=['#854F0B'],
        markers=True, category_orders={'Month_Name': month_order}
    )
    fig5.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12))
    fig5.update_traces(fill='tozeroy', fillcolor='rgba(133,79,11,0.1)')
    st.plotly_chart(fig5, use_container_width=True)

with col2:
    fig6 = px.bar(
        weather_monthly, x='Month_Name', y='precipitation',
        title='Monthly Average Precipitation (mm)',
        color_discrete_sequence=['#534AB7'],
        category_orders={'Month_Name': month_order}
    )
    fig6.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12))
    st.plotly_chart(fig6, use_container_width=True)


st.markdown('<p class="section-header">🚨 Crime Analysis (India)</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    crime_type = crime_filtered['Crime Description'].value_counts().head(8).reset_index()
    crime_type.columns = ['Crime Type', 'Count']
    fig7 = px.bar(
        crime_type, x='Count', y='Crime Type', orientation='h',
        title='Top 8 Crime Types',
        color_discrete_sequence=['#993C1D']
    )
    fig7.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12), yaxis={'categoryorder': 'total ascending', 'tickfont': {'color': '#1A1A2E'}})
    st.plotly_chart(fig7, use_container_width=True)

with col2:
    crime_hour = crime_filtered.groupby('Hour').size().reset_index(name='Count')
    fig8 = px.line(
        crime_hour, x='Hour', y='Count',
        title='Crime Incidents by Hour of Day',
        color_discrete_sequence=['#993C1D'],
        markers=True
    )
    fig8.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320, font=dict(color='#1A1A2E', size=12))
    fig8.update_traces(fill='tozeroy', fillcolor='rgba(153,60,29,0.1)')
    st.plotly_chart(fig8, use_container_width=True)

#Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#888; font-size:13px'>
    🏙️ City Pulse — Built with Python, PostgreSQL, Power BI & Streamlit &nbsp;|&nbsp; By Sravya
</div>
""", unsafe_allow_html=True)
