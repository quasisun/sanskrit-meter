import streamlit as st
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re

# --- Streamlit page config and title ---
st.set_page_config(page_title="Sloka Meter Visualizer", layout="wide")
st.title("Sloka Meter Visualizer")
st.markdown(
    "Convert IAST text to SLP1, split into syllables, classify Laghus (light) and Gurus (heavy), "
    "detect meters and alankāras, and visualize as a grid with customizable options.")

# --- Sidebar options ---
st.sidebar.header("Options")
grid_size = st.sidebar.selectbox("Grid size (number of syllables)", [8, 16, 32], index=0)
show_pada_anustubh = st.sidebar.checkbox("Highlight padā anustubh (4×8)", True)

st.sidebar.markdown("### Yamaka Alankāras to highlight")
opt_padaanta = st.sidebar.checkbox("Pādānta Yamaka", False)
opt_padadi   = st.sidebar.checkbox("Pādādi Yamaka", False)
opt_vikranta = st.sidebar.checkbox("Vikrānta Yamaka", False)

st.sidebar.markdown("### Sanskrit terms (IAST)")
st.sidebar.markdown("- laghu: light syllable")
st.sidebar.markdown("- guru: heavy syllable")
st.sidebar.markdown("- padā: quarter" )
st.sidebar.markdown("- anustubh: classical meter of 4×8 syllables")
st.sidebar.markdown("- yamaka: repetition alankāra")

# --- Input area ---
text_iast = st.text_area("Enter IAST text (4 pādas of 8 syllables)", height=200)

if text_iast:
    # 1. Normalize and convert to SLP1
    text_clean = re.sub(r'[।॥\d]', '', text_iast.strip())
    text_slp = transliterate(text_clean, sanscript.IAST, sanscript.SLP1)

    # 2. Split into syllables (SLP1)
    # pattern: vowel groups AI, AU or simple vowels, optional anusvāra/visarga, plus trailing consonant if standalone
    vowel_pattern = r'(?:AI|AU|[aiuIREo])'
    syl_pat = rf'([^ {vowel_pattern}]*{vowel_pattern}(?:M|H)?(?:[kgGNcjJTDtpbmyrlvSZsh](?!h))?)'
    sylls = re.findall(syl_pat, text_slp)
    # pad or trim to grid_size
    if len(sylls) < grid_size:
        sylls += [''] * (grid_size - len(sylls))
    else:
        sylls = sylls[:grid_size]

    # 3. Classify laghu (light) vs guru (heavy)
    def is_guru(s):
        return bool(re.search(r'(A|I|U|R|E|O|M|H|[aiuIREo][^aiuIREo]{2,})', s))
    classes = [is_guru(s) for s in sylls]

    # 4. Meter detection: padā anustubh
    is_anustubh = (grid_size == 32 and all(len(sylls[i*8:(i+1)*8]) == 8 for i in range(4)))

    # 5. Plot grid
    cols = int(grid_size**0.5)
    rows = cols
    fig, ax = plt.subplots(figsize=(cols, rows))
    ax.set_xticks([]); ax.set_yticks([])
    # draw squares and text
    for idx, syl in enumerate(sylls):
        row = rows - 1 - (idx // cols)
        col = idx % cols
        guru = classes[idx]
        face = 'black' if guru else 'white'
        text_color = 'white' if guru else 'black'
        ax.add_patch(Rectangle((col, row), 1, 1, facecolor=face, edgecolor='gray'))
        if syl:
            ax.text(col+0.5, row+0.5, syl, ha='center', va='center', color=text_color, fontsize=12)

    # highlight padā anustubh
    if show_pada_anustubh and is_anustubh:
        rect = Rectangle((0, 0), cols, rows, fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(rect)

    # legend
    legend_items = [Patch(facecolor='white', edgecolor='gray', label='laghu'),
                    Patch(facecolor='black', edgecolor='gray', label='guru')]
    if show_pada_anustubh and is_anustubh:
        legend_items.append(Patch(facecolor='none', edgecolor='red', label='padā anustubh'))
    ax.legend(handles=legend_items, loc='upper right', bbox_to_anchor=(1.2, 1))

    st.pyplot(fig)

    # 6. Output detections
    st.subheader("Detected features:")
    feats = []
    if is_anustubh: feats.append("padā anustubh")
    if opt_padaanta: feats.append("pādānta yamaka: not implemented")
    if opt_padadi:   feats.append("pādādi yamaka: not implemented")
    if opt_vikranta: feats.append("vikrānta yamaka: not implemented")
    st.write(feats or "None detected.")
