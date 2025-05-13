# Sloka Meter Visualizer — updated Mālinī‑aware version
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re, unicodedata
from typing import List, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== CONFIG =====
long_vowels = set('AIUFXeEoO')

vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}

# ===== HELPERS =====

def normalize(text: str) -> str:
    text = unicodedata.normalize('NFC', text.strip())
    text = re.sub(r'[।॥|,.;:!?\d]', '', text)  # strip punctuation & digits
    return transliterate(text, sanscript.IAST, sanscript.SLP1)


def split_syllables_slp1(txt: str) -> List[str]:
    """IAST→SLP1 string → list of syllables following classical rules.
    • single consonant after a short vowel joins *next* syllable
    • ≥2 consonants: first stays in coda, rest shift to onset
    • anusvāra/visarga (M/H) stay with nucleus"""
    s = re.sub(r"\s+", "", txt)
    vowels = set('aAiIuUfFxXeEoO')
    out, n, i = [], len(s), 0
    while i < n:
        j = i
        while j < n and s[j] not in vowels:
            j += 1
        if j >= n:
            break
        k = j + 1
        if k < n and s[k] in 'MH':
            k += 1
        c = k
        while c < n and s[c] not in vowels:
            c += 1
        cluster_len = c - k
        if cluster_len == 0 or cluster_len == 1:
            cut = k  # open syllable or single consonant migrates
        else:
            cut = k + 1  # keep first, shift rest
        out.append(s[i:cut])
        i = cut
    if i < n:
        out.append(s[i:])
    return out


def is_guru(syl: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', syl)
    if not m:
        return False
    _, v, nas, coda = m.groups()
    return v in long_vowels or nas or len(coda) >= 1  # ≥1 coda consonant = heavy


def identify_vipula(syls: List[str]) -> Optional[str]:
    if len(syls) < 4:
        return None
    pat = ''.join('g' if is_guru(s) else 'l' for s in syls[:4])
    return {
        'lglg': 'Nagari', 'lllg': 'Bhavani', 'llgg': 'Shardula',
        'glgg': 'Arya', 'gglg': 'Vidyunmala'
    }.get(pat)

# simple detectors kept unchanged (pathyā, yamaka, anuprāsa)

def classify_pathya(block: List[str]) -> bool:
    return (len(block) >= 32 and
            not is_guru(block[20]) and is_guru(block[21]) and
            is_guru(block[28]) and is_guru(block[29]))

def detect_padayadi_yamaka(b: List[str]) -> bool:
    return len(b) >= 32 and len({b[i*8] for i in range(4)}) == 1

def detect_padaanta_yamaka(b: List[str]) -> bool:
    return len(b) >= 32 and len({b[i*8+7] for i in range(4)}) == 1

def detect_vrttyanuprasa(line: List[str]) -> bool:
    if len(line) < 7:
        return False
    onsets = []
    for s in line[4:7]:
        m = re.match(r'^([^aAiIuUfFxXeEoO]+)', s)
        onsets.append(m.group(1) if m else '')
    return len(set(onsets)) == 1 and onsets[0]

# ===== VIS =====

def visualize_lines(lines: List[List[str]]):
    rows = len(lines)
    cols = max(map(len, lines)) if rows else 0
    if not rows or not cols:
        st.error('No data')
        return

    disp = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in r] for r in lines]
    flat = [s for r in lines for s in r]

    fig, ax = plt.subplots(figsize=(cols * 0.55, rows * 0.55))
    ax.set(xlim=(0, cols), ylim=(0, rows)); ax.axis('off'); ax.set_aspect('equal')

    for r, row in enumerate(lines):
        y = rows - 1 - r
        for c, syl in enumerate(row):
            g = is_guru(syl)
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor='black' if g else 'white', edgecolor='gray', zorder=1))
            ax.text(c + 0.5, y + 0.5, disp[r][c], ha='center', va='center', color='white' if g else 'black', fontsize=9, zorder=2)

    for r, row in enumerate(lines):
        y = rows - 1 - r
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0, y), min(4, len(row)), 1, facecolor=vipula_colors[vip], alpha=0.45, zorder=3))
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((0, y), len(row), 1, fill=False, edgecolor='purple', lw=2, zorder=4))

    for i in range(0, len(flat), 32):
        blk = flat[i:i+32]
        if len(blk) < 32:
            break
        base = i // cols
        yb = rows - 1 - base - 1
        if yb < 0:
            continue
        w = min(cols, 8)
        if classify_pathya(blk):
            ax.add_patch(Rectangle((0, yb), w, 2, fill=False, edgecolor='blue', lw=2.5, zorder=5))
        if detect_padayadi_yamaka(blk):
            ax.add_patch(Rectangle((0, yb), w, 2, fill=False, edgecolor='green', lw=2, linestyle='--', zorder=5))
        if detect_padaanta_yamaka(blk):
            ax.add_patch(Rectangle((0, yb), w, 2, fill=False, edgecolor='red', lw=2, linestyle=':', zorder=5))

    st.pyplot(fig)
    plt.close(fig)

# ===== UI =====
st.set_page_config(page_title='Sloka Meter', layout='wide')

st.title('Sloka Meter Visualizer')

st.markdown("**Quick instructions:** Paste IAST, one pāda per line separated by `|`, `।`, or `॥`. Click **Show**. Guru squares are black, laghu white; vipulā are filled; yamaka, anuprāsa, pathyā appear as borders.")

# Sidebar legend (scrolls with the page)
st.sidebar.header('Legend')
legend = [('Guru', 'black', True), ('Laghu', 'white', True)]
for n, c in vipula_colors.items():
    legend.append((f'Vipula {n}', c, True))
legend += [
    ('Vṛtti Anuprāsa', 'purple', False),
    ('Pathya', 'blue', False),
    ('Pāda‑ādi Yamaka', 'green', False),
    ('Pāda‑anta Yamaka', 'red', False)
]
for label, col, fill in legend:
    style = f"background:{col};" if fill else f"border:2px solid {col};"
    st.sidebar.markdown(f"<span style='display:inline-block;width:14px;height:14px;{style}'></span> {label}<br>", unsafe_allow_html=True)

text = st.text_area('IAST input:', height=200)
if st.button('Show'):
    parts = [p.strip() for p in re.split(r'[।॥|]+', text) if p.strip()]
    if not parts:
        st.error('No valid lines found.')
    else:
        lines = [split_syllables_slp1(normalize(p)) for p in parts]
        visualize_lines(lines)

st.markdown("<div style='text-align:center; font-size:0.9em; margin-top:1em;'>App by Svetlana Kreuzer</div>", unsafe_allow_html=True)
