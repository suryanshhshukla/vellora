# 🤟 Vellora

A hand-gesture assistant built with **Streamlit**, **MediaPipe** and **OpenCV**.
Show a gesture to your webcam or type a message, and Vellora replies.

## Features
- Live webcam hand tracking, plus a snapshot mode as a fallback
- 7 gestures, each reported once after being held steady
- Chat with quick-reply buttons
- Optional read-aloud replies (uses the browser's speech engine)
- Dark, responsive interface

## Gestures
| Gesture | Meaning |
|---|---|
| 👍 | Yes / Good |
| 👎 | No / Bad |
| ✋ | Hello / Stop |
| ✊ | Wait |
| ✌️ | Peace / Two |
| ☝️ | Attention / Question |
| 👌 | Small / Little |

## Run locally
Needs Python 3.10 – 3.13.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The first run downloads MediaPipe's hand model (needs internet).

## Tests
```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Deploy on Streamlit Community Cloud
1. Push this repository to GitHub.
2. Sign in at https://share.streamlit.io and create an app from the repository.
3. Set the main file to `app.py` and choose Python 3.12 in the advanced settings.

Live video may not connect on some networks without a TURN server. Use
**Snapshot** mode in that case.

## Project structure
```
app.py               Streamlit interface
vellora/gestures.py  Gesture rules and stabiliser
vellora/tracker.py   MediaPipe hand tracking
vellora/chat.py      Text replies
vellora/ui.py        Styling
tests/               Unit tests
```

## Limitations
Vellora recognises a small set of static gestures using hand-written rules. It
is not a translator for Indian, American or any other sign language.

## Author
Suryansh Mani Shukla
