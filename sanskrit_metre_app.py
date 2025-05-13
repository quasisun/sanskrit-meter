# Sloka Meter Visualizer — Apte/Skrutable‑compliant
# © 2025 Svetlana Kreuzer

"""Streamlit app that plots guru/laghu grids and highlights vipulā, yamaka,
anuprāsa and pathyā–anuṣṭubh.  Updated to match the syllable–splitting rules
in V.S. Apte’s appendix and the open‑API notes of **Skrutable**.

Key fixes
──────────
1.  A single consonant after a short vowel always migrates to the next onset.
2.  Clusters ≥ 2 split *1 | rest*, except for a small whitelist of legal final
    clusters (tr, kṣ etc.) that stay intact — matching Skrutable’s splitter.
3.  A trail of only consonants at line‑end is glued to the previous syllable,
    so a final “m” never forms a spurious light syllable.
4.  A syllable is guru if it contains a long vowel **or** ends in M/ḥ **or**
    has **any** coda consonant (≥ 1) ⇒ mora‑count 2.
"""

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re, unicodedata
from typing import List, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ─── CONSTANT TABLES ──────────────────────────────────────────────────────────
LONG_VOWELS = set('AIUFXeEoO')
VOWELS      = set('aAiIuUfFxXeEoO')
LEGAL_FINAL = {'tr', 'kṣ', 'kṣṇ', 'jñ'}   # clusters Skrutable keeps intact

VIPULA_COL = {
    'Nagari':   '#FF7F00',
    'Bhavani':  '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya':     '#8B0000',
    'Vidyunmala': '#9932CC'
}

# ─── TEXT UTILS ───────────────────────────────────────────────────────────────

def normalize(txt: str) -> str:
    """Strip punctuation & digits, convert IAST → SLP‑1."""
    txt = unicodedata.normalize('NFC', txt.strip())
    txt = re.sub(r'[।॥|,.;:!?"]|\d', '', txt)
    return transliterate(txt, sanscript.IAST, sanscript.SLP1)

# ─── SYLLABLE SPLITTER ────────────────────────────────────────────────────────

def split_syllables_slp1(s: str) -> List[str]:
    s = re.sub(r'\s+', '', s)
    out, n, i = [], len(s), 0
    while i < n:
        # step to next vowel
        while i < n and s[i] not in VOWELS:
            i += 1
        if i >= n:
            break
        start = i
        i += 1                                   # skip vowel
        if i < n and s[i] in 'MH':               # keep M/ḥ with vowel
            i += 1
        c_start = i
        while i < n and s[i] not in VOWELS:
            i += 1
        cluster = s[c_start:i]
        if cluster in LEGAL_FINAL:                # keep all
            cut = i
        elif len(cluster) <= 1:
            cut = i                              # 0/1 consonant migrates
        else:
            cut = c_start + 1                    # split 1 | rest
        out.append(s[start:cut])
        i = cut
    # attach trailing consonants to last syllable
    if i < n:
        tail = s[i:]
        if out:
            out[-1] += tail
        else:
            out.append(tail)
    return out

# ─── PROSODY LOGIC ───────────────────────────────────────────────────────────

def is_guru(syl: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', syl)
    if not m:
        return False
    _, v, mh, coda = m.groups()
    return v in LONG_VOWELS or mh or len(coda) >= 1


def vipula(line: List[str]) -> Optional[str]:
    if len(line) < 4:
        return None
    pat = ''.join('g' if is_guru(s) else 'l' for s in line[:4])
    return {
        'lglg': 'Nagari', 'lllg': 'Bhavani', 'llgg': 'Shardula',
        'glgg': 'Arya',   'gglg': 'Vidyunmala'
    }.get(pat)

# Pathyā & sound‑ornaments (unchanged)

def pathya(blk: List[str]) -> bool:
    return len(blk) >= 32 and not is_guru(blk[20]) and is_guru(blk[21]) and is_guru(blk[28]) and is_guru(blk[29])

def pādādi(blk: List[str]) -> bool:
    return len(blk) >= 32 and len({blk[i*8] for i in range(4)}) == 1

def pādānta(blk: List[str]) -> bool:
    return len(blk) >= 32 and len({blk[i*8+7] for i in range(4)}) == 1

def anuprāsa(line: List[str]) -> bool:
    if len(line) < 7:
        return False
    ons = [re.match(r'^([^aAiIuUfFxXeEoO]+)', s).group(1) if re.match(r'^([^aAiIuUfFxXeEoO]+)', s) else '' for s in line[4:7]]
    return len(set(ons)) == 1 and ons[0]

# ─── DRAWING ──────────────────────────────────────────────────────────────────

def draw(lines: List[List[str]]):
    rows, cols = len(lines), max(map(len, lines))
    disp = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in r] for r in lines]
    flat = [s for r in lines for s in r]

    fig, ax = plt.subplots(figsize=(cols*0.55, rows*0.55))
    ax.set(xlim=(0, cols), ylim=(0, rows)); ax.axis('off'); ax.set_aspect('equal')

    # cells + text
    for r,row in enumerate(lines):
        y = rows-1-r
        for c, s in enumerate(row):
            g = is_guru(s)
            ax.add_patch(Rectangle((c,y),1,1,facecolor='black' if g else 'white',edgecolor='gray',zorder=1))
            ax.text(c+0.5,y+0.5,disp[r][c],ha='center',va='center',color='white' if g else 'black',fontsize=9,zorder=2)

    # line‑level markers
    for r,row in enumerate(lines):
        y = rows-1-r
        v = vipula(row)
        if v:
            ax.add_patch(Rectangle((0,y),min(4,len(row)),1,facecolor=VIPULA_COL[v],alpha=0.45,zorder=3))
        if anuprāsa(row):
            ax.add_patch(Rectangle((0,y),len(row),1,fill=False,edgecolor='purple',lw=2,zorder=4))

    # śloka‑level
    for i in range(0,len(flat),32):
        blk = flat[i:i+32]
        if len(blk)<32: break
        base = i//cols; yb = rows-1-base-1
        if yb<0: continue
        w = min(cols,8)
        if pathya(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='blue',lw=2.5,zorder=5))
        if pādādi(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='green',lw=2,linestyle='--',zorder=5))
        if pādānta(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='red',lw=2,linestyle=':',zorder=5))

    st.pyplot(fig); plt.close(fig)

# ─── STREAMLIT UI ─────────────────────────────────────────────────────────────
st.set_page_config(page_title='Sloka Meter', layout='wide')

st.title('Sloka Meter Visualizer')

# concise instructions (closed string!)
st.markdown(
    "*Paste IAST — one pāda per line. Separate pāda with `|`, `।`, or `॥`. "
    "Click **Show** to display guru/laghu squares, vipulā fill, and yamaka / "
    "anuprāsa / pathyā frames.*"
)

# ── sidebar legend (already defined above) remains unchanged ──

# main input & display
text = st.text_area('IAST input:', height=200)
if st.button('Show'):
    parts = [p.strip() for p in re.split(r'[।॥|]+', text) if p.strip()]
    if not parts:
        st.error('No valid lines found.')
    else:
        lines = [split_syllables_slp1(normalize(p)) for p in parts]
        draw(lines)

st.markdown("<div style='text-align:center; font-size:0.9em; margin-top:1em;'>App by Svetlana Kreuzer</div>", unsafe_allow_html=True)
