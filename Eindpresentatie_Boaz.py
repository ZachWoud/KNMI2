import requests
import pandas as pd
import streamlit as st
from folium.features import CustomIcon
from streamlit_folium import st_folium
import folium
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

# Custom CSS for weather broadcast styling
st.markdown(
    """
    <style>
    /* Global text and header colors set to #fdcb50 */
    body, h1, h2, h3, h4, h5, h6, .css-18e3th9, .css-1d391kg {
        color: #fdcb50 !important;
    }
    /* Slider styling: white background with border #fdcb50 */
    [data-baseweb="slider"] > div {
        background-color: white !important;
        border: 1px solid #fdcb50 !important;
        border-radius: 4px;
    }
    [data-baseweb="slider"] input[type="range"] {
        accent-color: #fdcb50 !important;
    }
    /* Button styling: white background, #fdcb50 border and text */
    div.stButton > button {
        background-color: white !important;
        color: #fdcb50 !important;
        border: 1px solid #fdcb50 !important;
        border-radius: 4px;
    }
    /* Select box styling: white background with border #fdcb50 */
    [data-baseweb="select"] > div {
        background-color: white !important;
        border: 1px solid #fdcb50 !important;
        border-radius: 4px;
        color: #fdcb50 !important;
    }
    [data-baseweb="select"] > div > div {
        color: #fdcb50 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# API Configuration
api_key = 'd5184c3b4e'
cities = [
    'Amsterdam', 'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht',
    'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam', 'Zwolle'
]

@st.cache_data
def fetch_weather_data():
    liveweer, wk_verw, uur_verw, api_data = [], [], [], []
    for city in cities:
        api_url = f'https://weerlive.nl/api/weerlive_api_v2.php?key={api_key}&locatie={city}'
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if 'liveweer' in data:
                liveweer.extend(data['liveweer'])
            if 'wk_verw' in data:
                for entry in data['wk_verw']:
                    entry['plaats'] = city
                wk_verw.extend(data['wk_verw'])
            if 'uur_verw' in data:
                for entry in data['uur_verw']:
                    entry['plaats'] = city
                uur_verw.extend(data['uur_verw'])
            if 'api_data' in data:
                api_data.extend(data['api'])
        else:
            print(f"Error fetching data for {city}: {response.status_code}")
    return liveweer, wk_verw, uur_verw, api_data

liveweer, wk_verw, uur_verw, api_data = fetch_weather_data()

df_liveweer = pd.DataFrame(liveweer)
df_wk_verw = pd.DataFrame(wk_verw)
df_uur_verw = pd.DataFrame(uur_verw)
df_api_data = pd.DataFrame(api_data)

# Tabs for Amsterdam & Country Weather
tab1, tab2 = st.tabs(["Amsterdam Weer", "Landelijk Weer"])

with tab1:
    st.header("Weer in Amsterdam")

with tab2:
    st.title("Landelijk Weerkaart")

    @st.cache_data
    def process_hourly_data(df):
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['datum'] = df['datetime'].dt.strftime('%d-%m-%Y')
        df['tijd'] = df['datetime'].dt.strftime('%H:%M')
        df['tijd'] = pd.to_datetime(df['tijd'], format='%H:%M', errors='coerce')
        return df

    df_uur_verw = process_hourly_data(df_uur_verw)

    weather_icons = {
        "zonnig": "zonnig.png",
        "bewolkt": "bewolkt.png",
        "half bewolkt": "halfbewolkt.png",
        "licht bewolkt": "halfbewolkt.png",
        "regen": "regen.png",
        "buien": "buien.png",
        "mist": "mist.png",
        "sneeuw": "sneeuw.png",
        "onweer": "bliksem.png",
        "hagel": "hagel.png",
        "helderenacht": "helderenacht.png",
        "nachtmist": "nachtmist.png",
        "wolkennacht": "wolkennacht.png",
        "zwaar bewolkt": "zwaarbewolkt.png"
    }

    city_coords = {
        "Amsterdam": [52.3676, 4.9041],
        "Assen": [52.9929, 6.5642],
        "Lelystad": [52.5185, 5.4714],
        "Leeuwarden": [53.2012, 5.7999],
        "Arnhem": [51.9851, 5.8987],
        "Groningen": [53.2194, 6.5665],
        "Maastricht": [50.8514, 5.6910],
        "Eindhoven": [51.4416, 5.4697],
        "Den Helder": [52.9563, 4.7601],
        "Enschede": [52.2215, 6.8937],
        "Amersfoort": [52.1561, 5.3878],
        "Middelburg": [51.4988, 3.6136],
        "Rotterdam": [51.9225, 4.4792],
        "Zwolle": [52.5167, 6.0833],
    }

    df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[0])
    df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[1])

    def create_full_map(df, visualisatie_optie, geselecteerde_uur, selected_cities):
        nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8, tiles="CartoDB positron")
        df_filtered = df[df["tijd"] == geselecteerde_uur]

        for index, row in df_filtered.iterrows():
            if visualisatie_optie == "Weer":
                icon_file = weather_icons.get(row['image'].lower(), "bewolkt.png")
                icon_path = f"iconen-weerlive/{icon_file}"
                popup_text = f"{row['plaats']}: {row['temp']}°C, {row['image']}"

                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=popup_text,
                    tooltip=row["plaats"],
                    icon=CustomIcon(icon_path, icon_size=(45, 45))
                ).add_to(nl_map)

            elif visualisatie_optie == "Temperatuur":
                folium.map.Marker(
                    location=[row["lat"], row["lon"]],
                    tooltip=row["plaats"],
                    icon=folium.DivIcon(
                        html=(
                            '<div style="'
                            'display:inline-block;'
                            'white-space:nowrap;'
                            'line-height:1;'
                            'background-color: rgba(255, 255, 255, 0.7);'
                            'border: 1px solid #fdcb50;'
                            'border-radius: 4px;'
                            'padding: 2px 6px;'
                            'color: black;'
                            'font-weight: bold;'
                            'font-size:18px;'
                            'text-align:center;'
                            '">'
                            f'{row["temp"]}°C'
                            '</div>'
                        )
                    )
                ).add_to(nl_map)

            elif visualisatie_optie == "Neerslag":
                folium.map.Marker(
                    location=[row["lat"], row["lon"]],
                    tooltip=row["plaats"],
                    icon=folium.DivIcon(
                        html=(
                            '<div style="'
                            'display:inline-block;'
                            'white-space:nowrap;'
                            'line-height:1;'
                            'background-color: rgba(255, 255, 255, 0.7);'
                            'border: 1px solid #93b2f4;'
                            'border-radius: 4px;'
                            'padding: 2px 6px;'
                            'color: #93b2f4;'
                            'font-weight: bold;'
                            'font-size:18px;'
                            'text-align:center;'
                            '">'
                            f'{row["neersl"]} mm'
                            '</div>'
                        )
                    )
                ).add_to(nl_map)

        return nl_map

    if "selected_cities" not in st.session_state:
        st.session_state["selected_cities"] = [cities[0]]

    selected_cities = st.session_state["selected_cities"]

    df_selected_cities = df_uur_verw[df_uur_verw['plaats'].isin(selected_cities)]
    visualization_option = st.selectbox("Selecteer weergave", ["Temperatuur", "Weer", "Neerslag"])

    unieke_tijden = df_selected_cities["tijd"].dropna().unique()
    huidig_uur = datetime.now().replace(minute=0, second=0, microsecond=0)
    if huidig_uur not in unieke_tijden and len(unieke_tijden) > 0:
        huidig_uur = unieke_tijden[0]
    selected_hour = st.select_slider(
        "Selecteer uur",
        options=sorted(unieke_tijden),
        value=huidig_uur,
        format_func=lambda t: t.strftime('%H:%M') if not pd.isnull(t) else "No time"
    )

    nl_map = create_full_map(df_uur_verw, visualization_option, selected_hour, selected_cities)
    st_folium(nl_map, width=700)
