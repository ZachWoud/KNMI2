import base64
import requests
import pandas as pd
import streamlit as st
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

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

menu = st.sidebar.radio("Navigeer naar:", ["Verandering", "Nieuwe versie"])

if menu == "Verandering":
    st.title("Veranderingen")
    st.write("Hier kun je de veranderingen toevoegen.")
else:
    set_bg_image("pexels-pixabay-531756.jpg")

    # -------------------------------------------------------
    # Fetch data (using your existing function or placeholders)
    # -------------------------------------------------------
    api_key = 'd5184c3b4e'
    cities = ['Amsterdam','Assen','Lelystad','Leeuwarden','Arnhem','Groningen','Maastricht',
              'Eindhoven','Den Helder','Enschede','Amersfoort','Middelburg','Rotterdam','Zwolle']

    @st.cache_data
    def fetch_weather_data():
        # Your usual fetch logic
        # This is just a placeholder
        liveweer, wk_verw, uur_verw, api_data = [], [], [], []
        return liveweer, wk_verw, uur_verw, api_data

    liveweer, wk_verw, uur_verw, api_data = fetch_weather_data()

    # Convert them to DataFrames
    df_liveweer = pd.DataFrame(liveweer)
    df_wk_verw   = pd.DataFrame(wk_verw)
    df_uur_verw  = pd.DataFrame(uur_verw)
    df_api_data  = pd.DataFrame(api_data)

    # -------------------------------------------------------
    # Example: PROCESS hourly data
    # -------------------------------------------------------
    @st.cache_data
    def process_hourly_data(df):
        # Convert "timestamp" to a datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        # Extract "HH:MM" in 24-hour format for a pure string time (no date)
        df['tijd_hhmm'] = df['datetime'].dt.strftime('%H:%M')
        # Convert temp & neersl to numeric if needed
        for col in ['temp','neersl']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    df_uur_verw = process_hourly_data(df_uur_verw)

    # -------------------------------------------------------
    # Create tabs
    # -------------------------------------------------------
    tab1, tab2 = st.tabs(["Amsterdam Weer", "Landelijk Weer"])

    # =============================
    # TAB 1: AMSTERDAM WEER
    # =============================
    with tab1:
        st.header("Weer in Amsterdam (vandaag)")

        today_date = datetime.now().date()

        # Filter for Amsterdam & today's date
        df_ams_today = df_uur_verw[
            (df_uur_verw['plaats'] == 'Amsterdam') &
            (df_uur_verw['datetime'].dt.date == today_date)
        ].copy()

        if df_ams_today.empty:
            st.warning("Geen data voor Amsterdam vandaag.")
        else:
            # Drop any rows missing time or values
            df_ams_today.dropna(subset=['tijd_hhmm','temp','neersl'], inplace=True)
            # Sort by the "HH:MM" string ascending
            df_ams_today.sort_values('tijd_hhmm', inplace=True)

            # --- Compute stats
            max_temp = df_ams_today['temp'].max()
            min_temp = df_ams_today['temp'].min()
            avg_temp = df_ams_today['temp'].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Max Temp (°C)", round(max_temp,1))
            col2.metric("Min Temp (°C)", round(min_temp,1))
            col3.metric("Gem. Temp (°C)", round(avg_temp,1))

            # --- A short textual summary
            # Fallback on "image" if we have no "samenv"
            if 'samenv' in df_ams_today.columns:
                summary = df_ams_today.iloc[0]['samenv']
            else:
                summary = df_ams_today.iloc[0].get('image','Geen samenvatting')

            st.subheader("Samenvatting")
            st.write(summary)

            # --- Make a MATPLOTLIB chart with HH:MM as X-axis, grid ON, no date/AM/PM
            # We'll show "neersl" as Y. This is a STATIC chart with no date in the tooltip.
            times = df_ams_today['tijd_hhmm'].values
            neerslag = df_ams_today['neersl'].values

            fig, ax = plt.subplots()
            ax.plot(times, neerslag, marker='o')
            ax.set_xlabel("Tijd (HH:MM)")
            ax.set_ylabel("Neerslag (mm)")
            ax.set_title("Verwachte neerslag gedurende de dag")
            ax.grid(True)  # Add a grid
            # Show the plot in Streamlit
            st.pyplot(fig)

    # =============================
    # TAB 2: LANDLIJK WEER (example)
    # =============================
    with tab2:
        st.title("Landelijk Weerkaart")
        st.write("Hier komt je logica voor de landelijke weerkaart...")
        # Remainder of your code for the country map
