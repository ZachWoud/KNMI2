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
    # Data Preparation Examples (if needed)
    # ------------------------------------------
    @st.cache_data
    def process_hourly_data(df):
        # Convert timestamp to datetime, and split into date & time
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df['datum'] = df['datetime'].dt.strftime('%d-%m-%Y')
        df['tijd'] = df['datetime'].dt.strftime('%H:%M')
        # Also keep a proper datetime for the time, if you want to plot by time on x-axis
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
        st.header("Weer in Amsterdam")

        # -----------------------------
        # 1. Select today's row in df_wk_verw for Amsterdam
        # -----------------------------
        # Typically, df_wk_verw might contain columns like: ['plaats', 'datum', 'tmax', 'tmin', 'samenv', etc.]
        # We'll search for today's date as dd-mm-yyyy
        today_str = datetime.now().strftime('%d-%m-%Y')
        df_wk_ams = df_wk_verw[(df_wk_verw['plaats'] == 'Amsterdam') & (df_wk_verw['datum'] == today_str)]
        
        # Fallback if not found: just take the first row for Amsterdam
        if df_wk_ams.empty:
            df_wk_ams = df_wk_verw[df_wk_verw['plaats'] == 'Amsterdam'].head(1)

        # Extract data from that row (assuming columns exist)
        if not df_wk_ams.empty:
            row = df_wk_ams.iloc[0]
            tmax = row.get('tmax', 'N/A')
            tmin = row.get('tmin', 'N/A')
            samenv = row.get('samenv', 'Geen samenvatting beschikbaar')
            
            # Gemiddelde temperatuur: kan uit df_wk_verw komen, of (tmax + tmin)/2
            # Hier doen we simpelweg (tmax + tmin) / 2, als die numeriek zijn
            try:
                tavg = (float(tmax) + float(tmin)) / 2
            except:
                tavg = 'N/A'
        else:
            # Als er écht niks is...
            tmax, tmin, tavg, samenv = 'N/A', 'N/A', 'N/A', 'Geen data gevonden'

        # -----------------------------
        # 2. Show metric widgets
        # -----------------------------
        col1, col2, col3 = st.columns(3)
        col1.metric("Max Temp (°C)", tmax)
        col2.metric("Min Temp (°C)", tmin)
        col3.metric("Gem. Temp (°C)", tavg)

        # -----------------------------
        # 3. Tekstuele samenvatting
        # -----------------------------
        st.subheader("Samenvatting")
        st.write(samenv)

        # -----------------------------
        # 4. Grafiek neerslag (uurdata)
        # -----------------------------
        # Filter df_uur_verw naar Amsterdam & vandaag
        df_uur_ams = df_uur_verw[
            (df_uur_verw['plaats'] == 'Amsterdam') &
            (df_uur_verw['datum'] == today_str)
        ].copy()

        # Soms staat neerslag in column 'neersl' of 'mm', etc.  
        # We assume 'neersl' is the precipitation column.
        # Sort by tijd_dt so the line chart is chronological
        df_uur_ams.sort_values('tijd_dt', inplace=True)

        # Check if there's any data:
        if df_uur_ams.empty:
            st.warning("Geen uurlijke data gevonden voor vandaag in Amsterdam.")
        else:
            st.subheader("Verwachte neerslag gedurende de dag")
            # Met Streamlit kun je direct een line_chart doen:
            st.line_chart(
                data=df_uur_ams,
                x='tijd_dt',   # x-as: tijd
                y='neersl',    # y-as: neerslag
            )

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

        # Add lat/lon columns
        df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[0])
        df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[1])

        def create_full_map(df, visualisatie_optie, geselecteerde_uur, selected_cities):
            nl_map = folium.Map(
                location=[52.3, 5.3],
                zoom_start=8,
                tiles="CartoDB positron"
            )

            df_filtered = df[df["tijd"] == geselecteerde_uur]

            for _, row in df_filtered.iterrows():
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
        # Zet huidig_uur naar de eerste beschikbare tijd als de huidige tijd niet in de lijst zit
        if huidig_uur not in unieke_tijden and len(unieke_tijden) > 0:
            huidig_uur = unieke_tijden[0]

        # We need to display times in HH:MM format. We'll let the slider use the 'tijd' string or the actual datetime
        # For clarity, we can put them in a dictionary or just pick from the unique times.
        # Here, let's sort them and do a select_slider with a simple format:
        sorted_times = sorted(unieke_tijden)
        selected_hour = st.select_slider(
            "Selecteer uur",
            options=sorted_times,
            value=huidig_uur,
            format_func=lambda t: t.strftime('%H:%M') if not pd.isnull(t) else "No time"
        )

        # We need to feed back the 'tijd' string that matches selected_hour (which is a datetime).
        geselecteerde_uur_str = selected_hour.strftime('%H:%M')

        nl_map = create_full_map(df_uur_verw, visualization_option, geselecteerde_uur_str, selected_cities)
        st_folium(nl_map, width=None, height=600)
