import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
import math
from typing import List, Optional, Tuple
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    t = unicodedata.normalize('NFC', text.strip())
    t = re.sub(r'[।॥\d]', '', t)
    return transliterate(t, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> List[str]:
    s = re.sub(r"\s+", "", text)
    vowels = set('aAiIuUfFxXeEoO')
    n = len(s)
    sylls: List[str] = []
    pos = 0
    while pos < n:
        j = pos
        while j < n and s[j] not in vowels:
            j += 1
        if j >= n: break
        k = j + 1
        if k < n and s[k] in ('M','H'): k += 1
        cstart = k
        while k < n and s[k] not in vowels: k += 1
        cluster = s[cstart:k]
        cut = k if len(cluster) <= 1 else cstart + 1
        sylls.append(s[pos:cut])
        pos = cut
    if pos < n:
        rem = s[pos:]
        if sylls: sylls[-1] += rem
        else: sylls = [rem]
    return sylls

# ===== Определение гуру/лакху =====
long_vowels = set(['A','I','U','F','X','e','E','o','O'])
def is_guru(s: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m: return False
    _, vowel, nasal, after = m.groups()
    return vowel in long_vowels or bool(nasal) or len(after) >= 2

# ===== Метрики: pathya anuṣṭubh, yamaka, anuprāsa =====
def classify_pathya(block: List[str]) -> bool:
    # объединяем 32 слога śloka
    if len(block) < 32: return False
    s = block[:32]
    # проверяем группы 3rd pāda & 4th pāda слоги 5-7
    p3, p4 = s[16:24], s[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5]) and is_guru(p4[4]) and is_guru(p4[5]))

def detect_padayadi_yamaka(block: List[str]) -> bool:
    # одинаковые первые слоги всех 4 pāда
    if len(block) < 32: return False
    pads = [block[i*8:(i+1)*8] for i in range(4)]
    heads = [p[0] for p in pads]
    return len(set(heads)) == 1

def detect_padaanta_yamaka(block: List[str]) -> bool:
    # одинаковые последние слоги всех 4 pāda
    if len(block) < 32: return False
    pads = [block[i*8:(i+1)*8] for i in range(4)]
    tails = [p[-1] for p in pads]
    return len(set(tails)) == 1

def detect_vrttyanuprasa(line: List[str]) -> bool:
    # повтор одинакового согласного начала у слогов 5-7 в строке
    if len(line) < 7: return False
    onsets = []
    for syl in line[4:7]:
        m = re.match(r'^([^aAiIuUfFxXeEoO]+)', syl)
        onsets.append(m.group(1) if m else '')
    return len(set(onsets)) == 1 and onsets[0] != ''

# ===== Визуализация: сетка с детекторами =====
def visualize_lines(lines: List[List[str]]) -> None:
    rows = len(lines)
    cols = max((len(r) for r in lines), default=0)
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    all_sylls = [s for row in lines for s in row]

    fig, ax = plt.subplots(figsize=(cols/8*6, rows/8*6), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')
    fs = 12

    # 1) Draw row-level markers first (Vipula, Anuprāsa)
    for r, row in enumerate(lines):
        y = rows - 1 - r
        # Vipula (по первым 4 слогам)
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0, y), min(4, len(row)), 1,
                                    facecolor=vipula_colors[vip], alpha=0.25, zorder=0))
        # Vṛtti Anuprāsa (повтор onset слогов 5‑7)
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((0, y), len(row), 1,
                                    facecolor='purple', alpha=0.15, zorder=0))

    # 2) Draw cells and text over backgrounds
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            face = 'black' if is_guru(syl) else 'white'
            tc = 'white' if is_guru(syl) else 'black'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='gray', zorder=1))
            ax.text(c + 0.5, y + 0.5, display[r][c], ha='center', va='center', color=tc, fontsize=fs, zorder=2)

    # 3) Overlay sloka-level markers on top
    for start in range(0, len(all_sylls), 32):
        block = all_sylls[start:start+32]
        if len(block) < 32:
            continue
        # determine starting row of this sloka block
        # count how many rows above this sloka start
        idx = start
        row0 = rows - 1 - (idx // cols)
        # block spans two rows: row0 and row0-1
        y_block = row0 - 1
        # width: 8 columns
        w = min(cols, 8)
        h = 2
        if classify_pathya(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True, facecolor='blue', alpha=0.3, zorder=3))
        if detect_padayadi_yamaka(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True, facecolor='green', alpha=0.3, zorder=3))
        if detect_padaanta_yamaka(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True, facecolor='red', alpha=0.3, zorder=3))

    # 3) Overlay line-level anuprasa
    for r, row in enumerate(lines):
        if detect_vrttyanuprasa(row):
            y = rows - 1 - r
            ax.add_patch(Rectangle((0, y), len(row), 1, fill=True, facecolor='purple', alpha=0.3, zorder=3))

    # 4) Legend
    legend = [
        Patch(facecolor='black', label='Guru'),
        Patch(facecolor='white', label='Laghu'),
        Patch(facecolor='blue', alpha=0.3, label='Pathya Anuṣṭubh'),
        Patch(facecolor='green', alpha=0.3, label='Pāda-ādi Yamaka'),
        Patch(facecolor='red', alpha=0.3, label='Pāda-anta Yamaka'),
        Patch(facecolor='purple', alpha=0.3, label='Vṛtti Anuprāsa')
    ]
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8, frameon=False)

    st.pyplot(fig)

# ===== UI =====
st.title('Sloka Meter Visualizer')
text=st.text_area('Введите IAST-текст, разделяя строки знаком danda (। или ॥):',height=200)
if st.button('Показать сетку'):
    if not text.strip(): st.warning('Введите текст до danda!')
    else:
        parts=[p.strip() for p in re.split(r'[।॥]+',text) if p.strip()]
        lines=[split_syllables_slp1(normalize(p)) for p in parts]
        visualize_lines(lines)
