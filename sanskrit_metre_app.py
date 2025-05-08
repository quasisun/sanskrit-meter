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

# ===== Випула =====
vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}

def identify_vipula(sylls: List[str]) -> Optional[str]:
    """Возвращает тип випулы по первым 4 слогам строки."""
    if len(sylls) < 4:
        return None
    pattern = ''.join('g' if is_guru(s) else 'l' for s in sylls[:4])
    mapping = {
        'lglg': 'Nagari',
        'lllg': 'Bhavani',
        'llgg': 'Shardula',
        'glgg': 'Arya',
        'gglg': 'Vidyunmala'
    }
    return mapping.get(pattern)

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
    """Рисует сетку слогов + визуальные маркеры прямо НА клетках."""
    rows = len(lines)
    cols = max((len(r) for r in lines), default=0)
    if rows == 0 or cols == 0:
        st.error("Нет слогов для визуализации!")
        return

    # IAST для текста
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    all_sylls = [s for row in lines for s in row]

    fig, ax = plt.subplots(figsize=(cols / 8 * 6, rows / 8 * 6), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    fs = 12

    # 1) Сами клетки guru/laghu + текст (zorder=1/2)
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            guru = is_guru(syl)
            ax.add_patch(Rectangle((c, y), 1, 1,
                                    facecolor='black' if guru else 'white',
                                    edgecolor='gray', zorder=1))
            ax.text(c + 0.5, y + 0.5, display[r][c],
                    ha='center', va='center', color='white' if guru else 'black',
                    fontsize=fs, zorder=2)

    # 2) Row‑level markers (Vipula & vṛtti‑anuprāsa) OVER cells (zorder=3)
    for r, row in enumerate(lines):
        y = rows - 1 - r
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0, y), min(4, len(row)), 1,
                                    facecolor=vipula_colors[vip], alpha=0.45, zorder=3))
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((0, y), len(row), 1,
                                    facecolor='purple', alpha=0.25, zorder=3))

    # 3) Śloka‑level markers (Pathya & Yamaka) outline (zorder=4)
    for start in range(0, len(all_sylls), 32):
        block = all_sylls[start:start + 32]
        if len(block) < 32:
            continue
        # первая клетка блока
        idx_row = start // cols
        row_top = rows - 1 - idx_row
        row_bottom = max(row_top - 1, 0)
        y0 = row_bottom
        height = 2 if row_top != row_bottom else 1
        w = min(cols, 8)
        # Pathya (синий контур)
        if classify_pathya(block):
            ax.add_patch(Rectangle((0, y0), w, height, fill=False,
                                    edgecolor='blue', linewidth=2.5, zorder=4))
        # pādādi Yamaka (зелёный пунктир)
        if detect_padayadi_yamaka(block):
            ax.add_patch(Rectangle((0, y0), w, height, fill=False,
                                    edgecolor='green', linewidth=2, linestyle='--', zorder=4))
        # pādānta Yamaka (красный штрих‑точка)
        if detect_padaanta_yamaka(block):
            ax.add_patch(Rectangle((0, y0), w, height, fill=False,
                                    edgecolor='red', linewidth=2, linestyle=':', zorder=4))

    # 4) Легенда
    legend = [Patch(facecolor='black', label='Guru'),
              Patch(facecolor='white', label='Laghu')]
    # Vipula colors
    for name, col in vipula_colors.items():
        legend.append(Patch(facecolor=col, alpha=0.45, label=f'Vipula: {name}'))
    legend.extend([
        Patch(facecolor='purple', alpha=0.25, label='Vṛtti Anuprāsa'),
        Patch(edgecolor='blue', fill=False, linewidth=2.5, label='Pathya Anuṣṭubh'),
        Patch(edgecolor='green', fill=False, linestyle='--', linewidth=2, label='Pāda‑ādi Yamaka'),
        Patch(edgecolor='red', fill=False, linestyle=':', linewidth=2, label='Pāda‑anta Yamaka')
    ])
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15),
              ncol=3, fontsize=8, frameon=False)

    st.pyplot(fig)
    plt.close(fig)

# ===== UI =====
st.title('Sloka Meter Visualizer')
text=st.text_area('Введите IAST-текст, разделяя строки знаком danda (। или ॥):',height=200)
if st.button('Показать сетку'):
    if not text.strip(): st.warning('Введите текст до danda!')
    else:
        parts=[p.strip() for p in re.split(r'[।॥]+',text) if p.strip()]
        lines=[split_syllables_slp1(normalize(p)) for p in parts]
        visualize_lines(lines)
