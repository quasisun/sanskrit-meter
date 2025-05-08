import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
from typing import List, Optional
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
    sylls = []
    pos = 0
    while pos < n:
        j = pos
        while j < n and s[j] not in vowels:
            j += 1
        if j >= n:
            break
        k = j + 1
        if k < n and s[k] in ('M', 'H'):
            k += 1
        cstart = k
        while k < n and s[k] not in vowels:
            k += 1
        cluster = s[cstart:k]
        cut = k if len(cluster) <= 1 else cstart + 1
        sylls.append(s[pos:cut])
        pos = cut
    if pos < n:
        rem = s[pos:]
        if sylls:
            sylls[-1] += rem
        else:
            sylls = [rem]
    return sylls

# ===== Определение гуру/лакху =====
long_vowels = set('AIUFXeEoO')


def is_guru(s: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m:
        return False
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

# ===== Метрики =====

def classify_pathya(block: List[str]) -> bool:
    if len(block) < 32:
        return False
    p3, p4 = block[16:24], block[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5]) and is_guru(p4[4]) and is_guru(p4[5]))


def detect_padayadi_yamaka(block: List[str]) -> bool:
    if len(block) < 32:
        return False
    pads = [block[i * 8:(i + 1) * 8] for i in range(4)]
    heads = [p[0] for p in pads]
    return len(set(heads)) == 1


def detect_padaanta_yamaka(block: List[str]) -> bool:
    if len(block) < 32:
        return False
    pads = [block[i * 8:(i + 1) * 8] for i in range(4)]
    tails = [p[-1] for p in pads]
    return len(set(tails)) == 1


def detect_vrttyanuprasa(line: List[str]) -> bool:
    if len(line) < 7:
        return False
    onsets = []
    for syl in line[4:7]:
        m = re.match(r'^([^aAiIuUfFxXeEoO]+)', syl)
        onsets.append(m.group(1) if m else '')
    return len(set(onsets)) == 1 and onsets[0]

# ===== Визуализация =====

def visualize_lines(lines: List[List[str]]) -> None:
    rows = len(lines)
    cols = max((len(r) for r in lines), default=0)
    if not rows or not cols:
        st.error('Нет данных для визуализации')
        return

    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    all_sylls = [s for row in lines for s in row]

    fig, ax = plt.subplots(figsize=(cols / 8 * 6, rows / 8 * 6))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    # 1. базовые клетки + текст
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            guru = is_guru(syl)
            ax.add_patch(Rectangle((c, y), 1, 1,
                                    facecolor='black' if guru else 'white',
                                    edgecolor='gray', zorder=1))
            ax.text(c + 0.5, y + 0.5, display[r][c],
                    color='white' if guru else 'black', ha='center', va='center', zorder=2, fontsize=10)

    # 2. row‑level: vipula border, anuprāsa border
    for r, row in enumerate(lines):
        y = rows - 1 - r
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0, y), min(4, len(row)), 1,
                                    fill=False, edgecolor=vipula_colors[vip],
                                    linewidth=2.5, zorder=3))
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((0, y), len(row), 1,
                                    fill=False, edgecolor='purple', linewidth=2, zorder=3))

    # 3. śloka‑level borders
    for start in range(0, len(all_sylls), 32):
        block = all_sylls[start:start + 32]
        if len(block) < 32:
            continue
        base_row = start // cols
        # y range of this śloka = rows-1-base_row .. rows-1-base_row-1
        y_bottom = rows - 1 - base_row - 1
        if y_bottom < 0:
            continue
        w = min(cols, 8)
        if classify_pathya(block):
            ax.add_patch(Rectangle((0, y_bottom), w, 2, fill=False, edgecolor='blue', linewidth=2.5, zorder=4))
        if detect_padayadi_yamaka(block):
            ax.add_patch(Rectangle((0, y_bottom), w, 2, fill=False, edgecolor='green', linestyle='--', linewidth=2, zorder=4))
        if detect_padaanta_yamaka(block):
            ax.add_patch(Rectangle((0, y_bottom), w, 2, fill=False, edgecolor='red', linestyle=':', linewidth=2, zorder=4))

        # 4. легенда сбоку
    legend_patches = [
        Patch(facecolor='black', label='Guru'),
        Patch(facecolor='white', label='Laghu'),
    ]
    # Vipula
    for name, col in vipula_colors.items():
        legend_patches.append(Patch(edgecolor=col, facecolor='none', linewidth=2.5, label=f'Vipula {name}'))
    # Арупраса и ямаки
    legend_patches.extend([
        Patch(edgecolor='purple', facecolor='none', linewidth=2, label='Vṛtti Anuprāsa'),
        Patch(edgecolor='blue', facecolor='none', linewidth=2.5, label='Pathya Anuṣṭubh'),
        Patch(edgecolor='green', facecolor='none', linestyle='--', linewidth=2, label='Pāda-ādi Yamaka'),
        Patch(edgecolor='red', facecolor='none', linestyle=':', linewidth=2, label='Pāda-anta Yamaka')
    ])

    # Размещаем легенду справа от сетки
    ax.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10)

    st.pyplot(fig)
    plt.close(fig)

# ===== UI =====

st.title('Sloka Meter Visualizer')
text = st.text_area('Введите IAST-текст, разделяя строки знаком danda (। или ॥):', height=200)

if st.button('Показать сетку'):
    if not text.strip():
        st.warning('Введите текст!')
    else:
        parts = [p.strip() for p in re.split(r'[।॥]+', text) if p.strip()]
        if not parts:
            st.error('Не удалось разделить текст на строки!')
        else:
            lines = [split_syllables_slp1(normalize(p)) for p in parts]
            visualize_lines(lines)
