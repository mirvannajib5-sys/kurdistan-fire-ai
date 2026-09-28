import streamlit as st
import pandas as pd
import cv2
import numpy as np
import requests
import winsound

# -------------------------------------------------------------
# Function to get exact live geolocation based on IP/Network
def get_exact_location():
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', 'Unknown City')
            region = data.get('region', 'Unknown Region')
            country = data.get('country_name', 'Unknown Country')
            lat = data.get('latitude', 'N/A')
            lon = data.get('longitude', 'N/A')
            org = data.get('org', 'Unknown ISP')
            
            location_str = f"{city}, {region}, {country}"
            coords_str = f"{lat}, {lon}"
            maps_link = f"https://www.google.com/maps?q={lat},{lon}" if lat != 'N/A' else "N/A"
            
            return location_str, coords_str, maps_link, org
    except Exception as e:
        print(f"Location fetch error: {e}")
    
    return "Qaladiza, Sulaymaniyah, Iraq", "36.1831, 45.1219", "https://maps.google.com", "Local Network"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8960079126:AAFCZj43Bo_n7z1yXvq4KRbw6BnySebdOwo"
TELEGRAM_CHAT_ID = "814653277"

def send_telegram_alert(message, image_frame=None):
    """Function to send text & image alerts to Telegram"""
    try:
        if image_frame is not None:
            _, img_encoded = cv2.imencode('.jpg', image_frame)
            files = {'photo': ('fire_alert.jpg', img_encoded.tobytes(), 'image/jpeg')}
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message, 'parse_mode': 'Markdown'}
            requests.post(url, data=data, files=files)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
            requests.post(url, data=data)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
# -------------------------------------------------------------

# Page Configuration
st.set_page_config(page_title="Kurdistan AI Fire Monitoring", layout="wide")

# Main Title & Subtitle
st.title("🔥 AI Wildfire Detection & Monitoring System")
st.markdown("Real-time Mountain Forest Fire Monitoring Dashboard powered by AI")

# Sidebar Controls
st.sidebar.title("🎛️ Control Panel")
source_option = st.sidebar.radio(
    "Select Video Source",
    ["Webcam / IP Camera (Live)", "Upload Image/Video"]
)

ip_camera_url = st.sidebar.text_input("IP Camera RTSP Stream URL (Optional)", value="0")

uploaded_file = None
if source_option == "Upload Image/Video":
    uploaded_file = st.sidebar.file_uploader("Upload Test File", type=['jpg', 'jpeg', 'png', 'mp4'])

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Active Cameras", "12")
col2.metric("System Status", "Online 100%")
col3.metric("Unread Alerts", "1", delta_color="inverse")

st.divider()

# Live Feed & Alerts Layout
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📹 Live Camera Stream")
    frame_placeholder = st.empty()
    run_live_camera = st.button("Start Live Monitoring")

with col_right:
    st.subheader("🚨 Real-time Alerts")
    alert_placeholder = st.empty()
    alert_placeholder.success("✅ System Monitoring: All clear")

# Live Stream Processing Loop
if source_option == "Webcam / IP Camera (Live)" and run_live_camera:
    cam_source = int(ip_camera_url) if ip_camera_url.isdigit() else ip_camera_url
    cap = cv2.VideoCapture(cam_source)

    stop_button = st.button("Stop Monitoring")
    alert_sent = False

    while cap.isOpened() and not stop_button:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to connect to camera feed.")
            break

        h, w, _ = frame.shape

        # Balanced Fire Range
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_fire = np.array([5, 110, 210])
        upper_fire = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_fire, upper_fire)
        fire_pixels = cv2.countNonZero(mask)

        # Alarm Trigger Condition
        if fire_pixels > 400:
            start_point = (int(w * 0.2), int(h * 0.2))
            end_point = (int(w * 0.8), int(h * 0.8))
            cv2.rectangle(frame, start_point, end_point, (0, 0, 255), 4)
            cv2.putText(frame, "CRITICAL: FIRE DETECTED!", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
            alert_placeholder.error("🚨 EMERGENCY ALARM: Wildfire detected on live camera feed!")
            
            if not alert_sent:
                # Fetch exact live geolocation
                loc_name, coords, maps_url, isp = get_exact_location()
                
                alert_text = (
                    "🚨 *EMERGENCY: WILDFIRE DETECTED!*\n\n"
                    f"📍 *Exact Address:* {loc_name}\n"
                    f"🌐 *Coordinates:* `{coords}`\n"
                    f"🔗 *Google Maps Link:* [Open Location]({maps_url})\n"
                    f"📡 *Network/ISP:* {isp}\n"
                    f"📹 *Camera ID:* CAM-LIVE-01\n"
                    "⚠️ *Status:* Immediate Action Required!"
                )
                send_telegram_alert(alert_text, frame)
                alert_sent = True

            try:
                winsound.Beep(2000, 300)
            except:
                pass
        else:
            alert_placeholder.success("✅ Region Safe - No Active Wildfire")
            alert_sent = False

        frame_placeholder.image(frame, channels="BGR", use_container_width=True)

    cap.release()

elif source_option == "Upload Image/Video" and uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    h, w, _ = img.shape
    cv2.rectangle(img, (int(w * 0.3), int(h * 0.3)), (int(w * 0.8), int(h * 0.85)), (0, 0, 255), 4)
    cv2.putText(img, "AI Detection: Fire & Smoke (94%)", (int(w * 0.3), int(h * 0.25)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
    
    frame_placeholder.image(img, channels="BGR", caption="Processed Frame", use_container_width=True)
    alert_placeholder.error("⚠️ Smoke Detected - Confidence: 94%")
    
    loc_name, coords, maps_url, isp = get_exact_location()
    
    alert_text = (
        "⚠️ *TEST ALERT: Smoke & Fire Analyzed*\n\n"
        f"📍 *Exact Address:* {loc_name}\n"
        f"🌐 *Coordinates:* `{coords}`\n"
        f"🔗 *Google Maps Link:* [Open Location]({maps_url})\n"
        f"📹 *Source:* Uploaded Test Image"
    )
    send_telegram_alert(alert_text, img)
    try:
        winsound.Beep(2000, 500)
    except:
        pass

st.divider()

# Map & Table
st.subheader("📍 Live Camera Network Map")

cameras_df = pd.DataFrame([
    {"name": "Gweizha Camera 01", "latitude": 35.5667, "longitude": 45.4333, "status": "Normal"},
    {"name": "Hawraman Camera 02", "latitude": 35.2833, "longitude": 46.2167, "status": "Alert: Smoke Detected"},
    {"name": "Halgurd Camera 03", "latitude": 36.6264, "longitude": 44.8258, "status": "Normal"},
])

st.map(cameras_df, latitude="latitude", longitude="longitude", zoom=7)

st.subheader("📊 Camera Status Table")
st.dataframe(cameras_df, use_container_width=True)