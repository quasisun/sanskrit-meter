import streamlit as st
import matplotlib.pyplot as plt
import re
import unicodedata
from indic_transliteration.sanscript import transliterate

# Vowel definitions
short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']

def normalize_text(text):
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[।॥|॥]', '', text)
    return text.strip()

def detect_script(text):
    if any('\u0B80' <= c <= '\u0BFF' for c in text):
        return 'tamil'
    elif any('\u0900' <= c <= '\u097F' for c in text):
        return 'devanagari'
    else:
        return 'iast'

def transliterate_to_iast(text):
    script = detect_script(text)
    if script == 'iast':
        return text.lower()
    return transliterate(text, script, 'iast').lower()

def split_syllables(text):
    return re.findall(r'[^aeiouṛḷāīūṝeoau]*[aeiouṛḷāīūṝeoau]+(?:[ṃḥ])?', text)

def is_guru(syl):
    if any(v in syl for v in long_vowels):
        return True
    if syl.endswith('ṃ') or syl.endswith('ḥ'):
        return True
    return False

def make_blocks(syllables, row_length, rows_per_block=8):
    block_size = row_length * rows_per_block
    return [syllables[i:i+block_size] for i in range(0, len(syllables), block_size)]

def syllables_to_grid(syllables, row_length):
    grid = []
    for i in range(0, len(syllables), row_length):
        row = syllables[i:i+row_length]
        binary = [1 if is_guru(s) else 0 for s in row]
        binary += [0]*(row_length - len(binary))
        grid.append(binary)
    while len(grid) < 8:
        grid.append([0]*row_length)
    return grid

def plot_grid(grid, index, row_length):
    fig, ax = plt.subplots(figsize=(row_length / 2, 4))
    ax.imshow(grid, cmap='gray', interpolation='nearest')
    ax.axis('off')
    ax.set_title(f'Block {index+1} ({row_length}×8)')
    st.pyplot(fig)

# === Streamlit Interface ===

st.title("Sanskrit Meter Visualizer")
st.markdown("Upload Sanskrit or Tamil text. Select the block size for syllable grouping.")

text_input = st.text_area("Paste your Sanskrit or Tamil text below:", height=200)

row_length = st.selectbox("Syllables per line (row):", [8, 16, 32], index=0)

if st.button("Generate Visualization"):
    if not text_input.strip():
        st.warning("Please enter some text.")
    else:
        try:
            iast = transliterate_to_iast(normalize_text(text_input))
            syllables = split_syllables(iast)
            blocks = make_blocks(syllables, row_length=row_length)

            for i, block in enumerate(blocks):
                grid = syllables_to_grid(block, row_length)
                plot_grid(grid, i, row_length)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
