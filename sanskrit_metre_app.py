import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
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
    pattern = r"([^aAiIuUfFxXeEoOMH]*[aAiIuUfFxXeEoO][MH]?[^aAiIuUfFxXeEoOMH]?)"
    return [s for s in re.findall(pattern, text) if s]

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
def visualize_grid(syllables: list[str], line_length: int) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, line_length)
    ax.set_ylim(0, line_length)
    ax.axis('off')

    # строки слогов
    lines = [syllables[i:i+line_length] for i in range(0, len(syllables), line_length)]
    while len(lines) < line_length:
        lines.append([])

    # базовая сетка и текст слога
    for i, row in enumerate(lines):
        for j in range(line_length):
            y = line_length - 1 - i
            syl = row[j] if j < len(row) else ''
            guru = is_guru_syllable_slp1(syl) if syl else False
            face = 'black' if guru else 'white'
            txt_color = 'white' if guru else 'black'
            ax.add_patch(Rectangle((j, y), 1, 1, facecolor=face, edgecolor='black'))
            if syl:
                ax.text(j+0.5, y+0.5, syl, ha='center', va='center', color=txt_color, fontsize=10)

    # випулы
    for start in range(0, min(len(syllables), 32*108), 32):
        if start+32 > len(syllables): break
        block = syllables[start:start+32]
        v1 = identify_vipula(block[0:4])
        v2 = identify_vipula(block[16:20])
        top_row = line_length - 1 - (start // line_length)
        mid_row = top_row - 2
        for idx, vip in enumerate((v1, v2)):
            if vip and vip in vipula_colors:
                row = top_row if idx == 0 else mid_row
                for j in range(4):
                    ax.add_patch(Rectangle((j, row), 1, 1,
                                            facecolor=vipula_colors[vip], alpha=0.65))

    # заголовок и легенда
    title = f"{line_length}×{line_length} Grid"
    if classify_pathya(syllables):
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)

    legend = [Patch(facecolor='black', label='Guru'), Patch(facecolor='white', label='Laghu')]
    for name, col in vipula_colors.items():
        legend.append(Patch(facecolor=col, alpha=0.65, label=name))
    legend.append(Patch(facecolor=pathyā_color, alpha=0.5, label='Pathyā'))
    ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)
    st.pyplot(fig)

# ===== UI =====
st.title("Shloka Visualizer (IAST → SLP1 → Guru/Laghu + Vipula + Pathyā)")
text = st.text_area("Введите шлоки на IAST (до 108 шлок):", height=200)
size = st.selectbox("Слогов в строке:", [8, 16, 32], index=0)
if st.button("Показать"):
    if text:
        s = normalize(text)
        syl = split_syllables_slp1(s)
        blocks = [syl[i:i+size*size] for i in range(0, len(syl), size*size)]
        for i, b in enumerate(blocks[:108]):
            st.subheader(f"Шлока {i+1}")
            visualize_grid(b, size)
    else:
        st.warning("Введите текст IAST")
