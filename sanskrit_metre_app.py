import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import re
import unicodedata
from collections import Counter

# —————————————————————————————————————————————————————————————————————
# Настройка страницы
# —————————————————————————————————————————————————————————————————————
st.set_page_config(layout="wide")
st.title("Sanskrit Śloka Visualizer")

# — Sidebar: настройки —
st.sidebar.header("Настройки визуализации")

# 1) Размер сетки (количество слогов в строке)
line_length = st.sidebar.selectbox(
    "Слогов в строке:",
    [8, 16, 32],
    index=0,
    help="8 = pāda, 16 = ardha-śloka, 32 = śloka"
)

# 2) Включаемые элементы
show_pathya = st.sidebar.checkbox("Выделять Pathyā-anuṣṭubh", True)
show_vipula = st.sidebar.checkbox("Показывать Vipulā", True)
show_anu    = st.sidebar.checkbox("Показывать Anuprāsa", False)
show_yam    = st.sidebar.checkbox("Показывать Yamaka", False)

# 3) Типы Vipulā
vipula_options = ["Nagari", "Bhavānī", "Śārdūla", "Āryā", "Vidyunmālā"]
selected_vip = st.sidebar.multiselect(
    "Типы Vipulā:",
    vipula_options,
    default=vipula_options
)

st.sidebar.markdown("---")
st.sidebar.write("© Svetlana Kreutzer 2025")

# —————————————————————————————————————————————————————————————————————
# Утилиты для разбора и метрики
# —————————————————————————————————————————————————————————————————————

def normalize(text: str) -> str:
    # удаляем danda и цифры, нормализуем Unicode
    t = re.sub(r"[।॥\d]", "", text)
    return unicodedata.normalize("NFC", t.strip())

def split_syllables(txt: str) -> list[str]:
    # удаляем пробелы и делим на слоги по IAST
    s = re.sub(r"\s+", "", txt)
    pattern = r"""
      ([kgṅcjñṭḍṇtdnpbmyrlvśṣshṅ]*    # начальный кластер согласных
       [aeiouāīūṛṝeoau]               # основная гласная
       (?:ṃ|ḥ)?                       # анусвара или висарга
       (?:[kgṅcjñṭḍṇtdnpbmyrlvśṣshṅ]{0,2})  # до двух финальных согласных
      )
    """
    return re.findall(pattern, s, re.IGNORECASE | re.VERBOSE)

def is_guru(s: str) -> bool:
    # долгий гласный, анусвара/висарга или закрытый слог
    if re.search(r"[āīūṛṝeoau]", s): return True
    if re.search(r"[ṃḥ]", s): return True
    if re.search(r"[aeiou][^aeiou]{2,}", s): return True
    return False

def get_padas(sylls: list[str]) -> list[list[str]]:
    # делим на pāda по заданному line_length
    return [
        sylls[i*line_length:(i+1)*line_length]
        for i in range(len(sylls)//line_length)
    ]

def is_pathya(sylls: list[str]) -> bool:
    # Pathyā-anuṣṭubh для первой śloka (32 слога)
    if len(sylls) < 32: return False
    p3 = sylls[16:24]; p4 = sylls[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5])
         and  is_guru(p4[4]) and is_guru(p4[5]))

vipula_map = {
    'lglg': 'Nagari', 'lllg': 'Bhavānī',
    'llgg': 'Śārdūla','glgg': 'Āryā',
    'gglg': 'Vidyunmālā'
}
def identify_vipula(half: list[str]) -> str:
    key = "".join('g' if is_guru(s) else 'l' for s in half[:4])
    return vipula_map.get(key, "")

def detect_anuprasa(pada: list[str]) -> set[str]:
    # повтор инициала ≥3 раза в pāda
    inits = [re.match(r"[^aeiouāīūṛṝeoau]*", s).group(0) for s in pada]
    cnt = Counter(inits)
    return {i for i,c in cnt.items() if i and c >= 3}

def detect_yamaka(sylls: list[str]) -> set[tuple[int,int]]:
    # śloka-yamaka зеркально 1↔3, 2↔4 для line_length==8
    coords = set()
    if line_length != 8 or len(sylls) < 32:
        return coords
    for a,b in [(0,2),(1,3)]:
        for i in range(line_length):
            x = sylls[a*8 + i]; y = sylls[b*8 + i]
            if x and x == y:
                coords.add((a, i)); coords.add((b, i))
    return coords

# —————————————————————————————————————————————————————————————————————
# Основная визуализация
# —————————————————————————————————————————————————————————————————————

text = st.text_area("Вставьте IAST-текст ślok:", height=180)
if text.strip():
    sylls = split_syllables(normalize(text))
    blocks = [
        sylls[i:i + line_length*line_length]
        for i in range(0, len(sylls), line_length*line_length)
    ]

    for bi, block in enumerate(blocks):
        fig, ax = plt.subplots(figsize=(4,4))
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(0, line_length); ax.set_ylim(0, line_length)

        pathya = is_pathya(block) if show_pathya else False
        half = line_length * (line_length // line_length)  # half-syllable count
        vip1 = identify_vipula(block[0:line_length*2])
        vip2 = identify_vipula(block[line_length*2:line_length*4])
        yam_coords = detect_yamaka(block) if show_yam else set()

        for i in range(line_length):
            pada = block[i*line_length:(i+1)*line_length]
            anu = detect_anuprasa(pada) if show_anu else set()
            for j in range(line_length):
                idx = i*line_length + j
                syl = block[idx] if idx < len(block) else ""
                face = 'black' if is_guru(syl) else 'white'
                ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                       facecolor=face, edgecolor='gray'))
                ax.text(j+0.5, line_length-1-i+0.5, syl,
                        ha='center', va='center',
                        color='white' if face=='black' else 'black',
                        fontsize=8)

                # Vipulā
                if show_vipula and j < 4:
                    half_idx = 0 if i < (line_length*2)//line_length else 1
                    vip_label = vip1 if half_idx==0 else vip2
                    if vip_label in selected_vip:
                        color = '#ffa500' if half_idx==0 else '#1e90ff'
                        ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                               facecolor=color, alpha=0.4))

                # Anuprāsa
                if show_anu and re.match(r"[^aeiouāīūṛṝeoau]*", syl).group(0) in anu:
                    ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                           fill=False, edgecolor='blue', linewidth=2))

                # Yamaka
                if show_yam and (i, j) in yam_coords:
                    ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                           fill=False, edgecolor='purple', linewidth=2))

        title = f"Block {bi+1}"
        if show_pathya and pathya:
            title += " — Pathyā-anuṣṭubh"
        ax.set_title(title, fontsize=10)
        st.pyplot(fig)

    # — Легенда —
    st.markdown("**Legend:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
- **Black** = Guru  
- **White** = Laghu  
- **Blue border** = Anuprāsa  
- **Purple border** = Yamaka
""")
    with col2:
        st.markdown(f"""
- **Orange** = Vipulā (first half)  
- **Blue**   = Vipulā (second half)  
- **Pathyā-anuṣṭubh** = {'Yes' if show_pathya else 'Off'}
""")
    st.markdown("---")
    st.markdown("App by Svetlana Kreutzer 2025 ©")
