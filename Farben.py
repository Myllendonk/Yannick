import streamlit as st
import random
import json
import os
import pandas as pd
from matplotlib import colors as mcolors
from streamlit_extras.stylable_container import stylable_container
import warnings
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
import numpy as np
from streamlit_gsheets import GSheetsConnection

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)


np.asscalar = lambda x: x.item()
warnings.filterwarnings("ignore")

st.set_option("client.showErrorDetails", False)

st.set_page_config(layout="wide")

st.title("Das große Häkelrunden Farb-Duell")

show_name = st.checkbox("Farbname anzeigen", value=True)
FILTER_FILE = "filtered_colors.json"
from math import sqrt

def hex_distance(hex1, hex2):

    # HEX → RGB
    rgb1 = sRGBColor.new_from_rgb_hex(hex1)
    rgb2 = sRGBColor.new_from_rgb_hex(hex2)

    # RGB → LAB
    lab1 = convert_color(rgb1, LabColor)
    lab2 = convert_color(rgb2, LabColor)

    # CIEDE2000 Abstand
    return delta_e_cie2000(lab1, lab2)
# ---------- XKCD Farben laden ----------
colors = [c.replace("xkcd:", "") for c in mcolors.XKCD_COLORS.keys()]
xkcd = mcolors.XKCD_COLORS
# if False:
if os.path.exists(FILTER_FILE):

    # Datei laden
    with open(FILTER_FILE, "r") as f:
        filtered_colors = json.load(f)

else:

    # Farben filtern (dein Code von vorher)
    filtered_colors = []
    filtered_hex = []

    for name, hex_code in mcolors.XKCD_COLORS.items():

        too_similar = False

        for existing in filtered_hex:
            if hex_distance(hex_code, existing) < 6:
                too_similar = True
                # st.write(hex_distance(hex_code, existing))
                # st.markdown(
                #     f'<p style="color:{hex_code}; font-size:20px;">Diese Farbe wird angezeigt</p>',
                #     unsafe_allow_html=True
                # )
                # st.markdown(
                #     f'<p style="color:{existing}; font-size:20px;">Diese Farbe wird angezeigt</p>',
                #     unsafe_allow_html=True
                # )
                break

        if not too_similar:
            filtered_colors.append(name.replace("xkcd:", ""))
            filtered_hex.append(hex_code)

    # Ergebnis speichern
    with open(FILTER_FILE, "w") as f:
        json.dump(filtered_colors, f)
# st.write("Anzahl aller XKCD-Farben:", len(xkcd))
# st.write("Anzahl nach dem Filtern:", len(filtered_colors))
colors = filtered_colors
FILE = "votes.json"

# ---------- Stimmen laden ----------
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        data = json.load(f)
else:
    data = {}
# alte Daten (nur Punkte) automatisch umwandeln
for color in colors:
    if color not in data:
        data[color] = {"wins": 0, "duels": 0}
    elif isinstance(data[color], int):
        data[color] = {"wins": data[color], "duels": 0}

# ---------- Duell speichern ----------
if "duel" not in st.session_state:
    st.session_state.duel = random.sample(colors, 2)
if "duels" not in st.session_state:
    st.session_state.duels = {c: 0 for c in colors}
    
c1, c2 = st.session_state.duel

st.subheader("Welche Farbe gefällt dir besser?")

# ---------- Farb-Button Funktion ----------
def colored_button(label, key):
    hex_color = mcolors.XKCD_COLORS["xkcd:" + label]
    print(hex_color)
    if show_name:
        button_text = label
    else:
        button_text = " X "
    # Farbfeld anzeigen
    st.markdown(f"""
        <div style="
            background-color:{hex_color};
            height:160px;
            border-radius:20px;
            margin-bottom:10px;
        ">
        </div>
    """, unsafe_allow_html=True)

    # Button darunter
    return st.button(button_text, key=key, use_container_width=True)

    # with stylable_container(
    #     key,
    #     css_styles=f"""
    #     button {{
    #         background-color: {hex_color};
    #         color: black;
    #         height: 150px;
    #         font-size: 22px;
    #         font-weight: bold;
    #         border-radius: 20px;
    #     }}
    #     button:hover {{
    #         background-color: {hex_color} !important;
    #         color: black !important;
    #         border: none !important;
    #         transform: none !important;
    #         box-shadow: none !important;
    #     }}
    
    #    button:active {{
    #         background-color: {hex_color};
    #         color: black;
    #         border: none;
    #     }}
    #     """,
    # ):

    #    return st.button(button_text, key=key, use_container_width=True)

# ---------- Zwei große Farb-Buttons ----------
col1, col2 = st.columns(2)

with col1:
    vote1 = colored_button(c1, f"btn1_{c1}_{c2}")

with col2:
    vote2 = colored_button(c2, f"btn2_{c1}_{c2}")

# ---------- Abstimmen ----------
if vote1:
    data[c1]["wins"] += 1
    data[c2]["wins"] -= 1
    data[c1]["duels"] += 1
    data[c2]["duels"] += 1

    with open(FILE, "w") as f:
        json.dump(data, f)
    st.session_state.duel = random.sample(colors, 2)
    st.rerun()

if vote2:
    data[c2]["wins"] += 1
    data[c1]["wins"] -= 1
    data[c2]["duels"] += 1
    data[c1]["duels"] += 1

    with open(FILE, "w") as f:
        json.dump(data, f)
    st.session_state.duel = random.sample(colors, 2)
    st.rerun()

st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

# ---------- Ranking anzeigen / verbergen ----------
if "show_ranking" not in st.session_state:
    st.session_state.show_ranking = False

if not st.session_state.show_ranking:
    if st.button("Ergebnisse einblenden"):
        st.session_state.show_ranking = True
        st.rerun()
else:
    if st.button("Ergebnisse ausblenden"):
        st.session_state.show_ranking = False
        st.rerun()

# ---------- Ranking ----------
if st.session_state.show_ranking:
    ranking = []

    for color in colors:
        wins = data[color]["wins"]
        duels = data[color]["duels"]
    
        if duels > 0:
            ratio = round((wins + duels) / (2 * duels), 2)*100
        else:
            ratio = 0

        ranking.append((color, wins, duels, ratio))

    # sortieren nach Quote
    ranking = sorted(ranking, key=lambda x: (x[1], x[3]), reverse=True)
    st.markdown(
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[0][0]]};font-size:30px;">Dies</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[1][0]]};font-size:30px;">sind</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[2][0]]};font-size:30px;">die</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[3][0]]};font-size:30px;">schönsten</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[4][0]]};font-size:30px;">Farben.</span>'
        ,
        unsafe_allow_html=True
    )
    st.markdown(
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[-1][0]]};font-size:30px;">Dies</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[-2][0]]};font-size:30px;">sind</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[-3][0]]};font-size:30px;">die</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[-4][0]]};font-size:30px;">hässlichsten</span> '
        f'<span style="color:{mcolors.XKCD_COLORS["xkcd:" + ranking[-5][0]]};font-size:30px;">Farben.</span>'
        ,
        unsafe_allow_html=True
    )
    st.subheader("Aktuelles Ranking")
    for i, (color, wins, duels, ratio) in enumerate(ranking, 1):
        hex_color = mcolors.XKCD_COLORS["xkcd:" + color]
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom:8px;">
                <div style="
                    width:25px;
                    height:25px;
                    background-color:{hex_color};
                    border-radius:6px;
                    border:1px solid black;
                "></div>
    
                    {i}. {color} – {wins} Punkte – Gewinn-Quote: {ratio}% 
            </div>
            """,           
            unsafe_allow_html=True
        )

st.write("")
st.write("")
st.write("")
st.write("")

st.markdown("---")
st.markdown("### Datenverwaltung")

# json_data = json.dumps(data, indent=2)
# st.download_button(
#     label="Ergebnis als JSON herunterladen",
#     data=json_data,
#     file_name="farben_ranking.json",
#     mime="application/json",
# )
# st.markdown("Upload")

# uploaded_file = st.file_uploader("JSON wieder laden", type=["json"])

# if uploaded_file is not None:
#     try:
#         new_data = json.load(uploaded_file)

#         # Sicherheit: prüfen ob Format stimmt
#         for color in new_data:
#             if "wins" not in new_data[color] or "duels" not in new_data[color]:
#                 st.error("Ungültige Datei – falsches Format.")
#                 st.stop()

#         with open(FILE, "w") as f:
#             json.dump(new_data, f)

#         st.success("Daten erfolgreich geladen!")
#         st.rerun()
def upload_to_gsheet(data):
    df = pd.DataFrame([
        {
            "Farbe": color,
            "Punkte": data[color]["wins"],
            "Duelle": data[color]["duels"],
            "HEX": mcolors.XKCD_COLORS["xkcd:" + color],
            "Quote": (
                (data[color]["wins"] + data[color]["duels"]) / (2 * data[color]["duels"])
                if data[color]["duels"] > 0 else 0
            )
        }
        for color in data
    ])

    conn.update(data=df, worksheet="Alle")
def download_from_gsheet():
    st.write("Downloading")
    df = conn.read(worksheet="Alle", ttl = 0)

    if df is None or df.empty:
        return {}
    st.write(df)
    return (
        df.fillna(0)
        .set_index("Farbe")[["Punkte", "Duelle"]]
        .rename(columns={"Punkte": "wins", "Duelle": "duels"})
        .astype(int)
        .to_dict("index")
    )

st.markdown("### 🔄 Synchronisation")

col1, col2 = st.columns(2)

# Upload
if col1.button("⬆️ In Spreadsheet speichern"):
    try:
        upload_to_gsheet(data)
        st.success("Daten ins Spreadsheet hochgeladen!")
    except Exception as e:
        st.error(f"Fehler beim Upload: {e}")

# Download
if col2.button("⬇️ Aus Spreadsheet laden"):
    try:
        new_data = download_from_gsheet()

        if new_data:
            st.write(new_data)
            with open(FILE, "w") as f:
                json.dump(new_data, f)

            st.success("Daten aus Spreadsheet geladen!")
            st.rerun()
        else:
            st.warning("Spreadsheet ist leer.")

    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

if not st.session_state.confirm_reset:
    if st.button("Hard Reset starten"):
        st.session_state.confirm_reset = True
        st.rerun()

else:
    st.warning("Sicher?")

    delete_sheet = st.checkbox("Auch Spreadsheet zurücksetzen?")

    col1, col2 = st.columns(2)

    if col1.button("Ja, alles löschen"):
        # JSON löschen
        if os.path.exists(FILE):
            os.remove(FILE)

        if delete_sheet:
            empty_data = {color: {"wins": 0, "duels": 0} for color in colors}
            upload_to_gsheet(empty_data)

        data = {}

        st.session_state.duel = random.sample(colors, 2)
        st.session_state.duels = {c: 0 for c in colors}
        st.session_state.show_ranking = False
        st.session_state.confirm_reset = False

        if delete_sheet:
            st.success("Alles inkl. Spreadsheet wurde gelöscht.")
        else:
            st.success("Lokale Daten wurden gelöscht.")

        st.rerun()

    if col2.button("Abbrechen"):
        st.session_state.confirm_reset = False
        st.rerun()
