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
menu = st.sidebar.radio("Navigeer naar:", ["Oude versie", "Nieuwe versie", "Bronnen"])

if menu == "Oude versie":
    tab3, tab4 = st.tabs(["Oude versie", "Veranderingen"])

    with tab3:
            st.title("Oude Versie Weerapp")
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

            # API Configuration
            api_key = 'd5184c3b4e'
            cities = [
                'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht',
                'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam'
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

            @st.cache_data
            def process_hourly_data(df):
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df['datum'] = df['datetime'].dt.strftime('%d-%m-%Y')
                df['tijd'] = df['datetime'].dt.strftime('%H:%M')
                df['tijd'] = pd.to_datetime(df['tijd'], format='%H:%M', errors='coerce')
                return df

            df_uur_verw = process_hourly_data(df_uur_verw)

            st.title("Het weer van vandaag")

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
                "heldere nacht": "helderenacht.png",
                "nachtmist": "nachtmist.png",
                "wolkennacht": "wolkennacht.png",
                "zwaar bewolkt": "zwaarbewolkt.png"
            }

            city_coords = {
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
            }

            df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[0])
            df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[1])

            def create_full_map(df, visualisatie_optie, geselecteerde_uur, selected_cities):
                nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8)
                df_filtered = df[df["tijd"] == geselecteerde_uur]

                for index, row in df_filtered.iterrows():
                    # Uncomment if you only want markers for selected cities:
                    # if row["plaats"] not in selected_cities:
                    #     continue

                    if visualisatie_optie == "Weer":
                        icon_file = weather_icons.get(row['image'].lower(), "bewolkt.png")
                        icon_path = f"iconen-weerlive/{icon_file}"
                        popup_text = f"{row['plaats']}: {row['temp']}°C, {row['image']}"
                        
                        folium.Marker(
                            location=[row["lat"], row["lon"]],
                            popup=popup_text,
                            tooltip=row["plaats"],
                            icon=CustomIcon(icon_path, icon_size=(30, 30))
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

            if len(selected_cities) == 0:
                st.warning("Geen stad geselecteerd. Kies een stad onderaan de pagina om de grafiek te tonen.")
            else:
                if visualization_option in ["Temperatuur", "Neerslag"]:
                    plt.rcParams['axes.facecolor'] = '#f0f8ff'
                    plt.rcParams['figure.facecolor'] = '#f0f8ff'
                    plt.rcParams['axes.edgecolor'] = '#b0c4de'
                    plt.rcParams['axes.labelcolor'] = '#333333'
                    plt.rcParams['xtick.color'] = '#333333'
                    plt.rcParams['ytick.color'] = '#333333'
                    plt.rcParams['grid.color'] = '#b0c4de'
                    plt.rcParams['grid.linestyle'] = '--'
                    plt.rcParams['grid.linewidth'] = 0.5
                    plt.rcParams['axes.titlepad'] = 15

                    fig, ax1 = plt.subplots(figsize=(10, 5))

                    if visualization_option == "Temperatuur":
                        for city in selected_cities:
                            city_data = df_selected_cities[df_selected_cities['plaats'] == city]
                            city_data = city_data.sort_values('tijd')
                            city_data['temp'] = city_data['temp'].interpolate(method='linear')

                            ax1.set_xlabel('Tijd')
                            ax1.set_ylabel('Temperatuur (°C)', color='tab:red')
                            ax1.plot(city_data['tijd'], city_data['temp'], label=city, linestyle='-', marker='o')

                        ax1.tick_params(axis='y', labelcolor='tab:red')
                        ax1.set_title("Temperatuur per Stad")

                    elif visualization_option == "Neerslag":
                        for city in selected_cities:
                            city_data = df_selected_cities[df_selected_cities['plaats'] == city]
                            city_data = city_data.sort_values('tijd')
                            city_data['neersl'] = city_data['neersl'].interpolate(method='linear')
                            if city_data['neersl'].isna().all():
                                city_data['neersl'] = 0

                            ax1.set_xlabel('Tijd')
                            ax1.set_ylabel('Neerslag (mm)', color='tab:blue')
                            ax1.plot(city_data['tijd'], city_data['neersl'], label=city, linestyle='-', marker='x')

                        ax1.set_ylim(-0.2, 8)
                        ax1.set_yticks(range(0, 9))
                        ax1.tick_params(axis='y', labelcolor='tab:blue')
                        ax1.set_title("Neerslag per Stad")

                    ax1.grid(True)
                    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

                    fig.legend(loc='upper right', bbox_to_anchor=(1.1, 1), bbox_transform=ax1.transAxes)
                    plt.tight_layout()
                    st.pyplot(fig)

            if visualization_option != "Weer":
                st.subheader("Selecteer steden")
                st.write("Hieronder kun je de steden selecteren die je weergeven")
                cols = st.columns(3)
                for i, city in enumerate(cities):
                    with cols[i % 3]:
                        key = f"checkbox_{city}_{i}"
                        checked_now = city in st.session_state["selected_cities"]
                        checkbox_value = st.checkbox(city, value=checked_now, key=key)

                        if checkbox_value and city not in st.session_state["selected_cities"]:
                            st.session_state["selected_cities"].append(city)
                        elif not checkbox_value and city in st.session_state["selected_cities"]:
                            st.session_state["selected_cities"].remove(city)
    with tab4:
        st.title("Veranderingen voor de nieuwe versie")
        st.write("""
        Voor de nieuwe versie hebben we als eerst de volgende plannen gemaakt:
        - We focussen ons op het maken van een weerapp van Amsterdam, met een landelijke kaart als extra optie.
        - Het eerste wat een gebruiker moet zien is de maximale, minimale en gemiddelde temperatuur van de dag.
        - Vervolgens moet er een samenvatting zijn van het weer in Amsterdam.
        - Daarna willen we een grafiek maken van de neerslag en zonnestraling in Amsterdam.
        """)

elif menu == 'Nieuwe versie':  
    # Alleen achtergrond instellen in "Nieuwe versie"
    set_bg_image("pexels-pixabay-531756.jpg")

    st.markdown("""
        <style>
            /* Apply black background only to key text elements */
            div.stTitle, div.stHeader, div.stSubheader, div.stTabs, div[data-testid="metric-container"] {
                background-color: rgba(0, 0, 0, 0.8) !important;
                color: white !important;
                padding: 10px;
                border-radius: 5px;
                display: inline-block;
            }
            /* Style text inside metrics */
            div[data-testid="stMetricValue"] {
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)


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
        # Also keep the time as HH:MM (24h) so we can chart without a date
        df['tijd'] = df['datetime'].dt.strftime('%H:%M')  # For the slider/markers
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
        st.header("Weer in Amsterdam (vandaag)", divider='gray')

        # 1) Filter df_uur_verw voor Amsterdam en "vandaag"
        today_date = datetime.now().date()
        df_uur_ams = df_uur_verw[
            (df_uur_verw['plaats'] == 'Amsterdam') &
            (df_uur_verw['datetime'].dt.date == today_date)
        ].copy()

        if df_uur_ams.empty:
            st.warning("Geen uurlijke voorspellingen voor Amsterdam gevonden voor vandaag.")
        else:
            # Convert to numeric if needed
            for col in ['temp', 'neersl']:
                if col in df_uur_ams.columns:
                    df_uur_ams[col] = pd.to_numeric(df_uur_ams[col], errors='coerce')

            # 2) Bepaal min/max/gemiddelde temp
            max_temp = df_uur_ams['temp'].max()
            min_temp = df_uur_ams['temp'].min()
            avg_temp = df_uur_ams['temp'].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Max Temp (°C)", round(max_temp, 1) if pd.notnull(max_temp) else "N/A")
            col2.metric("Min Temp (°C)", round(min_temp, 1) if pd.notnull(min_temp) else "N/A")
            col3.metric("Gem. Temp (°C)", round(avg_temp, 1) if pd.notnull(avg_temp) else "N/A")

            # 3) Korte samenvatting (val terug op 'image' of iets anders als je geen samenv hebt)
            if 'samenv' in df_uur_ams.columns:
                summary = df_uur_ams.iloc[0]['samenv']
            else:
                summary = df_uur_ams.iloc[0].get('image', 'Geen samenvatting')

            st.subheader("Samenvatting")
            st.write(summary)

            # 4) Grafiek neerslag -> X-as zonder datum, alleen HH:MM
            if 'neersl' in df_uur_ams.columns:
                # Convert time to a proper datetime format
                df_uur_ams['tijd_24h'] = df_uur_ams['datetime'].dt.strftime('%H:%M')
                df_uur_ams['tijd_24h_sortable'] = pd.to_datetime(df_uur_ams['tijd_24h'], format='%H:%M')

                # Generate a full 24-hour range from 00:00 to 23:59
                full_day = pd.date_range(start=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0), 
                                        periods=24, freq='H').strftime('%H:%M')

                # Create a DataFrame with this full range
                full_range_df = pd.DataFrame(full_day, columns=['tijd_24h'])

                # Merge with actual data (ensuring all hours are present)
                df_uur_ams = full_range_df.merge(df_uur_ams, on='tijd_24h', how='left')

                st.subheader("Verwachte neerslag (mm)")
                st.line_chart(
                    data=df_uur_ams,
                    x='tijd_24h',  # Only 24h time here, no date
                    y='neersl',
                    x_label='Uur van de dag',
                    y_label='Neerslag (mm)',
                )
            else:
                st.info("Geen neerslagkolom ('neersl') gevonden in de uurlijkse data.")

            # 5) Grafiek zonlicht -> X-as zonder datum, alleen HH:MM
            if 'gr' in df_uur_ams.columns:
                # Convert time to a proper datetime format
                df_uur_ams['tijd_24h'] = df_uur_ams['datetime'].dt.strftime('%H:%M')
                df_uur_ams['tijd_24h_sortable'] = pd.to_datetime(df_uur_ams['tijd_24h'], format='%H:%M')

                # Generate a full 24-hour range from 00:00 to 23:59
                full_day = pd.date_range(start=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0), 
                                        periods=24, freq='H').strftime('%H:%M')

                # Create a DataFrame with this full range
                full_range_df = pd.DataFrame(full_day, columns=['tijd_24h'])

                # Merge with actual data (ensuring all hours are present)
                df_uur_ams = full_range_df.merge(df_uur_ams, on='tijd_24h', how='left')

                st.subheader("Verwachte zonnestraling (Watt/M²)")
                st.line_chart(
                    data=df_uur_ams,
                    x='tijd_24h',  # Keeps labels as HH:MM
                    y='gr',
                    x_label='Uur van de dag',
                    y_label='Zonnestraling (Watt/M²)',
                    color='#FFFF00'
                )

            else:
                st.info("Geen zonlichtkolom ('gr') gevonden in de uurlijkse data.")

    # =========================
    # TAB 2: LANDLIJK WEER
    # =========================
    with tab2:
        st.title("Landelijk Weerkaart")

        weather_icons = {
            "zonnig": "zonnig.png",
            "bewolkt": "bewolkt.png",
            "halfbewolkt": "halfbewolkt.png",
            "lichtbewolkt": "halfbewolkt.png",
            "regen": "regen.png",
            "buien": "buien.png",
            "mist": "mist.png",
            "sneeuw": "sneeuw.png",
            "onweer": "bliksem.png",
            "hagel": "hagel.png",
            "helderenacht": "helderenacht.png",
            "nachtmist": "nachtmist.png",
            "wolkennacht": "wolkennacht.png",
            "zwaarbewolkt": "zwaarbewolkt.png"
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

        df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[0])
        df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda c: city_coords.get(c, [None, None])[1])

        def create_full_map(df, visualisatie_optie, geselecteerde_uur_str, selected_cities):
            nl_map = folium.Map(
                location=[52.3, 5.3],
                zoom_start=8,
                tiles="CartoDB positron"
            )

            # Filter on the time string, e.g. "13:00"
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

        unieke_tijden = df_selected_cities["tijd"].dropna().unique()
        # Sort them so the slider is in ascending time order
        sorted_times = sorted(unieke_tijden)

        # Attempt to match the current hour if it exists, otherwise default to first time
        current_hour_str = datetime.now().strftime('%H:%M')
        if current_hour_str not in sorted_times and len(sorted_times) > 0:
            current_hour_str = sorted_times[0]

        selected_hour_str = st.select_slider(
            "Selecteer uur",
            options=sorted_times,
            value=current_hour_str
        )

        # Build the map
        nl_map = create_full_map(df_uur_verw, visualization_option, selected_hour_str, selected_cities)
        st_folium(nl_map, width=None, height=600)

else: 
    st.title("Gebruikte bronnen")
    st.write("""
    Voor het maken van deze weerapp hebben wij gebruik gemaakt van een API, AI en een bron van inspiratie. Deze zijn als volgt:
    - De WeerLive API (https://weerlive.nl/delen.php)
    - ChatGPT (https://chatgpt.com/)
    - Weeronline als inspiratiebron (https://www.weeronline.nl/)
    """)