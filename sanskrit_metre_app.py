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
    # удаляем все пробельные символы
    t = re.sub("\s+", "", text)
    vowel_set = 'aAiIuUfFxXeEoO'
    pat = rf'([^ {vowel_set}]*[{vowel_set}][MH]?)(?=[^{vowel_set}]*[{vowel_set}][MH]?|$)'
    return re.findall(pat, t)

# ===== Определение гуру/лакху =====
short_vowels = ['a', 'i', 'u', 'f', 'x']
long_vowels  = ['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O']
def is_guru(s: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    return vowel in long_vowels or bool(nasal) or len(after) >= 2

# ===== Визуализация: строки → сетка =====
def visualize_lines(lines: list[list[str]]) -> None:
    # Перевод на IAST для отображения
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    rows = len(lines)
    cols = max(len(row) for row in lines) if rows>0 else 0

    # Размеры фигуры
    fig_w = max(cols, 1) / 8 * 6
    fig_h = max(rows,1) / 8 * 6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    fs = 12  # фиксированный размер шрифта
    # Рисуем клетки и текст
    for r, row in enumerate(lines):
        for c, syl in enumerate(row):
            y = rows - 1 - r
            face = 'black' if is_guru(syl) else 'white'
            txt_color = 'white' if is_guru(syl) else 'black'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='black'))
            ax.text(c + 0.5, y + 0.5, display[r][c], ha='center', va='center', color=txt_color, fontsize=fs)

    # Легенда
    legend = [Patch(facecolor='black', label='guru'), Patch(facecolor='white', label='laghu')]
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)

    # Отображаем
    st.pyplot(fig)

# ===== UI =====
st.title("Sloka Meter Visualizer")
text = st.text_area("Введите текст на IAST, разделяя pādas/строки знаком danda (। или ॥):", height=200)
if st.button("Показать сетку"):
    if not text.strip():
        st.warning("Введите текст до danda!")
    else:
        # Разбиваем на строки (pādas) по danda
        parts = [p.strip() for p in re.split(r'[।॥]', text) if p.strip()]
        # Для каждой создаём список слогов в SLP1
        lines = [split_syllables_slp1(normalize(p)) for p in parts]
        # Выводим одну общую сетку
        visualize_lines(lines)
