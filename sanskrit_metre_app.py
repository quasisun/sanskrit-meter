import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import re
import unicodedata
from collections import Counter, defaultdict

st.set_page_config(layout="wide")
st.title("Sanskrit Śloka Visualizer")

# — Sidebar: настройки —
st.sidebar.header("Настройки визуализации")

# 1) Размер сетки (syllables per row)
line_length = st.sidebar.selectbox(
    "Слогов в строке:",
    options=[8, 16, 32],
    index=0,
    help="8 = pada, 16 = ardhaśloka, 32 = śloka"
)

# 2) Что показывать
show_pathya = st.sidebar.checkbox("Выделять Pathyā-anuṣṭubh", True)
show_vipula  = st.sidebar.checkbox("Показывать Vipulā", True)
show_anu     = st.sidebar.checkbox("Показывать Anuprāsa", False)
show_yam     = st.sidebar.checkbox("Показывать Yamaka", False)

# 3) Vipulā: выбор типов
vipula_options = ["Nagari", "Bhavānī", "Śārdūla", "Āryā", "Vidyunmālā"]
selected_vip = st.sidebar.multiselect(
    "Типы Vipulā:",
    options=vipula_options,
    default=vipula_options
)

st.sidebar.markdown("---")
st.sidebar.write("© Svetlana Kreutzer 2025")

# — Текст ввода —
text = st.text_area("Вставьте IAST-текст шлоки:", height=180)
if not text.strip():
    st.info("Вставьте текст, и настройте опции слева.")
    st.stop()

# — Предобработка —
def normalize(text: str) -> str:
    # убираем danda, цифры, нормализуем Unicode
    txt = re.sub(r"[।॥\d]", "", text)
    return unicodedata.normalize("NFC", txt)

def split_syllables(txt: str) -> list[str]:
    s = re.sub(r"\s+", "", txt)
    pat = r"([^aeiouāīūṛṝeoau]*[aeiouāīūṛṝeoau]+(?:ṃ|ḥ)?(?:[kgṅcjñṭḍṇtdnpbmyrlvśṣsh](?!h))?)"
    return re.findall(pat, s)

# — Метрика —
def is_guru(s: str) -> bool:
    # долгота или закрытый слог
    if re.search(r"[āīūṛṝeoau]", s): return True
    if re.search(r"[ṃḥ]", s): return True
    if re.search(r"[aeiou][^aeiou]{2,}", s): return True
    return False

def get_padas(sylls: list[str]) -> list[list[str]]:
    return [sylls[i*line_length:(i+1)*line_length]
            for i in range(len(sylls)//line_length)]

# Pathyā-anuṣṭubh
def is_pathya(sylls: list[str]) -> bool:
    if len(sylls) < 32: return False
    p3 = sylls[16:24]; p4 = sylls[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5])
         and  is_guru(p4[4]) and is_guru(p4[5]))

# Vipulā
vipula_map = {
    'lglg':'Nagari','lllg':'Bhavānī','llgg':'Śārdūla',
    'glgg':'Āryā','gglg':'Vidyunmālā'
}
def identify_vipula(half: list[str]) -> str:
    key = "".join('g' if is_guru(s) else 'l' for s in half[:4])
    return vipula_map.get(key, "")

# Anuprāsa (строго: повтор инициала ≥3)
def detect_anuprasa(pada: list[str]) -> set[str]:
    inits = [re.match(r"[^aeiouāīūṛṝeoau]*", s).group(0) for s in pada]
    cnt = Counter(inits)
    return {i for i,c in cnt.items() if i and c >= 3}

# Yamaka (śloka-yamaka зеркально 1↔3,2↔4)
def detect_yamaka(sylls: list[str]) -> set[tuple[int,int]]:
    coords = set()
    if len(sylls) < 32: return coords
    # только для line_length=8
    for pair in [(0,2),(1,3)]:
        for i in range(line_length):
            a = sylls[pair[0]*line_length+i]
            b = sylls[pair[1]*line_length+i]
            if a == b and a:
                coords.add((pair[0],i))
                coords.add((pair[1],i))
    return coords

# — Визуализация —
sylls = split_syllables(normalize(text))
blocks = [sylls[i:i+line_length*line_length]
          for i in range(0, len(sylls), line_length*line_length)]

for bi, block in enumerate(blocks):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(0,line_length)
    ax.set_ylim(0,line_length)
    # предвычислить
    pathya = is_pathya(block) if show_pathya else False
    vip1 = identify_vipula(block[0:line_length*2])   # first half
    vip2 = identify_vipula(block[line_length*2:line_length*4]) if len(block)>=line_length*4 else ""
    yam_coords = detect_yamaka(block) if show_yam else set()

    for i in range(line_length):
        pada = block[i*line_length:(i+1)*line_length]
        anu_inits = detect_anuprasa(pada) if show_anu else set()
        for j in range(line_length):
            idx = i*line_length + j
            syl = block[idx] if idx < len(block) else ""
            # базовая ячейка
            face = 'black' if is_guru(syl) else 'white'
            ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                   facecolor=face,edgecolor='gray'))
            ax.text(j+0.5,line_length-1-i+0.5,syl,
                    ha='center',va='center',
                    color='white' if face=='black' else 'black',
                    fontsize=8)

            # Vipulā
            if show_vipula and vip1 in selected_vip and i < (line_length*2)//line_length and j<4:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       facecolor='#ffa500',alpha=0.4))
            if show_vipula and vip2 in selected_vip and i >= (line_length*2)//line_length and j<4:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       facecolor='#1e90ff',alpha=0.4))

            # Anuprāsa
            if show_anu and get_initial(syl) in anu_inits:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       fill=False,edgecolor='blue',linewidth=2))

            # Yamaka
            if show_yam and (i,j) in yam_coords:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       fill=False,edgecolor='purple',linewidth=2))

    title = f"Block {bi+1}"
    if show_pathya and pathya:
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)

    st.pyplot(fig)

# — Legend —
st.markdown("**Legend:**")
col1, col2 = st.columns(2)
with col1:
    st.markdown("- **Black** = Guru  
                 **White** = Laghu  
                 **Blue border** = Anuprāsa  
                 **Purple border** = Yamaka")
with col2:
    st.markdown("- **Orange** = Vipulā Nagari  
                 **Blue**   = Vipulā Bhavānī")

st.markdown("App by Svetlana Kreutzer 2025 ©")
