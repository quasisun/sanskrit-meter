import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Обработка текста =====
short_vowels = ['a', 'i', 'u', 'f', 'x']  # SLP1 short vowels
long_vowels = ['A', 'I', 'U', 'F', 'X', 'e', 'E', 'o', 'O']

vipula_colors = {
    'Nagari': '#FF7F00',      # ярко-оранжевый
    'Bhavani': '#1E3F66',     # насыщенный тёмно-синий
    'Shardula': '#2E8B57',    # морской зелёный
    'Arya': '#8B0000',        # тёмно-красный
    'Vidyunmala': '#9932CC',  # тёмный фиолетовый
    'Other': '#555555'        # тёмно-серый, чтобы выделялся
}

anushtubh_colors = {
    'Pathyā-anuṣṭubh': '#4682B4',     # steel blue
    'Vipulā-anuṣṭubh': '#DAA520',     # goldenrod
    'Unknown': '#A9A9A9'              # dim gray
}

def normalize(text):
    text = text.strip()
    return transliterate(text, sanscript.IAST, sanscript.SLP1)

def split_syllables_slp1(text):
    pattern = r"""
        ([^aAiIuUfFxXeEoOMH]*
         [aAiIuUfFxXeEoO]
         [MH]?
         [^aAiIuUfFxXeEoOMH]?)
    """
    syllables = re.findall(pattern, text, re.VERBOSE)
    return [s for s in syllables if s]

def is_guru_syllable_slp1(syl):
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)([^aAiIuUfFxXeEoOMH]*)$', syl)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    if vowel in long_vowels:
        return True
    if nasal:
        return True
    if len(after) >= 2:
        return True
    return False

def identify_vipula(first_4):
    pattern = ''.join(['g' if is_guru_syllable_slp1(s) else 'l' for s in first_4])
    mapping = {
        'lglg': 'Nagari',
        'lllg': 'Bhavani',
        'llgg': 'Shardula',
        'glgg': 'Arya',
        'gglg': 'Vidyunmala'
    }
    return mapping.get(pattern, 'Other')

def classify_anushtubh(syllables):
    if len(syllables) < 32:
        return 'Unknown'
    p3 = syllables[16:24]
    p4 = syllables[24:32]
    if len(p3) < 6 or len(p4) < 6:
        return 'Unknown'
    l3_5 = is_guru_syllable_slp1(p3[4])
    l3_6 = is_guru_syllable_slp1(p3[5])
    l4_5 = is_guru_syllable_slp1(p4[4])
    l4_6 = is_guru_syllable_slp1(p4[5])
    if (not l3_5) and l3_6 and l4_5 and l4_6:
        return 'Pathyā-anuṣṭubh'
    else:
        return 'Vipulā-anuṣṭubh'

# ===== Визуализация =====
def visualize_grid(syllables, line_length):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, line_length)
    ax.set_ylim(0, line_length)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')

    lines = [syllables[i:i + line_length] for i in range(0, len(syllables), line_length)]
    while len(lines) < line_length:
        lines.append([])

    vipula_labels = ['Other', 'Other']
    metre_type = classify_anushtubh(syllables)

    if len(syllables) >= 32:
        vipula_labels[0] = identify_vipula(syllables[0:4])
        vipula_labels[1] = identify_vipula(syllables[16:20])

    # Затем рисуем гуру/лакху поверх
    for i in range(line_length):
        line = lines[i] if i < len(lines) else []
        for j in range(line_length):
            x, y = j, line_length - 1 - i
            if j < len(line):
                syl = line[j]
                guru = is_guru_syllable_slp1(syl)
                base_color = 'black' if guru else 'white'
            else:
                base_color = 'white'
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor=base_color, edgecolor='black'))

    # Поверх всех — подкраска випул полупрозрачным фоном
    for shloka_start in range(0, len(syllables), 32):
        if shloka_start + 32 <= len(syllables):
            shloka = syllables[shloka_start:shloka_start + 32]
            vipula_1 = identify_vipula(shloka[0:4])
            vipula_2 = identify_vipula(shloka[16:20])

            row_offset = line_length - 1 - (shloka_start // line_length)
            row_1 = row_offset
            row_3 = row_offset - 2

            for j in range(4):
                if 0 <= row_1 < line_length:
                    ax.add_patch(Rectangle((j, row_1), 1, 1, facecolor=vipula_colors[vipula_1], alpha=0.65))
                if 0 <= row_3 < line_length:
                    ax.add_patch(Rectangle((j, row_3), 1, 1, facecolor=vipula_colors[vipula_2], alpha=0.65))

    ax.set_title(f"{line_length}x{line_length} Grid — {metre_type}
Vipula: {vipula_labels[0]}, {vipula_labels[1]}", fontsize=10)(f"{line_length}x{line_length} Grid — {metre_type}\nVipula: {vipula_labels[0]}, {vipula_labels[1]}", fontsize=10)


    legend_elements = [
        Patch(facecolor='black', edgecolor='black', label='Guru'),
        Patch(facecolor='white', edgecolor='black', label='Laghu')
    ]
    for name, color in vipula_colors.items():
        legend_elements.append(Patch(facecolor=color, alpha=0.65, label=f'Vipula: {name}'))
    for name, color in anushtubh_colors.items():
        legend_elements.append(Patch(facecolor=color, alpha=0.5, label=f'Type: {name}'))

    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=2, fontsize=8)
    st.pyplot(fig)

# ===== Streamlit UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu + Vipula + Anuṣṭubh type)")

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
