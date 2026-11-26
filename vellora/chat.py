"""Rule-based replies for typed messages."""
import re

# Order matters: the first matching rule wins.
_RULES = [
    ({"thank", "thanks"}, "You're welcome! Is there anything else you need?", "THUMBS_UP"),
    ({"help", "assistance"}, "I'm here to help. You can show a gesture or type your question.", "OPEN_PALM"),
    ({"hello", "hi", "hey"}, "Hello! How can I help you today?", "OPEN_PALM"),
    ({"no", "nope", "not", "don't", "bad", "wrong"},
     "I understand. Let me know if you need something else.", "THUMBS_DOWN"),
    ({"yes", "yeah", "ok", "okay", "sure", "good", "fine"},
     "Great! What would you like to do next?", "THUMBS_UP"),
    ({"wait", "hold", "stop", "pause"}, "Sure, I'll wait.", "CLOSED_FIST"),
    ({"peace", "two", "both"}, "Peace! Do you need help with two options?", "PEACE_SIGN"),
    ({"small", "little", "tiny", "bit"}, "Got it, something small.", "PINCH"),
    ({"what", "how", "when", "where", "why"},
     "Good question. I can answer simple greetings and requests.", "POINTING_UP"),
]


def reply_to(text):
    """Return (reply_text, gesture_key) for a typed message."""
    cleaned = text.lower().replace("’", "'")
    # Whole words only, so "this" doesn't count as "hi".
    words = set(re.findall(r"[a-z']+", cleaned))
    for keywords, reply, gesture in _RULES:
        if words & keywords:
            return reply, gesture
    if "?" in cleaned:
        return "Good question. I can answer simple greetings and requests.", "POINTING_UP"
    return "I understand your message. How else can I assist you?", "OPEN_PALM"
