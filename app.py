"""Vellora: Streamlit entry point. Run with `streamlit run app.py`."""
import hashlib
import json
from datetime import datetime

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer

from vellora import ui
from vellora.chat import reply_to
from vellora.gestures import GESTURES
from vellora.tracker import LiveSession, annotate, create_landmarker, to_mp_image

st.set_page_config(page_title="Vellora", page_icon="🤟", layout="wide")

WELCOME = "Hello! I can recognise hand gestures and reply. How can I help you today?"
QUICK_REPLIES = ["Hello", "Thank you", "Yes", "No", "Help", "I need assistance"]


# ---------- state ----------
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.response_sign = "OPEN_PALM"
        st.session_state.pending_speech = None
        add_message("assistant", WELCOME)


def add_message(role, text):
    st.session_state.messages.append(
        {"role": role, "text": text, "time": datetime.now().strftime("%H:%M")}
    )


def add_bot_reply(text, sign):
    add_message("assistant", text)
    st.session_state.response_sign = sign
    st.session_state.pending_speech = text


def send_text(text):
    add_message("user", text)
    add_bot_reply(*reply_to(text))


def send_gesture(key):
    gesture = GESTURES[key]
    add_message("user", f"{gesture.emoji} *Gesture:* {gesture.meaning}")
    add_bot_reply(gesture.reply, key)


def submit_chat_input():
    text = (st.session_state.chat_text or "").strip()
    if text:
        send_text(text)


def clear_chat():
    del st.session_state.messages


# ---------- camera ----------
@st.cache_resource(show_spinner="Loading the hand-tracking model...")
def image_landmarker():
    return create_landmarker(video=False)


def live_camera(hold_seconds):
    if "live" not in st.session_state:
        with st.spinner("Loading the hand-tracking model..."):
            st.session_state.live = LiveSession()
    session = st.session_state.live
    session.set_hold_seconds(hold_seconds)

    # Runs in a separate thread, so it must not touch st.session_state.
    def on_frame(frame):
        image = session.process(frame.to_ndarray(format="bgr24"))
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    context = webrtc_streamer(
        key="vellora-camera",
        video_frame_callback=on_frame,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    playing = context.state.playing

    @st.fragment(run_every=0.4 if playing else None)
    def detection_status():
        events = session.pop_events()
        if events:
            for key in events:
                send_gesture(key)
            st.rerun()  # refresh the chat and response card
        if session.error:
            st.error(f"Hand tracking failed: {session.error}")
        st.markdown(
            ui.gesture_card(
                "Detected gesture",
                session.current if playing else None,
                "Hold a gesture steady" if playing else "Press START to turn on the camera",
            ),
            unsafe_allow_html=True,
        )

    detection_status()


def snapshot_camera():
    photo = st.camera_input("Take a photo of your gesture")
    if photo is None:
        return
    data = photo.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    if st.session_state.get("last_photo") != digest:
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        image = cv2.flip(image, 1)
        key = annotate(image, image_landmarker().detect(to_mp_image(image)))
        st.session_state.last_photo = digest
        st.session_state.photo_result = (image, key)
        if key:
            send_gesture(key)
    image, key = st.session_state.photo_result
    st.image(image, channels="BGR", width="stretch")
    if not key:
        st.warning("No gesture recognised. Keep your whole hand in frame and try again.")


# ---------- audio ----------
def speak(text):
    """Read text aloud in the visitor's browser."""
    # Escape "<" so the text can never close the script tag.
    safe = json.dumps(text).replace("<", "\\u003c")
    count = len(st.session_state.messages)  # makes each script unique
    st.html(
        f"""<script>/* {count} */
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance({safe});
        u.rate = 0.95;
        window.speechSynthesis.speak(u);
        </script>""",
        unsafe_allow_javascript=True,
    )


# ---------- page ----------
init_state()
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.HERO, unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Camera mode", ["Live video", "Snapshot"],
                    help="Use Snapshot if live video does not connect on your network.")
    hold = st.slider("Hold time before a gesture counts (seconds)", 0.3, 2.0, 0.8, 0.1,
                     disabled=mode != "Live video")
    audio_on = st.toggle("🔊 Read replies aloud")
    st.button("🗑️ Clear chat", on_click=clear_chat, width="stretch")
    st.divider()
    st.caption("Vellora recognises 7 hand gestures. It is not a full sign-language translator.")

camera_column, chat_column = st.columns([1.1, 1], gap="large")

with camera_column:
    st.subheader("📹 Camera")
    try:
        if mode == "Live video":
            live_camera(hold)
        else:
            snapshot_camera()
    except OSError as error:
        st.error(f"Could not load hand tracking: {error}. "
                 "Check your internet connection (the model downloads on first run).")

with chat_column:
    st.subheader("💬 Chat")
    st.markdown(
        ui.gesture_card("Vellora's sign response", st.session_state.response_sign, "No response yet"),
        unsafe_allow_html=True,
    )
    history = st.container(height=360, border=True)
    with history:
        for message in st.session_state.messages:
            avatar = "🤟" if message["role"] == "assistant" else "🧑"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["text"])
                st.caption(message["time"])
    quick = st.columns(3)
    for index, label in enumerate(QUICK_REPLIES):
        quick[index % 3].button(label, on_click=send_text, args=(label,), width="stretch")
    st.chat_input("Type a message", key="chat_text", on_submit=submit_chat_input)

st.subheader("✨ Gesture guide")
st.markdown(ui.guide_grid(), unsafe_allow_html=True)

speech, st.session_state.pending_speech = st.session_state.pending_speech, None
if audio_on and speech:
    speak(speech)
