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
    # удаляем все пробельные символы, чтобы слоги не терялись на границах слов
    t = re.sub(r"\s+", "", text)
    vowel_set = 'aAiIuUfFxXeEoO'
    # базовый паттерн: любое число согласных + гласный + опц. M/H
    pat = rf'([^ {vowel_set}]*[{vowel_set}][MH]?)'
    sylls = re.findall(pat, t)
    # прикрепляем к последнему слогу все оставшиеся согласные в конце
    consumed = ''.join(sylls)
    rem = t[len(consumed):]
    if rem:
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

# ===== Визуализация: строки → сетка =====
def visualize_lines(lines: list[list[str]]) -> None:
    # перевод в IAST для показа
    display = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in row] for row in lines]
    # оригинальное число строк и столбцов
    orig_rows = len(lines)
    cols = max((len(row) for row in lines), default=0)

    # фиксированная высота в 16 строк для квадратных клеток
    grid_rows = 16
    # при необходимости добавляем пустые строки сверху
    pad_rows = max(0, grid_rows - orig_rows)
    padded_lines = [[] for _ in range(pad_rows)] + lines
    padded_display = [['' for _ in range(cols)] for __ in range(pad_rows)] + display

    # размеры фигуры пропорциональны cols x grid_rows
    fig_w = max(cols, 1) / 8 * 6
    fig_h = grid_rows / 8 * 6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, grid_rows)
    ax.axis('off')
    ax.set_aspect('equal')

    fs = 12
    # отрисовка клеток и текста
    for r, row in enumerate(padded_lines):
        for c in range(cols):
            syl = row[c] if c < len(row) else ''
            y = grid_rows - 1 - r
            if syl:
                face = 'black' if is_guru(syl) else 'white'
                txt_color = 'white' if is_guru(syl) else 'black'
            else:
                face = 'white'
                txt_color = 'none'
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=face, edgecolor='black'))
            if syl:
                ax.text(c + 0.5, y + 0.5, padded_display[r][c], ha='center', va='center', color=txt_color, fontsize=fs)

    # легенда
    legend = [Patch(facecolor='black', label='guru'), Patch(facecolor='white', label='laghu')]
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
    st.pyplot(fig)(fig)

# ===== UI =====
st.title("Sloka Meter Visualizer")
text = st.text_area("Введите текст на IAST, разделяя pādas/строки знаком danda (। или ॥):", height=200)
if st.button("Показать сетку"):
    if not text.strip():
        st.warning("Введите текст до danda!")
    else:
        # разбиваем текст по danda на pādas
        parts = [p.strip() for p in re.split(r'[।॥]+', text) if p.strip()]
        # превращаем каждую pāda в список слогов
        lines = [split_syllables_slp1(normalize(p)) for p in parts]
        # группируем pādas по два в ślokas
        slokas = [lines[i:i+2] for i in range(0, len(lines), 2)]
        # визуализируем каждый śloka как блок из 2 строк
        for idx, block in enumerate(slokas, 1):
            st.subheader(f"Śloka {idx}")
            visualize_lines(block)
