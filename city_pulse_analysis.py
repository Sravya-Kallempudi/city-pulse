#  CITY PULSE - Complete Analysis Script
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import warnings
warnings.filterwarnings('ignore')

engine = create_engine(URL.create(
    drivername = "postgresql+psycopg2",
    username   = "postgres",
    password   = "sravya@123",  
    host       = "localhost",
    port       = 5432,
    database   = "city_pulse"
))

print("Connecting to database...")


print("Loading data...")

traffic = pd.read_sql('SELECT * FROM traffic', engine)
air     = pd.read_sql('SELECT * FROM air_quality', engine)
weather = pd.read_sql('SELECT * FROM weather', engine)
crime   = pd.read_sql('SELECT * FROM crime', engine)

print(f"  Traffic rows    : {len(traffic):,}")
print(f"  Air quality rows: {len(air):,}")
print(f"  Weather rows    : {len(weather):,}")
print(f"  Crime rows      : {len(crime):,}")


print("Cleaning data...")

traffic.columns = traffic.columns.str.strip()
traffic['DateTime'] = pd.to_datetime(traffic['DateTime'])
traffic['hour']     = traffic['DateTime'].dt.hour
traffic['day_name'] = traffic['DateTime'].dt.day_name()

air.columns = air.columns.str.strip()
air['timestamp'] = pd.to_datetime(air['timestamp'])
air['hour']      = air['timestamp'].dt.hour
air['date']      = air['timestamp'].dt.date

weather.columns = weather.columns.str.strip()

weather = weather.rename(columns={
    'time'                      : 'time',
    'temperature_2m (°C)'       : 'temperature',
    'precipitation (mm)'        : 'precipitation',
    'wind_speed_10m (km/h)'     : 'wind_speed',
    'relative_humidity_2m (%)'  : 'humidity'
})
weather['time'] = pd.to_datetime(weather['time'])
weather['hour'] = weather['time'].dt.hour
weather['month'] = weather['time'].dt.month

crime.columns = crime.columns.str.strip()

crime.columns = [c.replace('\ufeff', '') for c in crime.columns]
crime['Date of Occurrence'] = pd.to_datetime(
    crime['Date of Occurrence'], format='%d-%m-%Y %H:%M', errors='coerce'
)
crime['hour'] = crime['Date of Occurrence'].dt.hour
crime['month'] = crime['Date of Occurrence'].dt.month

print("Data ready!")

print("Running analysis...")

traffic_hourly = (
    traffic.groupby('hour')['Vehicles']
    .mean()
    .reset_index()
    .rename(columns={'Vehicles': 'avg_vehicles'})
)
peak_hour = traffic_hourly.loc[traffic_hourly['avg_vehicles'].idxmax(), 'hour']
print(f"  Peak traffic hour: {int(peak_hour)}:00")

busiest_junction = (
    traffic.groupby('Junction')['Vehicles']
    .mean()
    .idxmax()
)
print(f"  Busiest junction: Junction {busiest_junction}")

aqi_by_city = (
    air.groupby('city')['aqi']
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
most_polluted = aqi_by_city.iloc[0]['city']
print(f"  Most polluted city: {most_polluted} (AQI: {aqi_by_city.iloc[0]['aqi']:.0f})")

aqi_hourly = air.groupby('hour')['aqi'].mean().reset_index()

weather_monthly = (
    weather.groupby('month')[['temperature', 'precipitation', 'humidity']]
    .mean()
    .reset_index()
)

crime_by_type = (
    crime['Crime Description']
    .value_counts()
    .head(8)
    .reset_index()
)
crime_by_type.columns = ['Crime Type', 'Count']

crime_hourly = (
    crime.groupby('hour')
    .size()
    .reset_index(name='count')
)

crime_by_city = (
    crime['City']
    .value_counts()
    .head(8)
    .reset_index()
)
crime_by_city.columns = ['City', 'Count']

print("Analysis complete!")

print("Building dashboard...")

plt.style.use('seaborn-v0_8-whitegrid')
colors = {
    'traffic' : '#185FA5',
    'air'     : '#0F6E56',
    'weather' : '#854F0B',
    'crime'   : '#993C1D',
    'accent'  : '#534AB7'
}

fig = plt.figure(figsize=(20, 22))
fig.patch.set_facecolor('#F8F9FA')
gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.35)

ax1 = fig.add_subplot(gs[0, 0])
bars = ax1.bar(
    traffic_hourly['hour'], traffic_hourly['avg_vehicles'],
    color=colors['traffic'], alpha=0.85, width=0.7
)
bars[int(peak_hour)].set_color('#E24B4A')
ax1.set_title('Average Vehicles per Hour', fontsize=13, fontweight='bold', pad=10)
ax1.set_xlabel('Hour of Day')
ax1.set_ylabel('Avg Vehicles')
ax1.set_xticks(range(0, 24, 2))
ax1.annotate(f'Peak: {int(peak_hour)}:00',
    xy=(peak_hour, traffic_hourly['avg_vehicles'].max()),
    xytext=(peak_hour + 1.5, traffic_hourly['avg_vehicles'].max() * 0.97),
    fontsize=9, color='#E24B4A', fontweight='bold')

ax2 = fig.add_subplot(gs[0, 1])
junc_avg = traffic.groupby('Junction')['Vehicles'].mean()
ax2.bar(
    [f'Junction {j}' for j in junc_avg.index], junc_avg.values,
    color=colors['traffic'], alpha=0.85
)
ax2.set_title('Average Vehicles by Junction', fontsize=13, fontweight='bold', pad=10)
ax2.set_ylabel('Avg Vehicles')

ax3 = fig.add_subplot(gs[1, 0])
bars3 = ax3.barh(
    aqi_by_city['city'], aqi_by_city['aqi'],
    color=colors['air'], alpha=0.85
)
ax3.invert_yaxis()
ax3.set_title('Top 10 Cities by Average AQI', fontsize=13, fontweight='bold', pad=10)
ax3.set_xlabel('Average AQI')
for bar, val in zip(bars3, aqi_by_city['aqi']):
    ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f'{val:.0f}', va='center', fontsize=9)

ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(
    aqi_hourly['hour'], aqi_hourly['aqi'],
    color=colors['air'], linewidth=2.5, marker='o', markersize=4
)
ax4.fill_between(aqi_hourly['hour'], aqi_hourly['aqi'],
                 alpha=0.15, color=colors['air'])
ax4.set_title('Average AQI by Hour of Day', fontsize=13, fontweight='bold', pad=10)
ax4.set_xlabel('Hour of Day')
ax4.set_ylabel('Average AQI')
ax4.set_xticks(range(0, 24, 2))

ax5 = fig.add_subplot(gs[2, 0])
month_names = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']
ax5.plot(
    weather_monthly['month'], weather_monthly['temperature'],
    color=colors['weather'], linewidth=2.5, marker='s', markersize=5
)
ax5.fill_between(weather_monthly['month'], weather_monthly['temperature'],
                 alpha=0.15, color=colors['weather'])
ax5.set_title('Monthly Average Temperature (Hyderabad)', fontsize=13, fontweight='bold', pad=10)
ax5.set_xlabel('Month')
ax5.set_ylabel('Temperature (°C)')
ax5.set_xticks(weather_monthly['month'])
ax5.set_xticklabels([month_names[m-1] for m in weather_monthly['month']], rotation=45)

ax6 = fig.add_subplot(gs[2, 1])
ax6.bar(
    weather_monthly['month'], weather_monthly['precipitation'],
    color=colors['accent'], alpha=0.85, width=0.6
)
ax6.set_title('Monthly Average Precipitation (Hyderabad)', fontsize=13, fontweight='bold', pad=10)
ax6.set_xlabel('Month')
ax6.set_ylabel('Precipitation (mm)')
ax6.set_xticks(weather_monthly['month'])
ax6.set_xticklabels([month_names[m-1] for m in weather_monthly['month']], rotation=45)

ax7 = fig.add_subplot(gs[3, 0])
ax7.barh(
    crime_by_type['Crime Type'], crime_by_type['Count'],
    color=colors['crime'], alpha=0.85
)
ax7.invert_yaxis()
ax7.set_title('Top 8 Crime Types (India)', fontsize=13, fontweight='bold', pad=10)
ax7.set_xlabel('Number of Incidents')

ax8 = fig.add_subplot(gs[3, 1])
ax8.plot(
    crime_hourly['hour'], crime_hourly['count'],
    color=colors['crime'], linewidth=2.5, marker='o', markersize=4
)
ax8.fill_between(crime_hourly['hour'], crime_hourly['count'],
                 alpha=0.15, color=colors['crime'])
ax8.set_title('Crime Incidents by Hour of Day', fontsize=13, fontweight='bold', pad=10)
ax8.set_xlabel('Hour of Day')
ax8.set_ylabel('Number of Incidents')
ax8.set_xticks(range(0, 24, 2))

fig.suptitle(
    'CITY PULSE — Urban Analytics Dashboard',
    fontsize=20, fontweight='bold', y=0.98,
    color='#1a1a2e'
)

plt.savefig('city_pulse_dashboard.png', dpi=150,
            bbox_inches='tight', facecolor='#F8F9FA')
print("Dashboard saved as city_pulse_dashboard.png")
plt.show()

print("\n" + "="*55)
print("  CITY PULSE — KEY INSIGHTS")
print("="*55)
print(f"\n TRAFFIC")
print(f"  Peak traffic hour     : {int(peak_hour)}:00")
print(f"  Busiest junction      : Junction {busiest_junction}")
print(f"  Total records         : {len(traffic):,}")

print(f"\n AIR QUALITY")
print(f"  Most polluted city    : {most_polluted}")
print(f"  Cities analysed       : {air['city'].nunique()}")
print(f"  Avg AQI overall       : {air['aqi'].mean():.1f}")

print(f"\n WEATHER (Hyderabad 2023)")
print(f"  Avg temperature       : {weather['temperature'].mean():.1f} °C")
print(f"  Max temperature       : {weather['temperature'].max():.1f} °C")
print(f"  Total precipitation   : {weather['precipitation'].sum():.0f} mm")

print(f"\n CRIME (India)")
print(f"  Total incidents       : {len(crime):,}")
print(f"  Cities covered        : {crime['City'].nunique()}")
top_crime = crime_by_type.iloc[0]['Crime Type']
print(f"  Most common crime     : {top_crime}")
print("="*55)