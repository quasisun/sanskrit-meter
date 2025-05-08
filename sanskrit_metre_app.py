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
    'Nagari': '#FFA500',
    'Bhavani': '#1E90FF',
    'Shardula': '#32CD32',
    'Arya': '#FF6347',
    'Vidyunmala': '#9370DB',
    'Other': '#D3D3D3'
}

anushtubh_colors = {
    'Pathyā-anuṣṭubh': '#B0E0E6',
    'Vipulā-anuṣṭubh': '#F5DEB3',
    'Unknown': '#FFFFFF'
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
    vipula_rows = [line_length - 1, line_length - 3]
    for idx, row in enumerate(vipula_rows):
        for j in range(4):
            x, y = j, row
            color = vipula_colors[vipula_labels[idx]]
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, alpha=0.3))

ax.set_title(f'{line_length}x{line_length} Grid — {metre_type}
Vipula: {vipula_labels[0]}, {vipula_labels[1]}', fontsize=10)

    legend_elements = [
        Patch(facecolor='black', edgecolor='black', label='Guru'),
        Patch(facecolor='white', edgecolor='black', label='Laghu')
    ]
    for name, color in vipula_colors.items():
        legend_elements.append(Patch(facecolor=color, alpha=0.3, label=f'Vipula: {name}'))
    for name, color in anushtubh_colors.items():
        legend_elements.append(Patch(facecolor=color, alpha=0.1, label=f'Type: {name}'))

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
