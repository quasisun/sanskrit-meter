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


def normalize(text):
    text = text.strip()
    return transliterate(text, sanscript.IAST, sanscript.SLP1)

def split_syllables_slp1(text):
    # Слог = (согласные) + гласная + (анусвара/висарга) + (опционально — одна согласная)
    pattern = r"""
        ([^aAiIuUfFxXeEoOMH]*    # начальные согласные
         [aAiIuUfFxXeEoO]         # гласная
         [MH]?                    # анусвара или висарга
         [^aAiIuUfFxXeEoOMH]?)    # одна согласная после (опционально)
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

    for i in range(line_length):
        line = lines[i] if i < len(lines) else []
        for j in range(line_length):
            if j < len(line):
                syl = line[j]
                guru = is_guru_syllable_slp1(syl)
                base_color = 'black' if guru else 'white'
            else:
                base_color = 'white'
            ax.add_patch(Rectangle((j, line_length - 1 - i), 1, 1, facecolor=base_color, edgecolor='black'))

    ax.set_title(f'{line_length}x{line_length} Grid', fontsize=12)

    legend_elements = [
        Patch(facecolor='black', edgecolor='black', label='Guru'),
        Patch(facecolor='white', edgecolor='black', label='Laghu')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=8)

    st.pyplot(fig)

# ===== Streamlit UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu)")

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
