import base64
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

# OPTIONAL: Set page layout
st.set_page_config(layout="wide")

def set_bg_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    page_bg_css = f"""
    <style>
    .stApp {{
        background: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_css, unsafe_allow_html=True)

# ------------------------------------------
# NAVIGATION
# ------------------------------------------
menu = st.sidebar.radio("Navigeer naar:", ["Verandering", "Nieuwe versie"])

if menu == "Verandering":
    st.title("Veranderingen")
    st.write("Hier kun je de veranderingen toevoegen.")

else:
    # Alleen achtergrond instellen in "Nieuwe versie"
    set_bg_image("pexels-pixabay-531756.jpg")

    # ------------------------------------------
    # API Configuration and Data Fetching
    # ------------------------------------------
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

    # ------------------------------------------
    # Process hourly data (df_uur_verw)
    # ------------------------------------------
    @st.cache_data
    def process_hourly_data(df):
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        # Extract HH:MM for a time slider in the map tab
        df['tijd'] = df['datetime'].dt.strftime('%H:%M')
        # Also keep a direct time-based datetime for plotting
        df['tijd_dt'] = pd.to_datetime(df['tijd'], format='%H:%M', errors='coerce')
        return df

    df_uur_verw = process_hourly_data(df_uur_verw)

    # ------------------------------------------
    # TABS
    # ------------------------------------------
    tab1, tab2 = st.tabs(["Amsterdam Weer", "Landelijk Weer"])

    # =========================
    # TAB 1: AMSTERDAM WEER
    # =========================
    with tab1:
        st.header("Weer in Amsterdam (vandaag)")

        # 1) Filter df_uur_verw voor Amsterdam en "vandaag"
        today_date = datetime.now().date()
        df_uur_ams = df_uur_verw[
            (df_uur_verw['plaats'] == 'Amsterdam') &
            (df_uur_verw['datetime'].dt.date == today_date)
        ].copy()

        # Als je hourly data wilt: convert temp/neersl to numeric if needed
        for col in ['temp', 'neersl']:
            if col in df_uur_ams.columns:
                df_uur_ams[col] = pd.to_numeric(df_uur_ams[col], errors='coerce')

        if df_uur_ams.empty:
            st.warning("Geen uurlijke voorspellingen voor Amsterdam gevonden voor vandaag.")
        else:
            # 2) Bereken min/max/gemiddelde temp
            max_temp = df_uur_ams['temp'].max()
            min_temp = df_uur_ams['temp'].min()
            avg_temp = df_uur_ams['temp'].mean()

            # 3) Toon deze in metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Max Temp (°C)", round(max_temp, 1) if pd.notnull(max_temp) else "N/A")
            col2.metric("Min Temp (°C)", round(min_temp, 1) if pd.notnull(min_temp) else "N/A")
            col3.metric("Gem. Temp (°C)", round(avg_temp, 1) if pd.notnull(avg_temp) else "N/A")

            # 4) Korte samenvatting (als zoiets in df_uur_verw zit)
            #    Als er geen 'samenv' of 'verw' is, kun je bv. de eerste 'image' tonen.
            if 'samenv' in df_uur_ams.columns:
                summary = df_uur_ams.iloc[0]['samenv']
            else:
                # Fallback: neem de eerste 'image' description
                summary = df_uur_ams.iloc[0].get('image', 'Geen samenvatting beschikbaar')

            st.subheader("Samenvatting")
            st.write(summary)

            # 5) Grafiek neerslag (uurbasis)
            if 'neersl' in df_uur_ams.columns:
                df_uur_ams.sort_values('tijd_dt', inplace=True)
                st.subheader("Verwachte neerslag (mm)")
                st.line_chart(
                    data=df_uur_ams,
                    x='tijd_dt',
                    y='neersl'
                )
            else:
                st.info("Geen neerslagkolom ('neersl') gevonden in de uurlijkse data.")

    # =========================
    # TAB 2: LANDLIJK WEER
    # =========================
    with tab2:
        st.title("Landelijk Weerkaart")

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

        # Voor lat/lon
        df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[0])
        df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[1])

        def create_full_map(df, visualisatie_optie, geselecteerde_uur_str, selected_cities):
            nl_map = folium.Map(
                location=[52.3, 5.3],
                zoom_start=8,
                tiles="CartoDB positron"
            )

            df_filtered = df[df["tijd"] == geselecteerde_uur_str]

            for _, row in df_filtered.iterrows():
                if visualisatie_optie == "Weer":
                    icon_file = weather_icons.get(str(row.get('image', '')).lower(), "bewolkt.png")
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
                                'border: 1px solid red;'
                                'border-radius: 4px;'
                                'padding: 2px 6px;'
                                'color: red;'
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
                                'border: 1px solid blue;'
                                'border-radius: 4px;'
                                'padding: 2px 6px;'
                                'color: blue;'
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

        unieke_tijden = df_selected_cities["tijd_dt"].dropna().unique()
        huidig_uur = datetime.now().replace(minute=0, second=0, microsecond=0)
        if huidig_uur not in unieke_tijden and len(unieke_tijden) > 0:
            huidig_uur = unieke_tijden[0]

        sorted_times = sorted(unieke_tijden)
        selected_hour = st.select_slider(
            "Selecteer uur",
            options=sorted_times,
            value=huidig_uur,
            format_func=lambda t: t.strftime('%H:%M') if not pd.isnull(t) else "No time"
        )

        # Convert selected_hour back to "HH:MM"
        geselecteerde_uur_str = selected_hour.strftime('%H:%M')

        nl_map = create_full_map(df_uur_verw, visualization_option, geselecteerde_uur_str, selected_cities)
        st_folium(nl_map, width=None, height=600)
