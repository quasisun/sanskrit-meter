import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
import math
from typing import List, Optional, Tuple
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import uuid

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    """Нормализует текст IAST в SLP1, удаляя пунктуацию и цифры."""
    t = unicodedata.normalize('NFC', text.strip())
    t = re.sub(r'[।॥\d]', '', t)
    return transliterate(t, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> List[str]:
    """Разделяет текст в SLP1 на слоги."""
    s = re.sub(r"\s+", "", text)
    vowels = set('aAiIuUfFxXeEoO')
    n = len(s)
    sylls: List[str] = []
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

# ===== Определение гуру/лагху =====
long_vowels = set(['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O'])
def is_guru(s: str) -> bool:
    """Определяет, является ли слог гуру (тяжелым)."""
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
    """Определяет тип випулы по первым 4 слогам строки."""
    if len(sylls) < 4:
        st.write(f"Недостаточно слогов для випулы: {sylls}")
        return None
    pattern = ''.join('g' if is_guru(s) else 'l' for s in sylls[:4])
    mapping = {
        'lglg': 'Nagari',
        'lllg': 'Bhavani',
        'llgg': 'Shardula',
        'glgg': 'Arya',
        'gglg': 'Vidyunmala'
    }
    vip = mapping.get(pattern)
    if vip:
        st.write(f"Обнаружена випула: {vip} (паттерн: {pattern})")
    return vip

# ===== Метрики: pathya anuṣṭubh, yamaka, anuprāsa =====
def classify_pathya(block: List[str]) -> bool:
    """Проверяет, является ли блок pathya anuṣṭubh."""
    if len(block) < 32:
        st.write(f"Блок слишком короткий для pathya: {len(block)} слогов")
        return False
    p3, p4 = block[16:24], block[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5]) and is_guru(p4[4]) and is_guru(p4[5]))

def detect_padayadi_yamaka(block: List[str]) -> bool:
    """Проверяет наличие pāda-ādi yamaka (одинаковые первые слоги pāda)."""
    if len(block) < 32:
        return False
    pads = [block[i*8:(i+1)*8] for i in range(4)]
    heads = [p[0] for p in pads if p]
    return len(set(heads)) == 1

def detect_padaanta_yamaka(block: List[str]) -> bool:
    """Проверяет наличие pāda-anta yamaka (одинаковые последние слоги pāda)."""
    if len(block) < 32:
        return False
    pads = [block[i*8:(i+1)*8] for i in range(4)]
    tails = [p[-1] for p in pads if p]
    return len(set(tails)) == 1

def detect_vrttyanuprasa(line: List[str]) -> bool:
    """Проверяет наличие vṛtti anuprāsa (повтор согласных в слогах 5–7)."""
    if len(line) < 7:
        return False
    onsets = []
    for syl in line[4:7]:
        m = re.match(r'^([^aAiIuUfFxXeEoO]+)', syl)
        onsets.append(m.group(1) if m else '')
    return len(set(onsets)) == 1 and onsets[0] != ''

# ===== Визуализация: сетка с детекторами =====
def visualize_lines(lines: List[List[str]]) -> None:
    """Создает визуализацию слогов с метками випул, ямака и анупрасы."""
    rows = len(lines)
    cols = max((len(r) for r in lines), default=0)
    if cols == 0 or rows == 0:
        st.error("Нет слогов для визуализации!")
        return
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    all_sylls = [s for row in lines for s in row]

    fig, ax = plt.subplots(figsize=(cols/8*6, rows/8*6), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')
    fs = 12

    # 1) Випулы и анупраса (фон строк)
    for r, row in enumerate(lines):
        y = rows - 1 - r
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0, y), min(4, len(row)), 1,
                                  facecolor=vipula_colors[vip], alpha=0.5, zorder=1))
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((4, y), 3, 1,
                                  facecolor='purple', alpha=0.3, zorder=1))

    # 2) Ячейки и текст
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            face = 'black' if is_guru(syl) else 'white'
            tc = 'white' if is_guru(syl) else 'black'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='gray', zorder=2))
            ax.text(c + 0.5, y + 0.5, display[r][c], ha='center', va='center',
                    color=tc, fontsize=fs, zorder=3)

    # 3) Pathya, yamaka (на уровне śoka)
    for start in range(0, len(all_sylls), 32):
        block = all_sylls[start:start+32]
        if len(block) < 32:
            continue
        idx = start
        row0 = rows - 1 - (idx // cols)
        y_block = row0 - 1
        w = min(cols, 8)
        h = 2
        if classify_pathya(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True,
                                  facecolor='blue', alpha=0.4, zorder=4))
        if detect_padayadi_yamaka(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True,
                                  facecolor='green', alpha=0.4, zorder=4))
        if detect_padaanta_yamaka(block):
            ax.add_patch(Rectangle((0, y_block), w, h, fill=True,
                                  facecolor='red', alpha=0.4, zorder=4))

    # 4) Легенда
    legend = [
        Patch(facecolor='black', label='Guru'),
        Patch(facecolor='white', label='Laghu'),
        Patch(facecolor='blue', alpha=0.4, label='Pathya Anuṣṭubh'),
        Patch(facecolor='green', alpha=0.4, label='Pāda-ādi Yamaka'),
        Patch(facecolor='red', alpha=0.4, label='Pāda-anta Yamaka'),
        Patch(facecolor='purple', alpha=0.3, label='Vṛtti Anuprāsa')
    ]
    for vip, color in vipula_colors.items():
        legend.append(Patch(facecolor=color, alpha=0.5, label=f'Vipula: {vip}'))
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.2),
              ncol=3, fontsize=8, frameon=True)

    st.pyplot(fig)
    plt.close(fig)

# ===== UI =====
st.title('Sloka Meter Visualizer')
text = st.text_area('Введите IAST-текст, разделяя строки знаком danda (। или ॥):',
                    height=200, placeholder="Пример: rāmo rājā rāghavaḥ śrīmān ।")
if st.button('Показать сетку'):
    if not text.strip():
        st.warning('Введите текст!')
    else:
        parts = [p.strip() for p in re.split(r'[।॥]+', text) if p.strip()]
        if not parts:
            st.error('Не удалось разделить текст на строки!')
        else:
            lines = [split_syllables_slp1(normalize(p)) for p in parts]
            st.write("Сегментированные строки:", lines)
            visualize_lines(lines)
