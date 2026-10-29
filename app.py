import json
import time
import unicodedata

import streamlit as st
import paho.mqtt.client as paho
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# ───────────────────────── Config ─────────────────────────
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "tefaweb005"
CLIENT_ID = "GIT-HUBC"

st.set_page_config(page_title="Walkie Multimodal", page_icon="📻", layout="centered")

# Paleta LCD
LCD_BG = "#9bbc0f"
LCD_LIGHT = "#c4e86a"
LCD_MID = "#306230"
LCD_DARK = "#0f380f"

# ───────────────────────── Estado ─────────────────────────
if "accion" not in st.session_state:
    st.session_state.accion = None          # door_open, door_close, light_on, light_off, unknown
    st.session_state.puerta = "---"
    st.session_state.luz = "---"
    st.session_state.texto = ""
    st.session_state.ultimo = None
    st.session_state.enviado = None


# ───────────────────────── MQTT ─────────────────────────
def on_publish(client, userdata, result):
    print("el dato ha sido publicado \n")


def publicar(texto: str) -> bool:
    try:
        try:  # paho-mqtt 2.x
            client = paho.Client(paho.CallbackAPIVersion.VERSION1, CLIENT_ID)
        except AttributeError:  # paho-mqtt 1.x
            client = paho.Client(CLIENT_ID)
        client.on_publish = on_publish
        client.connect(BROKER, PORT)
        client.publish(TOPIC, json.dumps({"Act1": texto}))
        client.disconnect()
        return True
    except Exception as e:
        print("Error MQTT:", e)
        return False


# ───────────────────────── Interpretar comando ─────────────────────────
def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def interpretar(texto: str):
    t = normalizar(texto)
    if any(p in t for p in ["puerta", "porton"]):
        if any(v in t for v in ["cierr", "cerr"]):
            return "door_close"
        if any(v in t for v in ["abr"]):
            return "door_open"
    if any(p in t for p in ["luz", "luces", "bombillo", "lampara", "foco"]):
        if "apag" in t:
            return "light_off"
        if any(v in t for v in ["enciend", "encend", "prend"]):
            return "light_on"
    return "unknown"


# ───────────────────────── SVG: carita ─────────────────────────
def face_svg(mood: str) -> str:
    s = f'stroke="{LCD_DARK}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    head = f'<circle cx="85" cy="80" r="50" {s}/>'

    if mood == "happy":
        eyes = f'<path d="M60 74 Q68 62 76 74" {s}/><path d="M94 74 Q102 62 110 74" {s}/>'
        mouth = f'<path d="M62 92 Q85 124 108 92 Z" fill="{LCD_DARK}" stroke="{LCD_DARK}" stroke-width="4" stroke-linejoin="round"/>'
        extra = f'<circle cx="56" cy="92" r="5" fill="{LCD_MID}"/><circle cx="114" cy="92" r="5" fill="{LCD_MID}"/>'
    elif mood == "calm":
        eyes = f'<circle cx="68" cy="72" r="5" fill="{LCD_DARK}"/><circle cx="102" cy="72" r="5" fill="{LCD_DARK}"/>'
        mouth = f'<path d="M70 100 Q85 107 100 100" {s}/>'
        extra = ""
    elif mood == "wow":
        eyes = (f'<circle cx="68" cy="70" r="9" {s}/><circle cx="68" cy="70" r="3" fill="{LCD_DARK}"/>'
                f'<circle cx="102" cy="70" r="9" {s}/><circle cx="102" cy="70" r="3" fill="{LCD_DARK}"/>')
        mouth = f'<ellipse cx="85" cy="104" rx="8" ry="10" fill="{LCD_DARK}"/>'
        extra = ""
    elif mood == "sleepy":
        eyes = f'<path d="M60 73 Q68 78 76 73" {s}/><path d="M94 73 Q102 78 110 73" {s}/>'
        mouth = f'<path d="M78 102 Q85 98 92 102" {s}/>'
        extra = (f'<text x="128" y="40" class="zz" font-family="VT323, monospace" font-size="22" fill="{LCD_DARK}">z</text>'
                 f'<text x="140" y="26" class="zz zz2" font-family="VT323, monospace" font-size="16" fill="{LCD_DARK}">z</text>')
    elif mood == "confused":
        eyes = f'<circle cx="68" cy="72" r="5" fill="{LCD_DARK}"/><path d="M94 66 L110 74" {s}/>'
        mouth = f'<path d="M66 102 L74 97 L82 103 L90 97 L98 103 L106 97" {s}/>'
        extra = ""
    else:  # idle
        eyes = (f'<g class="blink"><circle cx="68" cy="72" r="5" fill="{LCD_DARK}"/>'
                f'<circle cx="102" cy="72" r="5" fill="{LCD_DARK}"/></g>')
        mouth = f'<path d="M66 96 Q85 112 104 96" {s}/>'
        extra = ""

    return f'<g class="face-pop">{head}{eyes}{mouth}{extra}</g>'


# ───────────────────────── SVG: íconos ─────────────────────────
def icon_svg(accion: str) -> str:
    d, m, l = LCD_DARK, LCD_MID, LCD_LIGHT
    if accion == "door_open":
        return f'''
        <rect x="190" y="28" width="64" height="104" fill="{d}"/>
        <path d="M204 60 L240 60 M204 80 L236 80 M204 100 L240 100" stroke="{l}" stroke-width="3" stroke-linecap="round" class="shine"/>
        <rect x="190" y="28" width="64" height="104" fill="none" stroke="{d}" stroke-width="5"/>
        <g class="swing-open">
          <polygon points="190,28 222,40 222,120 190,132" fill="{l}" stroke="{d}" stroke-width="4" stroke-linejoin="round"/>
          <circle cx="216" cy="82" r="3.5" fill="{d}"/>
        </g>'''
    if accion == "door_close":
        return f'''
        <rect x="190" y="28" width="64" height="104" fill="none" stroke="{d}" stroke-width="5"/>
        <g class="swing-close">
          <rect x="190" y="28" width="64" height="104" fill="{l}" stroke="{d}" stroke-width="4"/>
          <rect x="200" y="38" width="44" height="36" fill="none" stroke="{m}" stroke-width="3"/>
          <rect x="200" y="84" width="44" height="38" fill="none" stroke="{m}" stroke-width="3"/>
          <circle cx="245" cy="80" r="4" fill="{d}"/>
        </g>'''
    if accion == "light_on":
        rays = "".join(
            f'<line x1="{222 + 34 * c}" y1="{66 + 34 * s}" x2="{222 + 46 * c}" y2="{66 + 46 * s}" stroke="{d}" stroke-width="4" stroke-linecap="round"/>'
            for c, s in [(1, 0), (-1, 0), (0, -1), (0.7, -0.7), (-0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)]
        )
        return f'''
        <g class="rays">{rays}</g>
        <g class="glow">
          <circle cx="222" cy="66" r="26" fill="{l}" stroke="{d}" stroke-width="4"/>
          <path d="M212 74 Q217 60 222 74 Q227 60 232 74" fill="none" stroke="{d}" stroke-width="3" stroke-linecap="round"/>
        </g>
        <rect x="210" y="92" width="24" height="8" rx="2" fill="{d}"/>
        <rect x="212" y="102" width="20" height="7" rx="2" fill="{d}"/>
        <rect x="216" y="111" width="12" height="5" rx="2" fill="{d}"/>'''
    if accion == "light_off":
        return f'''
        <g class="dim">
          <circle cx="222" cy="66" r="26" fill="{m}" stroke="{d}" stroke-width="4"/>
          <path d="M212 74 Q217 60 222 74 Q227 60 232 74" fill="none" stroke="{LCD_BG}" stroke-width="3" stroke-linecap="round" opacity=".6"/>
        </g>
        <rect x="210" y="92" width="24" height="8" rx="2" fill="{d}"/>
        <rect x="212" y="102" width="20" height="7" rx="2" fill="{d}"/>
        <rect x="216" y="111" width="12" height="5" rx="2" fill="{d}"/>'''
    if accion == "unknown":
        return f'<text x="222" y="104" text-anchor="middle" class="face-pop" font-family="VT323, monospace" font-size="96" fill="{d}">?</text>'
    # idle: ondas de radio
    return f'''
    <circle cx="200" cy="80" r="6" fill="{d}"/>
    <path d="M214 62 Q226 80 214 98" class="wave w1" fill="none" stroke="{d}" stroke-width="5" stroke-linecap="round"/>
    <path d="M228 50 Q246 80 228 110" class="wave w2" fill="none" stroke="{d}" stroke-width="5" stroke-linecap="round"/>
    <path d="M242 38 Q266 80 242 122" class="wave w3" fill="none" stroke="{d}" stroke-width="5" stroke-linecap="round"/>'''


INFO = {
    None:         ("idle",     "LISTO PARA HABLAR"),
    "door_open":  ("happy",    "PUERTA ABIERTA"),
    "door_close": ("calm",     "PUERTA CERRADA"),
    "light_on":   ("wow",      "LUCES ENCENDIDAS"),
    "light_off":  ("sleepy",   "LUCES APAGADAS"),
    "unknown":    ("confused", "NO ENTENDI :("),
}


def pantalla_html(accion, puerta, luz, texto, tx_ok) -> str:
    mood, estado = INFO.get(accion, INFO[None])
    tx = "TX OK" if tx_ok else ("TX ERR" if tx_ok is False else "RX")
    texto_lcd = (texto[:38] + "…") if len(texto) > 38 else texto
    return f'''
<div class="lcd">
  <div class="lcd-bar"><span>PTA:{puerta}</span><span>LUZ:{luz}</span><span>{tx}</span></div>
  <svg viewBox="0 0 300 168" xmlns="http://www.w3.org/2000/svg" key="{accion}-{time.time()}">
    {face_svg(mood)}
    {icon_svg(accion)}
    <text x="150" y="160" text-anchor="middle" font-family="VT323, monospace" font-size="22" fill="{LCD_DARK}">{estado}</text>
  </svg>
  <div class="lcd-text">&gt; {texto_lcd or "toca HABLAR y di un comando"}</div>
</div>'''


# ───────────────────────── CSS ─────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Inter:wght@400;600;800&display=swap');

.stApp { background: radial-gradient(circle at 50% 0%, #2a2f3a 0%, #12141a 70%); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; }

.wt-title { text-align:center; font-family:Inter, sans-serif; color:#e8ecf3; font-weight:800;
            letter-spacing:.18em; font-size:1.05rem; margin:0; }
.wt-sub { text-align:center; font-family:Inter, sans-serif; color:#8a93a6; font-size:.8rem;
          letter-spacing:.3em; margin:.2rem 0 4.5rem; }

/* Cuerpo del walkie */
.st-key-walkie {
  position: relative; max-width: 330px; margin: 0 auto 1rem; padding: 22px 22px 26px;
  background: linear-gradient(160deg, #3b4150 0%, #23272f 55%, #1a1d23 100%);
  border-radius: 34px 34px 46px 46px;
  border: 2px solid #4b5263;
  box-shadow: inset 0 2px 0 rgba(255,255,255,.08), inset 0 -6px 12px rgba(0,0,0,.45),
              0 24px 50px rgba(0,0,0,.55);
  overflow: visible !important;
}
.antenna { position:absolute; top:-74px; left:44px; width:20px; height:84px; border-radius:10px 10px 4px 4px;
           background: linear-gradient(90deg,#15171c,#3a3f4b,#15171c); }
.antenna::after { content:""; position:absolute; top:-6px; left:2px; width:16px; height:12px;
                  border-radius:8px; background:#e04848; box-shadow:0 0 10px #e04848; }
.knob { position:absolute; top:-26px; right:46px; width:34px; height:30px; border-radius:8px 8px 4px 4px;
        background: repeating-linear-gradient(90deg,#2a2e37 0 4px,#444a57 4px 8px); }

.wt-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;
           font-family:Inter, sans-serif; font-size:.7rem; color:#9aa3b5; letter-spacing:.15em; }
.led { width:10px; height:10px; border-radius:50%; background:#44e07a; box-shadow:0 0 8px #44e07a;
       display:inline-block; margin-right:6px; animation: led 1.6s infinite; }
@keyframes led { 50% { opacity:.35; } }

.grill { height:54px; border-radius:14px; margin-bottom:16px; background:#14161b;
         background-image: radial-gradient(#3a3f4b 30%, transparent 32%);
         background-size: 11px 11px; box-shadow: inset 0 3px 6px rgba(0,0,0,.7); }

/* Pantalla LCD */
.lcd { background:#9bbc0f; border-radius:12px; padding:8px 10px 10px; border:6px solid #11131a;
       box-shadow: inset 0 0 18px rgba(15,56,15,.55), 0 0 0 2px #50586a; }
.lcd svg { width:100%; height:auto; display:block; }
.lcd-bar { display:flex; justify-content:space-between; font-family:VT323, monospace; font-size:1.05rem;
           color:#0f380f; border-bottom:2px dashed #306230; padding-bottom:2px; }
.lcd-text { font-family:VT323, monospace; font-size:1.05rem; color:#0f380f; border-top:2px dashed #306230;
            padding-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.ptt-label { text-align:center; font-family:Inter, sans-serif; font-size:.72rem; color:#9aa3b5;
             letter-spacing:.2em; margin:18px 0 4px; }
.st-key-walkie iframe { display:block; margin:0 auto; color-scheme: normal; }

.keypad { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.keypad span { height:22px; border-radius:7px; background:linear-gradient(#3a3f4b,#2a2e37);
               box-shadow:0 3px 0 #121419; }
.hint { text-align:center; font-family:Inter, sans-serif; font-size:.75rem; color:#7d869a; margin-top:6px; }

/* Animaciones SVG */
.lcd svg * { transform-box: fill-box; }
.face-pop { animation: pop .45s ease-out; transform-origin:center; }
@keyframes pop { 0% { transform:scale(.6); opacity:0; } 70% { transform:scale(1.08); } 100% { transform:scale(1); opacity:1; } }
.blink { animation: blink 4s infinite; transform-origin:center; }
@keyframes blink { 0%,92%,100% { transform:scaleY(1); } 95% { transform:scaleY(.1); } }
.swing-open { animation: swingOpen .9s ease-out; transform-origin:left center; }
@keyframes swingOpen { from { transform:scaleX(2); } to { transform:scaleX(1); } }
.swing-close { animation: swingClose .7s ease-in; transform-origin:left center; }
@keyframes swingClose { from { transform:scaleX(.45); } to { transform:scaleX(1); } }
.shine { animation: shine 1.4s ease-out; }
@keyframes shine { from { opacity:0; } to { opacity:1; } }
.glow { animation: glow 1.2s ease-in-out infinite; transform-origin:center; }
@keyframes glow { 50% { transform:scale(1.07); } }
.rays { animation: rays 1.2s ease-in-out infinite; transform-origin:center; }
@keyframes rays { 50% { opacity:.35; } }
.dim { animation: dim .8s ease-out; }
@keyframes dim { 0% { opacity:1; } 30% { opacity:.3; } 60% { opacity:.8; } 100% { opacity:1; } }
.zz { animation: zz 2s ease-in-out infinite; }
.zz2 { animation-delay: .6s; }
@keyframes zz { 0% { opacity:0; transform:translateY(6px); } 50% { opacity:1; } 100% { opacity:0; transform:translateY(-8px); } }
.wave { animation: wave 1.8s infinite; }
.w2 { animation-delay:.3s; } .w3 { animation-delay:.6s; }
@keyframes wave { 0%,100% { opacity:.2; } 50% { opacity:1; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ───────────────────────── Botón de voz (Bokeh) ─────────────────────────
stt_button = Button(label="🎙  HABLAR", width=200, height=48, button_type="danger")
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

# ───────────────────────── UI ─────────────────────────
st.markdown('<p class="wt-title">INTERFACES MULTIMODALES</p><p class="wt-sub">CONTROL POR VOZ</p>',
            unsafe_allow_html=True)

with st.container(key="walkie"):
    st.markdown(
        '<div class="antenna"></div><div class="knob"></div>'
        '<div class="wt-head"><span><span class="led"></span>ON AIR</span><span>MULTI-01</span><span>CH 05</span></div>'
        '<div class="grill"></div>',
        unsafe_allow_html=True,
    )
    pantalla = st.empty()
    st.markdown('<div class="ptt-label">PUSH TO TALK</div>', unsafe_allow_html=True)

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=60,
        debounce_time=0,
    )

    st.markdown(
        '<div class="keypad">' + "<span></span>" * 6 + "</div>"
        '<div class="hint">"abre la puerta" · "cierra la puerta"<br>"enciende las luces" · "apaga las luces"</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────── Lógica ─────────────────────────
if result and "GET_TEXT" in result:
    texto = result.get("GET_TEXT").strip()
    if texto and texto != st.session_state.ultimo:
        st.session_state.ultimo = texto
        st.session_state.texto = texto
        accion = interpretar(texto)
        st.session_state.accion = accion
        if accion == "door_open":
            st.session_state.puerta = "ABIERTA"
        elif accion == "door_close":
            st.session_state.puerta = "CERRADA"
        elif accion == "light_on":
            st.session_state.luz = "ON"
        elif accion == "light_off":
            st.session_state.luz = "OFF"
        st.session_state.enviado = publicar(texto)

pantalla.markdown(
    pantalla_html(
        st.session_state.accion,
        st.session_state.puerta,
        st.session_state.luz,
        st.session_state.texto,
        st.session_state.enviado,
    ),
    unsafe_allow_html=True,
)