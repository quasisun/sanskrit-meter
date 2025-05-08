import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
import math
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    t = unicodedata.normalize('NFC', text.strip())
    t = re.sub(r'[।॥\d]', '', t)
    return transliterate(t, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> list[str]:
    # Убираем пробелы для непрерывного деления
    s = re.sub(r"\s+", "", text)
    vowels = set('aAiIuUfFxXeEoO')
    n = len(s)
    sylls: list[str] = []
    pos = 0
    while pos < n:
        # найти гласный
        j = pos
        while j < n and s[j] not in vowels:
            j += 1
        if j >= n:
            break
        # nucleus и возможный M/H
        k = j + 1
        if k < n and s[k] in ('M', 'H'):
            k += 1
        # кластер после гласного
        cstart = k
        while k < n and s[k] not in vowels:
            k += 1
        cluster = s[cstart:k]
        # split cluster: 1 cons to coda, rest to next onset
        cut = k if len(cluster) <= 1 else cstart + 1
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
short_vowels = ['a', 'i', 'u', 'f', 'x']
long_vowels  = ['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O']
def is_guru(s: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    return vowel in long_vowels or bool(nasal) or len(after) >= 2

# ===== Визуализация: динамическая сетка =====
def visualize_lines(lines: list[list[str]]) -> None:
    # ИAST для отображения
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    rows = len(lines)
    cols = max((len(row) for row in lines), default=0)

    # Размер фигуры пропорционально сетке
    fig_w = max(cols, 1) / 8 * 6
    fig_h = max(rows, 1) / 8 * 6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    fs = 12
    # Рисуем каждые строки подряд
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            face = 'black' if is_guru(syl) else 'white'
            txt_color = 'white' if is_guru(syl) else 'black'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='black'))
            ax.text(c + 0.5, y + 0.5, display[r][c], ha='center', va='center', color=txt_color, fontsize=fs)

    # Легенда
    legend = [Patch(facecolor='black', label='guru'), Patch(facecolor='white', label='laghu')]
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8)
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
