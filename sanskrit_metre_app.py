import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import math

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

# ===== Визуализация сетки (с IAST-слогами) =====
def visualize_grid(syllables: list[str], columns: int) -> None:
    # Получаем IAST для отображения
    display = [transliterate(s, sanscript.SLP1, sanscript.IAST) for s in syllables]
    total = len(syllables)
    rows = math.ceil(total / columns)

    fig, ax = plt.subplots(figsize=(columns, rows), constrained_layout=True)
    ax.set_xlim(0, columns)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_aspect('equal')

    # Определяем базовый размер шрифта
    base_fs = 12
    fs = base_fs * min(1, 8 / columns)

    # Рисуем клетки и слоги
    for idx, syl in enumerate(syllables):
        col = idx % columns
        row = rows - 1 - (idx // columns)
        disp = display[idx]
        guru = is_guru_syllable_slp1(syl)
        face = 'black' if guru else 'white'
        txt_color = 'white' if guru else 'black'
        ax.add_patch(Rectangle((col, row), 1, 1, facecolor=face, edgecolor='black'))
        ax.text(col + 0.5, row + 0.5, disp, ha='center', va='center', color=txt_color, fontsize=fs)

    # Высветка випулы для каждой śloka по 32 слога
    for start in range(0, total, 32):
        if start + 32 > total:
            break
        block = syllables[start:start + 32]
        v1 = identify_vipula(block[0:4])
        v2 = identify_vipula(block[16:20])
        for idx, vip in enumerate((v1, v2)):
            if vip in vipula_colors:
                # позиция первого слога śloka
                start_idx = start
                # для v1: первый ряд śloka; для v2: третий ряд ślока
                rel_row = 0 if idx == 0 else 2
                row = rows - 1 - ((start_idx // columns) + rel_row)
                for j in range(4):
                    col = (start_idx + j) % columns
                    ax.add_patch(Rectangle((col, row), 1, 1, facecolor=vipula_colors[vip], alpha=0.65))

    # Pathyā заголовок
    title = f"{columns}×{rows} Grid"
    if classify_pathya(syllables):
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)

    # Легенда
    legend = [Patch(facecolor='black', label='Guru'), Patch(facecolor='white', label='Laghu'),
              Patch(facecolor=pathyā_color, alpha=0.5, label='Pathyā')]
    for name, col in vipula_colors.items():
        legend.append(Patch(facecolor=col, alpha=0.65, label=name))
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=8)
    st.pyplot(fig)

# ===== UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu + Vipula + Pathyā)")
text = st.text_area("Введите шлоки на IAST:", height=200)
columns = st.selectbox("Число слогов в строке:", [8, 16, 32], index=0)
if st.button("Показать"):
    if text:
        s = normalize(text)
        syl = split_syllables_slp1(s)
        visualize_grid(syl, columns)
    else:
        st.warning("Введите текст IAST")
