# Sloka Meter Visualizer  —  Skrutable-powered
# (c) 2025  Svetlana Kreuzer

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re, unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ────── NEW:  Skrutable imports ────────────────────────────────────────────
from skrutable.splitting import Splitter
from skrutable.metrics   import is_heavy                # guru / laghu test
from skrutable.patterns  import VIPULA_MAP, PATHYA_TEST
from skrutable.alankara  import (
    detect_padaadi_yamaka,
    detect_padaanta_yamaka,
    detect_vrtty_anuprasa
)

# instantiate once (latest model)
SPLITTER = Splitter(model='splitter_2024')

# vipulā colour table (unchanged)
VIPULA_COL = {
    'Nagari': '#FF7F00', 'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57', 'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}

# ────── TEXT HELPERS ───────────────────────────────────────────────────────
def normalize(iast: str) -> str:
    """IAST → NFC-normalised SLP-1, punctuation stripped."""
    iast = unicodedata.normalize('NFC', iast.strip())
    iast = re.sub(r'[।॥|,.;:!?\"\'()\\[\\]{}⟨⟩—–-\\d]', '', iast)
    return transliterate(iast, sanscript.IAST, sanscript.SLP1)

def split_syllables(line_iast: str):
    """Delegate to Skrutable splitter — returns list[SLP1-syllable]."""
    return SPLITTER.split(line_iast, preserve_punctuation=False)

# ────── PROSODY WRAPPERS ───────────────────────────────────────────────────
def g_or_l(syll):
    return 'g' if is_heavy(syll) else 'l'

def vipula_name(syllables):
    pattern = ''.join(g_or_l(s) for s in syllables[:4])
    return VIPULA_MAP.get(pattern)

# Skrutable already gives booleans for the rest:
#   PATHYA_TEST (expects list[str] of 'g'/'l' for 32-syl block)
#   detect_padaadi_yamaka / detect_padaanta_yamaka (32)  —> bool
#   detect_vrtty_anuprasa (line)                        —> bool

# ────── VISUALISATION ──────────────────────────────────────────────────────
def draw(lines):
    rows, cols = len(lines), max(len(r) for r in lines)
    disp = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in r] for r in lines]
    flat = [s for r in lines for s in r]

    fig, ax = plt.subplots(figsize=(cols*0.55, rows*0.55))
    ax.set(xlim=(0, cols), ylim=(0, rows)); ax.axis('off'); ax.set_aspect('equal')

    # cells + text
    for r,row in enumerate(lines):
        y = rows-1-r
        for c, syl in enumerate(row):
            g = is_heavy(syl)
            ax.add_patch(Rectangle((c,y),1,1,
                         facecolor='black' if g else 'white',
                         edgecolor='gray', zorder=1))
            ax.text(c+0.5, y+0.5, disp[r][c],
                    ha='center', va='center',
                    color='white' if g else 'black',
                    fontsize=9, zorder=2)

    # vipulā fill & line-level anuprāsa
    for r,row in enumerate(lines):
        y = rows-1-r
        vip = vipula_name(row)
        if vip:
            ax.add_patch(Rectangle((0,y), min(4,len(row)), 1,
                                   facecolor=VIPULA_COL[vip], alpha=0.45, zorder=3))
        if detect_vrtty_anuprasa(row):
            ax.add_patch(Rectangle((0,y), len(row), 1,
                                   fill=False, edgecolor='purple', lw=2, zorder=4))

    # 32-syllable block tests
    for i in range(0, len(flat), 32):
        blk = flat[i:i+32]
        if len(blk) < 32: break
        g_l = [g_or_l(s) for s in blk]
        row0 = i // cols
        y0   = rows - 1 - row0 - 1
        if y0 < 0: continue
        w = min(cols, 8)
        if PATHYA_TEST(g_l):
            ax.add_patch(Rectangle((0,y0), w, 2,
                                   fill=False, edgecolor='blue', lw=2.5, zorder=5))
        if detect_padaadi_yamaka(blk):
            ax.add_patch(Rectangle((0,y0), w, 2,
                                   fill=False, edgecolor='green',
                                   lw=2, linestyle='--', zorder=5))
        if detect_padaanta_yamaka(blk):
            ax.add_patch(Rectangle((0,y0), w, 2,
                                   fill=False, edgecolor='red',
                                   lw=2, linestyle=':', zorder=5))

    st.pyplot(fig); plt.close(fig)

# ────── STREAMLIT UI ────────────────────────────────────────────────────────
st.set_page_config(page_title='Sloka Meter', layout='wide')
st.title('Sloka Meter Visualizer')

st.markdown(
    '*Paste IAST lines, separated by `|`, `।` or `॥`. '
    'Click **Show** for guru/laghu squares, vipulā colours, and '
    'yamaka / anuprāsa / pathyā frames (now powered by **Skrutable 2.0.7**).*'
)

# legend in sidebar
st.sidebar.header('Legend')
for lbl, col, fill in [
    ('Guru', 'black', True), ('Laghu', 'white', True),
    *[(f'Vipula {n}', c, True) for n,c in VIPULA_COL.items()],
    ('Vṛtti Anuprāsa', 'purple', False),
    ('Pathyā Anuṣṭubh', 'blue', False),
    ('Pāda-ādi Yamaka', 'green', False),
    ('Pāda-anta Yamaka', 'red', False)
]:
    style = f"background:{col};" if fill else f"border:2px solid {col};"
    st.sidebar.markdown(
        f\"<span style='display:inline-block;width:14px;"
        f"height:14px;{style}'></span> {lbl}<br>\",
        unsafe_allow_html=True
    )

txt = st.text_area('IAST input:', height=220)
if st.button('Show'):
    lines_iast = [p.strip() for p in re.split(r'[।॥|]+', txt) if p.strip()]
    if not lines_iast:
        st.error('No valid pāda found.')
    else:
        lines_slp = [split_syllables(normalize(p)) for p in lines_iast]
        draw(lines_slp)

st.markdown(
    '<div style="text-align:center; font-size:0.9em; '
    'margin-top:1em;">App by Svetlana Kreuzer</div>',
    unsafe_allow_html=True
)
