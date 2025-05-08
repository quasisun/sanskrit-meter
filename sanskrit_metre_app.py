import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
import re
import unicodedata

# ===== Конфигурация цветов =====
vipula_colors = {
    'Nāgarī': '#FFA500',      # Оранжевый
    'Bhavānī': '#1E90FF',     # Синий
    'Śārdūla': '#32CD32',     # Зелёный
    'Āryā': '#FF6347',        # Красный
    'Vidyunmālā': '#9370DB',  # Фиолетовый
    'Other': '#D3D3D3'        # Серый
}

anuprasa_color = 'blue'
yamaka_color = 'purple'

# ===== Обработка текста =====
short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']
consonants = '[kgṅcjñṭḍṇtdnpbmyrlvśṣsh]'

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[।॥|॥]', '', text)
    return text.strip()

def split_syllables(text):
    text = re.sub(r'\s+', '', text)
    pattern = r"""
        ([^aeiouāīūṛṝeaiouṃḥ]*       
         [aeiouāīūṛṝeaiou]            
         (?:ṃ|ḥ)?                     
         (?:{c}(?!h))?)               
    """.format(c=consonants)
    syllables = re.findall(pattern, text, re.VERBOSE)
    return [s[0] for s in syllables if s[0]]

def is_guru(syl):
    v = re.search(r'[aeiouāīūṛṝeaiou]', syl)
    if not v:
        return False
    vowel = v.group()
    if vowel in long_vowels:
        return True
    if re.search(r'[ṃḥ]', syl):
        return True
    if re.search(r'[aeiouṛḷ]..', syl):
        return True
    return False

def identify_vipula(half_shloka):
    pattern = ''.join(['g' if is_guru(s) else 'l' for s in half_shloka[:4]])
    vipula_patterns = {
        'lglg': 'Nāgarī',
        'lllg': 'Bhavānī',
        'llgg': 'Śārdūla',
        'glgg': 'Āryā',
        'gglg': 'Vidyunmālā'
    }
    return vipula_patterns.get(pattern, 'Other')

def detect_anuprasa(line):
    initials = [re.match(r'[^\W\d_]*', syl).group(0) for syl in line if syl]
    repeats = [s for s in initials if initials.count(s) > 1 and s]
    return set(repeats)

def detect_yamaka(line):
    return set([s for s in line if line.count(s) > 1])

# ===== Визуализация =====
def visualize_block(syllables):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')

    vipulas = []
    if len(syllables) >= 32:
        vipulas = [identify_vipula(syllables[0:16]), identify_vipula(syllables[16:32])]
    else:
        vipulas = ['Other', 'Other']

    for i in range(8):
        line = syllables[i * 8:(i + 1) * 8]
        anuprasa_set = detect_anuprasa(line)
        yamaka_set = detect_yamaka(line)
        for j, syl in enumerate(line):
            x, y = j, 7 - i
            guru = is_guru(syl)

            # Vipula background
            if (i == 0 and j < 4) or (i == 2 and j < 4):
                vipula = vipulas[0] if i < 2 else vipulas[1]
                color = vipula_colors.get(vipula, '#D3D3D3')
                ax.add_patch(Rectangle((x, y), 1, 1, color=color, alpha=0.3))

            # Guru/Laghu base
            base_color = 'black' if guru else 'white'
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor=base_color, edgecolor='black'))

            # Anuprāsa border
            initial = re.match(r'[^\W\d_]*', syl).group(0)
            if initial in anuprasa_set:
                ax.add_patch(Rectangle((x, y), 1, 1, fill=False, edgecolor=anuprasa_color, linewidth=2))

            # Yamaka marker
            if syl in yamaka_set:
                ax.add_patch(Circle((x + 0.5, y + 0.5), 0.1, color=yamaka_color))

    ax.set_title(f'Vipula: {vipulas[0]}, {vipulas[1]}', fontsize=10)

    # Легенда
    legend_elements = [
        Patch(facecolor='black', edgecolor='black', label='Guru'),
        Patch(facecolor='white', edgecolor='black', label='Laghu'),
        Patch(edgecolor=anuprasa_color, facecolor='none', linewidth=2, label='Anuprāsa'),
        Patch(facecolor=yamaka_color, label='Yamaka', alpha=0.5)
    ]
    for name, color in vipula_colors.items():
        legend_elements.append(Patch(facecolor=color, alpha=0.3, label=f'Vipula: {name}'))
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.35), ncol=2, fontsize=8)

    st.pyplot(fig)

# ===== Streamlit UI =====
st.title("Shloka Visualizer: Guru, Laghu, Vipula, Anuprāsa, Yamaka")

text_input = st.text_area("Введите шлоки на IAST (до 64 слогов на блок):", height=200)

if st.button("Визуализировать"):
    if text_input.strip():
        syllables = split_syllables(normalize(text_input))
        blocks = [syllables[i:i + 64] for i in range(0, len(syllables), 64)]
        for i, block in enumerate(blocks):
            st.subheader(f"Блок {i+1}")
            visualize_block(block)
    else:
        st.warning("Пожалуйста, введите текст.")
