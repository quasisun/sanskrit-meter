import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
import math
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Конфигурация =====
short_vowels = ['a', 'i', 'u', 'f', 'x']
long_vowels = ['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O']

vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}
pathyā_color = '#4682B4'

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    text = unicodedata.normalize('NFC', text.strip())
    text = re.sub(r'[।॥\d]', '', text)
    return transliterate(text, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> list[str]:
    vowel_set = 'aAiIuUfFxXeEoO'
    pat = rf'([^ {vowel_set}]*[{vowel_set}][MH]?)(?=[^{vowel_set}]*[{vowel_set}][MH]?|$)'
    return re.findall(pat, text)

# ===== Определение гуру/лакху =====
def is_guru_syllable_slp1(syl: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', syl)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    return vowel in long_vowels or bool(nasal) or len(after) >= 2

# ===== Определение типа випулы =====
def identify_vipula(first_4: list[str]) -> str | None:
    pattern = ''.join('g' if is_guru_syllable_slp1(s) else 'l' for s in first_4)
    mapping = {
        'lglg': 'Nagari', 'lllg': 'Bhavani', 'llgg': 'Shardula',
        'glgg': 'Arya', 'gglg': 'Vidyunmala'
    }
    return mapping.get(pattern)

# ===== Классификация PATHYĀ =====
def classify_pathya(syllables: list[str]) -> bool:
    if len(syllables) < 32:
        return False
    p3, p4 = syllables[16:24], syllables[24:32]
    if len(p3) < 6 or len(p4) < 6:
        return False
    return (not is_guru_syllable_slp1(p3[4])
            and is_guru_syllable_slp1(p3[5])
            and is_guru_syllable_slp1(p4[4])
            and is_guru_syllable_slp1(p4[5]))

# ===== Визуализация сетки =====
def visualize_grid(syllables: list[str], columns: int) -> None:
    display = [transliterate(s, sanscript.SLP1, sanscript.IAST) for s in syllables]
    total = len(syllables)
    rows = math.ceil(total / columns)

    # Вычисляем реальные длины строк
    row_lengths = [(min((r+1)*columns, total) - r*columns) for r in range(rows)]
    max_len = max(row_lengths) if row_lengths else 0

    # Размер фигуры
    fig_width = max_len / 8 * 6
    fig_height = rows / 8 * 6
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    ax.set_xlim(0, max_len)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    # Шрифт
    fs = 12

    # Отрисовка клеток и слогов
    for idx, syl in enumerate(syllables):
        col = idx % columns
        row = rows - 1 - (idx // columns)
        # пропускать выравнивающие клеткит
        if col >= row_lengths[rows - 1 - row]:
            continue
        disp = display[idx]
        guru = is_guru_syllable_slp1(syl)
        face = 'black' if guru else 'white'
        txt_color = 'white' if guru else 'black'
        ax.add_patch(Rectangle((col, row), 1, 1, facecolor=face, edgecolor='black'))
        ax.text(col + 0.5, row + 0.5, disp, ha='center', va='center', color=txt_color, fontsize=fs)

        # Отметка випул для каждого ślока (32 слога)
    for start in range(0, total, 32):
        if start + 32 > total:
            break
        block = syllables[start:start + 32]
        v1 = identify_vipula(block[0:4])
        v2 = identify_vipula(block[16:20])
        for idx_v, vip in enumerate((v1, v2)):
            # rel_row == 0 для первого випула, 2 для второго
            rel_row = 0 if idx_v == 0 else 2
            # пропускаем, если строки меньше rel_row+1
            if rel_row >= rows:
                continue
            if vip in vipula_colors:
                # абсолютный индекс первого слога випулы
                abs_idx = start + rel_row * columns
                r = rows - 1 - (abs_idx // columns)
                # проверка валидности строки
                if r < 0 or r >= rows:
                    continue
                for j in range(4):
                    c = (start + j) % columns
                    if c < row_lengths[rows - 1 - r]:
                        ax.add_patch(Rectangle((c, r), 1, 1,
                                                facecolor=vipula_colors[vip], alpha=0.65))

    # Заголовок
    title = f"{max_len}×{rows} Grid"
    if classify_pathya(syllables):
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)

    # Легенда
    legend = [Patch(facecolor='black', label='Guru'), Patch(facecolor='white', label='Laghu'),
              Patch(facecolor=pathyā_color, alpha=0.5, label='Pathyā')]
    for name, colc in vipula_colors.items():
        legend.append(Patch(facecolor=colc, alpha=0.65, label=name))
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=8)
    st.pyplot(fig)

# ===== UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu + Vipula + Pathyā)")
text = st.text_area("Введите шлоки и pādas до danda (। или ॥) на IAST:", height=200)
if st.button("Показать"):
    if text:
        s = normalize(text)
        # Разбиваем по danda (। и ॥)
        raw_blocks = re.split(r'[।॥]+', s)
        verse_blocks = [b.strip() for b in raw_blocks if b.strip()]
        for i, block in enumerate(verse_blocks, 1):
            syl = split_syllables_slp1(block)
            num = len(syl)
            st.subheader(f"Стих {i} — {num} слогов, одна строка")
            visualize_grid(syl, num)
    else:
        st.warning("Введите текст IAST до danda")
