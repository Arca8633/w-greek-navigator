import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta
import plotly.graph_objects as go
import plotly.express as px

# DIESE ZEILE MUSS GANZ OBEN STEHEN
st.set_page_config(
    page_title="Ionian Navigator",
    page_icon="🧭", # Hier kannst du auch ein anderes Emoji wie ⛵ oder ⚓ nehmen
    layout="wide"
)

# Konfiguration der Seite
st.set_page_config(page_title="Ionian Sailor Pro", layout="wide", page_icon="⛵")

# Titel der Seite
st.title("⛵ Strategischer Segel-Planer")

# Auswahl des richtigen Pfeiles für die Tabelle
def get_arrow(deg):
    arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➡️", "↘️"]
    return arrows[int(((deg +22.5) % 360) / 45)]

# Funktion für die farbliche Gestaltung der Tabelle
def color_wind(val):
    # val ist hier der Wert in der Zelle
    color = 'white'
    if isinstance(val, (int, float)):
        if val >= 22: color = '#ff4b4b' # Rot ab 6 Bft
        elif val >= 15: color = '#ffa500' # Orange ab 4-5 Bft
        elif val >= 7: color = "#78E94C" # Grün (idealer Segelwind)
        elif val > 3: color = "#56dbec" # Hellblau (Chill-Segelwind)
        elif val <= 3: color = "#CECECEFF" # Grau (Motorselgel)
    return f'background-color: {color}'

# Beaufort Funktion -- Umrechnung
def get_bft(w_knots):
    if w_knots  < 1: return 0
    if w_knots  < 3: return 1
    if w_knots  < 6: return 2
    if w_knots  < 10: return 3
    if w_knots  < 15: return 4
    if w_knots  < 21: return 5
    if w_knots  < 27: return 6
    if w_knots  < 33: return 7
    if w_knots  < 40: return 8
    if w_knots  < 47: return 9
    if w_knots  < 55: return 10
    if w_knots  < 63: return 11
    return 12


# Definition für die Darstellung der Pfeile in der Windrose
#----------------------------------------------------------
def create_nautical_chart(wind_kn, wind_dir, wave_m, wave_dir, strom_kn, strom_dir):
    
    #Pfeillängenkorrektur
    if wind_kn <= 1:
        wind_kn_korr = wind_kn * 5
    elif wind_kn <= 2:
        wind_kn_korr = wind_kn * 2
    else: wind_kn_korr = 1

    if wave_m <= 1:
        wave_m_korr = wave_m * 5
    elif wave_m <= 2:
        wave_m_korr = wave_m * 2
    else: wave_m_korr = 1

    if strom_kn <= 1:
        strom_kn_korr = strom_kn * 10
    elif strom_kn <= 2:
        strom_kn_korr = strom_kn * 5
    else: strom_kn_korr = 2
    
    # Hier kommt dein kompletter "fig = go.Figure()" Block rein
    fig = go.Figure()
    # Eigener Kurs
    # Eigener Kurs (Schwarz, von Mitte nach Aussen)
    fig.add_trace(go.Scatterpolar(
        r=[0, max(wind_kn_korr-1, wind_kn_korr + 1)], theta=[my_course, my_course],
        mode='lines+markers', name='Mein Kurs',
        line=dict(color='gray', width=6),
        marker=dict(symbol='arrow', size=25, angleref='previous')
    ))

    # Wind-Pfeil
    fig.add_trace(go.Scatterpolar(
        r=[wind_kn_korr, 0], theta=[wind_dir, wind_dir],
        mode='lines+markers', name=f'🌬️ aus {wind_dir}°, {wind_kn} kn',
        line=dict(color='blue', width=6),
        marker=dict(symbol='arrow', size=25, angleref='previous')
    ))

    # Wellen-Pfeil (x10)
    fig.add_trace(go.Scatterpolar(
        r=[wave_m_korr, 0], theta=[wave_dir, wave_dir],
        mode='lines+markers', name=f'〰️ aus {wave_dir}°, {wave_m}m',
        line=dict(color='green', width=5),
        marker=dict(symbol='arrow', size=15, angleref='previous')
    ))

    # Strömung (Umgerechnet: Herkunft statt Ziel)
    strom_herkunft = (strom_dir + 180) % 360
    fig.add_trace(go.Scatterpolar(
        r=[strom_kn_korr, 0], theta=[strom_herkunft, strom_herkunft],
        mode='lines+markers', name=f'Strom aus {strom_herkunft}°, {strom_kn} kn',
        line=dict(color='red', width=4),
        marker=dict(symbol='arrow', size=15, angleref='previous')
    ))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=90),
            radialaxis=dict(range=[0, max(wind_kn_korr + 1, wind_kn_korr + 1)], showticklabels=True),
        ),
        title="Zentrum-Ansicht (Pfeile richtung Boot)",
        showlegend=True
    )
    return fig # Ganz wichtig: Die Funktion "gibt die Grafik zurück"


with st.sidebar:
    st.header("Einstellungen")

    # Region Auswahl
    region = st.selectbox("Region wählen:",
        ["Korfu (Nord)",
         "Lefkas (Mitte)",
         "Ithaka/Kefalonia",
         "Zakynthos (Süd)",
         "Ionio Pelagos",
         "Messinakos Eingang",
         "Messinakos Golf",
         "Kitira West",
         "Kitira Ost",
         "Lakonischer Golf",
         "Mirtoisches Meer",
         "Argolischer Golf",
         "Kolpos Idras",
         "Agios",
         "Saronischer Golf (E)",
         "Saronischer Golf (W)",
         "Golf von Korint (E)",
         "Golf von Korint (W)",
         "Solent"
         ])
    coords = {"Korfu (Nord)": [39.62, 19.96],
            "Lefkas (Mitte)": [38.72, 20.77], 
            "Ithaka/Kefalonia": [38.30, 20.82],
            "Zakynthos (Süd)": [37.78, 21.05],
            "Ionio Pelagos": [37.31, 21.45],
            "Messinakos Eingang": [36.64, 21.83],
            "Messinakos Golf": [36.86, 22.05],
            "Kitira West": [36.25,22.69],
            "Kitira Ost": [36.26,23.23],
            "Lakonischer Golf": [36.65,22.69],
            "Mirtoisches Meer": [36.97,23.63],
            "Argolischer Golf": [37.37,22.91],
            "Kolpos Idras": [37.37,23.42],
            "Agios": [37.52,23.78],
            "Saronischer Golf (E)": [37.74,23.64],
            "Saronischer Golf (W)": [37.78,23.31],
            "Golf von Korint (E)": [38.0,22.83],
            "Golf von Korint (w)": [38.28,22.39],
            "Solent": [50.78, -1.26]}
    lat, lon = coords[region]

    my_course = st.number_input("Mein CoG [°]", 0, 360, 0)

    # Von welcher Zeit an soll die Datenliste beginnen
    st.subheader("Startzeit")
    d = st.date_input("Tag wählen:", datetime.now())    
    t = st.time_input("Uhrzeit wählen:", datetime.now())
    start_dt = datetime.combine(d, t).replace(minute=0, second=0, microsecond=0)
    
    # Zeitraum Auswahl
    hours_to_show = st.radio("Zeitraum [h]:", [8, 24, 48, 72], horizontal=True)

# 2. DATEN ABFRAGEN & IM SPEICHER (Session State) HALTEN
if st.button("Strategie-Daten laden"):

    wh_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,temperature_2m,relative_humidity_2m,pressure_msl,precipitation&wind_speed_unit=kn&past_days=1&timezone=auto"
    sh_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction&wind_speed_unit=kn&timezone=auto"

    wh_res = requests.get(wh_url).json()['hourly']
    sh_res = requests.get(sh_url).json()['hourly']

    # Wetterdaten für Tabelle/Rose filtern
    # Wir nehmen nur die nächsten X Stunden ab jetzt
    data_list = []
    for i in range(len(wh_res['time'])):
        # Zeit aus API in Python-Zeit umwandeln
        forecast_time = datetime.fromisoformat(wh_res['time'][i])

        # Nur Zeiten anzeigen, die JETZT oder in der ZUKUNFT liegen
        if forecast_time >= start_dt:
            # Daten aus beiden Quellen zusammenführen            
            data_list.append({
                "Uhrzeit": forecast_time.strftime("%d.%m. %H:%M"),
                "Wind aus": wh_res['wind_direction_10m'][i], # {get_arrow(wh_res['wind_direction_10m'][i])}",
                "Wind (kn)": round(wh_res['wind_speed_10m'][i], 1),
                "Bft": get_bft(wh_res['wind_speed_10m'][i]),
                "Böen (kn)": round(wh_res['wind_gusts_10m'][i], 1),
                "Welle (m)": round(sh_res['wave_height'][i], 1),    # Aus Marine-API
                "Welle aus": sh_res['wave_direction'][i], # {get_arrow(wh_res['wave_direction'][i])}",
                "Strom (kn)": round(sh_res['ocean_current_velocity'][i], 1),
                "Strom nach": sh_res['ocean_current_direction'][i] ,
                "Regen (mm)": round(wh_res['precipitation'][i], 0),
                "P (hPa)": wh_res['pressure_msl'][i]
            })

        # Stop, wenn wir genug Stunden haben
        if len(data_list) >= hours_to_show: break
    
    # Barometer-Daten (Extra-Liste für Plot)   
    press_list = []
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
        
    start_plot = now - timedelta(hours=6)
    end_plot = now + timedelta(hours=12)

    for i in range(len(wh_res['time'])):
        f_time = datetime.fromisoformat(wh_res['time'][i])
        if start_plot <= f_time <= end_plot:
            press_list.append({
                "Zeit": f_time.strftime("%H:%M"),
                "P (hPa)": wh_res['pressure_msl'][i]
            })

    # Speichern im "Gedächtnis"
    st.session_state['weather_data'] = data_list
    st.session_state['pressure_history'] = press_list
    st.session_state['current_idx'] = 0

# --- 3. ANZEIGE-LOGIK (Wird bei jedem Klick ausgeführt) ---
if 'weather_data' in st.session_state:
    data = st.session_state['weather_data']
     
    # Tabelle anzeigen
        
    # Luftdruck-Warnung & Chart
    # Wir brauchen die letzten 3 Werte für den Alarm-Check
    p_hist = st.session_state['pressure_history']
    if len(p_hist) >= 4:
        # Aktueller Druck vs. Druck vor 3 Stunden
        p_diff = round(p_hist[5]['P (hPa)'] - p_hist[2]['P (hPa)'], 1) # Grober 3h Check
        #if p_diff <= -1.5: st.warning(f"📉 Barometer sinkt: {p_diff} hPa/3h")
        fig_p = px.line(pd.DataFrame(p_hist), x="Zeit", y="P (hPa)", title="Barograph")
        fig_p.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')        
        fig_p.update_yaxes(range=[980, 1045])
        st.plotly_chart(fig_p, width='stretch')
        

        # BAROMETER ALARM ANZEIGEN
        if p_diff <= -3.0:
            st.error(f"🚨 BAROMETER ALARM: Druckabfall von {p_diff} hPa in 3h! Starkwindgefahr!")
        elif p_diff <= -1.5:
            st.warning(f"⚠️ Achtung: Luftdruck sinkt ({p_diff} hPa/3h). Wetter beobachten.")
        else:
            st.success(f"⚖️ Luftdruck stabil ({p_diff} hPa/3h).")
   
    
# 3. DATEN ANZEIGEN (Falls vorhanden)
if 'weather_data' in st.session_state:
    
    data = st.session_state['weather_data']
    df = pd.DataFrame(data)
    
    styled_df = df.style.map(color_wind,subset=['Wind (kn)', 'Böen (kn)']).format({
            "Wind (kn)": "{:.1f}", 
            "Böen (kn)": "{:.1f}", 
            "Welle (m)": "{:.1f}", 
            "Strom (kn)": "{:.1f}",
            "Regen (mm)": "{:.1f}",
            "P (hPa)": "{:.1f}"
    })
    st.divider()

    # Tabelle anzeigen
    st.write("### 📅 Strategie-Planer")
    column_configuration = {
        "Uhrzeit": st.column_config.TextColumn("Zeit", width="small", pinned=True),
        "Wind (kn)": st.column_config.NumberColumn("Wind", width="small"),
        "Böen (kn)": st.column_config.NumberColumn("Böen", width="small"),
        "Welle (m)": st.column_config.NumberColumn("Welle", width="small"),
        "Strom (kn)": st.column_config.NumberColumn("Strom", width="small"),
        "Regen (mm)": st.column_config.NumberColumn("Regen", width="small"),
        "P (hPa) (mm)": st.column_config.NumberColumn("Regen", width="small"),
    }    
    st.dataframe(
        styled_df,
        column_config=column_configuration,
        use_container_width=False,
        hide_index=True
    )

    st.divider()
    
    curr = data[st.session_state['current_idx']]

    # Logik für Wind gegen Strömung
    diff = abs(curr["Wind aus"] - curr["Strom nach"])
    is_opposed = (diff < 50)
    # is_opposed = (diff > 140 and diff < 220)

    col1, col2 = st.columns(2)
    with col1:
        if curr["Böen (kn)"] >= 30:
                st.error("⚠️⚠️⚠️ REFF 3:" "Sehr starke Böen! Main: Reff 3 Jib: 1/3.")
        elif curr["Böen (kn)"] >= 25:
                st.warning("⚠️⚠️ REFF 2: Sehr starke Böen! Main: Reff 2 Jib: 1/2.")
        elif curr["Böen (kn)"] >= 20:
                st.warning("⚠️ REFF 1: Starke Böen! Main: Reff 1 Jib: 3/4.")
                
        else:
            st.success("🟢 Vollzeug: Windbedingungen sind stabil."
    )
        
    with col2:
        if is_opposed and (curr["Strom (kn)"] > 2.5):
            st.error("❗ ACHTUNG: Wind gegen Strömung! Erwarte steile, kurze Wellen.")
        else:
            st.info("See: Keine kritische Wind-Strömung-Konstellation."
    )

    st.divider()

    if 'current_idx' not in st.session_state:
        st.session_state['current_idx'] = 0

    st.subheader("Visualisierung Steuerung")

    # NAVIGATION WINDROSE
    st.divider()
    c1, c2, c3 = st.columns([1,2,1])
    if c1.button("⬅️ Früher") and st.session_state['current_idx'] > 0:
        st.session_state['current_idx'] -= 1
    if c3.button("Später ➡️") and st.session_state['current_idx'] < len(data)-1:
        st.session_state['current_idx'] += 1
    
    
    c2.write(f"**Anzeige für: {curr['Uhrzeit']}**")
    
    #AUFRUF der Funktion mit den Werten aus deiner 'curr' Variable
    fig_navigation = create_nautical_chart(
        curr["Wind (kn)"], curr["Wind aus"], 
        curr["Welle (m)"], curr["Welle aus"], 
        curr["Strom (kn)"], curr["Strom nach"]
    )
        
    #ANZEIGEN der Grafik
    st.plotly_chart(fig_navigation, width='stretch')

    # --- NOTFALL & FUNK (Olympia Radio / Ionische Inseln) ---
with st.expander("🆘 Notfall-Infos & Funk (Ionian Sea)"):
    emergency_data = {
        "Dienst": ["Küstenwache (General)", "Olympia Radio (VHF)", "Seenotruf (VHF)", "Medizin. Hilfe (EKAB)"],
        "Kanal / Tel": ["108", "Ch 02 / 03 / 04 / 85", "Ch 16", "166"],
        "Info": ["Griechenlandweit", "Wetter & Sicherheit", "Nur Notfall", "Rettungsdienst"]
    }
    st.table(pd.DataFrame(emergency_data))

    st.info("⚠️ VHF Olympia Radio Sendezeiten: 06:33, 09:33, 15:33, 21:33 (Lokalzeit)")
