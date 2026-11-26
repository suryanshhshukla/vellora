"""Styling and small HTML components."""
from html import escape

from .gestures import GESTURES

CSS = """
<style>
.block-container {max-width: 1200px; padding-top: 3.5rem;}
.hero {padding: 26px 30px; border-radius: 20px; margin-bottom: 18px;
  background: linear-gradient(120deg, #0f766e 0%, #1e3a8a 60%, #312e81 100%);}
.hero h1 {margin: 0; padding: 0; font-size: 2.4rem; color: #fff; letter-spacing: -0.5px;}
.hero p {margin: 6px 0 0; color: #dbeafe; font-size: 1.02rem;}
.card {display: flex; align-items: center; gap: 18px; padding: 16px 20px;
  border-radius: 16px; background: #172033; border: 1px solid #27344f; margin: 8px 0;}
.card.active {border-color: #2dd4bf; box-shadow: 0 0 0 1px #2dd4bf55;}
.card .emoji {font-size: 3rem; line-height: 1;}
.card .label {font-size: .72rem; text-transform: uppercase; letter-spacing: 1.2px; color: #94a3b8;}
.card .value {font-size: 1.3rem; font-weight: 700; color: #f1f5f9;}
.guide {display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 12px;}
.tile {padding: 16px 12px; text-align: center; border-radius: 16px;
  background: #172033; border: 1px solid #27344f; transition: transform .15s, border-color .15s;}
.tile:hover {transform: translateY(-3px); border-color: #2dd4bf;}
.tile .emoji {font-size: 2.4rem;}
.tile b {display: block; color: #f1f5f9; margin: 4px 0;}
.tile span {font-size: .8rem; color: #94a3b8;}
</style>
"""

HERO = """
<div class="hero">
  <h1>🤟 Vellora</h1>
  <p>Show a hand gesture or type a message, and Vellora replies.</p>
</div>
"""


def gesture_card(label, key, empty_text):
    gesture = GESTURES.get(key)
    emoji = gesture.emoji if gesture else "🖐️"
    value = gesture.meaning if gesture else empty_text
    active = " active" if gesture else ""
    return (
        f'<div class="card{active}"><div class="emoji">{emoji}</div><div>'
        f'<div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(value)}</div></div></div>'
    )


def guide_grid():
    tiles = "".join(
        f'<div class="tile"><div class="emoji">{g.emoji}</div>'
        f"<b>{escape(g.meaning)}</b><span>{escape(g.how_to)}</span></div>"
        for g in GESTURES.values()
    )
    return f'<div class="guide">{tiles}</div>'
