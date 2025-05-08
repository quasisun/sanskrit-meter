import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch, Circle
import re
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Конфигурация =====
short_vowels = ['a', 'i', 'u', 'f', 'x']
long_vowels = ['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O']

# Цвета для пяти классических випул
vipula_colors = {
    'Nagari': '#FF7F00',    # ярко-оранжевый
    'Bhavani': '#1E3F66',   # насыщенный тёмно-синий
    'Shardula': '#2E8B57',  # морской зелёный
    'Arya': '#8B0000',      # тёмно-красный
    'Vidyunmala': '#9932CC' # тёмный фиолетовый
}

# Pathyā color
pathyā_color = '#4682B4'  # steel blue

# Alaṅkāra colors
anuprasa_color = '#00CED1'  # dark turquoise border
yamaka_color = '#DA70D6'    # orchid circle

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    return transliterate(text.strip(), sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги SLP1 =====
def split_syllables_slp1(text: str) -> list[str]:
    pattern = r"""([^aAiIuUfFxXeEoOMH]*[aAiIuUfFxXeEoO][MH]?[^aAiIuUfFxXeEoOMH]?)"""
    return [s for s in re.findall(pattern, text) if s]

# ===== Определение гуру/лакху =====
def is_guru_syllable_slp1(syl: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])(M|H)?(.*)$', syl)
    if not m:
        return False
    vowel, nasal, after = m.group(2), m.group(3), m.group(4)
    if vowel in long_vowels or nasal or len(after) >= 2:
        return True
    return False

# ===== Определение вида Pathyā =====
def classify_pathya(syllables: list[str]) -> bool:
    if len(syllables) < 32:
        return False
    p3 = syllables[16:24]
    p4 = syllables[24:32]
    return (not is_guru_syllable_slp1(p3[4])
            and is_guru_syllable_slp1(p3[5])
            and is_guru_syllable_slp1(p4[4])
            and is_guru_syllable_slp1(p4[5]))

# ===== Определение типа випулы =====
def identify_vipula(first_4: list[str]) -> str | None:
    pattern = ''.join('g' if is_guru_syllable_slp1(s) else 'l' for s in first_4)
    mapping = {
        'lglg': 'Nagari', 'lllg': 'Bhavani', 'llgg': 'Shardula',
        'glgg': 'Arya',  'gglg': 'Vidyunmala'
    }
    return mapping.get(pattern)

# ===== Визуализация сетки =====
def visualize_grid(syllables: list[str], line_length: int) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, line_length)
    ax.set_ylim(0, line_length)
    ax.axis('off')

    # Разбивка по строкам
    lines = [syllables[i:i+line_length] for i in range(0, len(syllables), line_length)]
    while len(lines) < line_length:
        lines.append([])

    # 1) рисуем базу Guru/Laghu
    for i, row in enumerate(lines):
        for j in range(line_length):
            y = line_length - 1 - i
            if j < len(row):
                color = 'black' if is_guru_syllable_slp1(row[j]) else 'white'
            else:
                color = 'white'
            ax.add_patch(Rectangle((j, y), 1, 1, facecolor=color, edgecolor='black'))

    # 2) рисуем випулы по всем шлокам
    for start in range(0, len(syllables), 32):
        if start + 32 > len(syllables):
            break
        block = syllables[start:start+32]
        v1 = identify_vipula(block[0:4])
        v2 = identify_vipula(block[16:20])
        base_row = line_length - 1 - (start // line_length)
        rows = [base_row, base_row-2]
        for idx, vip in enumerate((v1, v2)):
            if vip and vip in vipula_colors:
                for j in range(4):
                    ax.add_patch(Rectangle((j, rows[idx]), 1, 1,
                                             facecolor=vipula_colors[vip], alpha=0.65))

    # 3) рисуем Anuprāsa и Yamaka внутри каждой pāda
    for i, row in enumerate(lines):
        y = line_length - 1 - i
        # извлекаем начальные согласные для Anuprāsa
        initials = []
        for syl in row:
            m = re.match(r'^([^AEIOUaeiouMHF]+)', syl)
            initials.append(m.group(1) if m else '')
        # находим повторы
        repeats = {s for s in initials if s and initials.count(s) > 1}
        # находим Yamaka (повторы полных слогов)
        yamakas = {s for s in row if row.count(s) > 1}
        for j, syl in enumerate(row):
            x = j
            # Anuprāsa: рамка
            if initials[j] in repeats:
                ax.add_patch(Rectangle((x, y), 1, 1, fill=False,
                                        edgecolor=anuprasa_color, linewidth=2))
            # Yamaka: точка
            if syl in yamakas:
                ax.add_patch(Circle((x+0.5, y+0.5), 0.15, color=yamaka_color))

    # 4) заголовок
    title = f"{line_length}×{line_length} Grid"
    if classify_pathya(syllables):
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)

    # 5) легенда
    legend = [
        Patch(facecolor='black', edgecolor='black', label='Guru'),
        Patch(facecolor='white', edgecolor='black', label='Laghu'),
        Patch(facecolor=pathyā_color, label='Pathyā-anuṣṭubh', alpha=0.5)
    ]
    for name, col in vipula_colors.items():
        legend.append(Patch(facecolor=col, label=f'Vipula: {name}', alpha=0.65))
    legend.append(Patch(facecolor='none', edgecolor=anuprasa_color, label='Anuprāsa', linewidth=2))
    legend.append(Patch(facecolor=yamaka_color, label='Yamaka', alpha=1.0))

    ax.legend(handles=legend, loc='lower center',
              bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8)
    st.pyplot(fig)

# ===== Streamlit UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu + Vipula + Pathyā + Alaṅkāra)")

text_input = st.text_area("Введите шлоки в IAST:", height=200)

grid_size = st.selectbox("Размер сетки (по слогам в строке):", options=[8, 16, 32], index=0)

if st.button("Визуализировать"):
    if text_input.strip():
        slp1_text = normalize(text_input)
        syllables = split_syllables_slp1(slp1_text)
        block_size = grid_size * grid_size
        blocks = [syllables[i:i + block_size] for i in range(0, len(syllables), block_size)]
        for i, block in enumerate(blocks):
            st.subheader(f"Блок {i+1}")
            visualize_grid(block, grid_size)
    else:
        st.warning("Пожалуйста, введите текст.")
