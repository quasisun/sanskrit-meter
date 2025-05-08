import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
import math
from typing import List, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    """Нормализует текст и транслитерирует из IAST в SLP1"""
    t = unicodedata.normalize('NFC', text.strip())
    t = re.sub(r'[।॥\d]', '', t)
    return transliterate(t, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> List[str]:
    """
    Делит SLP1-строку на слоги по классическим фонетическим правилам:
    - Каждый слог содержит ровно один гласный.
    - Согласные до гласного (onset) остаются вместе.
    - Согласные после гласного (coda): если их ≥2, первая остаётся тут, остальные переходят в следующий слог.
    - Аннусвара/висарга (M, H) всегда в coda.
    """
    s = re.sub(r"\s+", "", text)
    vowels = set('aAiIuUfFxXeEoO')
    n = len(s)
    sylls: List[str] = []
    pos = 0
    while pos < n:
        # ищем nucleus
        j = pos
        while j < n and s[j] not in vowels:
            j += 1
        if j >= n:
            break
        # включаем nucleus и возможный M/H
        k = j + 1
        if k < n and s[k] in ('M', 'H'):
            k += 1
        # собираем кластер после гласного
        cstart = k
        while k < n and s[k] not in vowels:
            k += 1
        cluster = s[cstart:k]
        # делим кластер
        if len(cluster) <= 1:
            cut = k
        else:
            cut = cstart + 1
        sylls.append(s[pos:cut])
        pos = cut
    # остаток добавляем к последнему слогу
    if pos < n:
        rem = s[pos:]
        if sylls:
            sylls[-1] += rem
        else:
            sylls = [rem]
    return sylls

# ===== Определение гуру/лакху =====
long_vowels = set(['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O'])
def is_guru(s: str) -> bool:
    """Возвращает True, если слог тяжелый (guru), иначе False (laghu)"""
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    return (vowel in long_vowels) or bool(nasal) or len(after) >= 2

# ===== Определение випулы =====
vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}
def identify_vipula(sylls: List[str]) -> Optional[str]:
    """Определяет тип випулы по первой четверке слогов"""
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

# ===== Визуализация: динамическая сетка с випулами =====
def visualize_lines(lines: List[List[str]]) -> None:
    """Рисует сетку: строки подряд, слоги в квадратах, подсветка випулы"""
    # вычисляем размер
    rows = len(lines)
    cols = max((len(row) for row in lines), default=0)
    # готовим отображение IAST
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]

    fig_w = max(cols, 1) / 8 * 6
    fig_h = max(rows, 1) / 8 * 6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    fs = 12
    # базовая отрисовка guru/laghu
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            face = 'black' if is_guru(syl) else 'white'
            txt_color = 'white' if is_guru(syl) else 'black'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='black'))
            ax.text(c + 0.5, y + 0.5, display[r][c], ha='center', va='center', color=txt_color, fontsize=fs)
    # подсветка випул по строкам
    for r, row in enumerate(lines):
        vip = identify_vipula(row)
        if vip:
            y = rows - 1 - r
            for c in range(4):
                if c < len(row):
                    ax.add_patch(Rectangle((c, y), 1, 1, facecolor=vipula_colors[vip], alpha=0.4))
    # легенда
    legend = [Patch(facecolor='black', label='Guru'), Patch(facecolor='white', label='Laghu')]
    for name, col in vipula_colors.items():
        legend.append(Patch(facecolor=col, alpha=0.4, label=name))
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8)
    st.pyplot(fig)

# ===== UI =====
st.title("Sloka Meter Visualizer")
text = st.text_area("Введите IAST-текст, разделяя строки знаком danda (। или ॥):", height=200)
if st.button("Показать сетку"):
    if not text.strip():
        st.warning("Введите текст до danda!")
    else:
        parts = [p.strip() for p in re.split(r'[।॥]+', text) if p.strip()]
        lines = [split_syllables_slp1(normalize(p)) for p in parts]
        visualize_lines(lines)
