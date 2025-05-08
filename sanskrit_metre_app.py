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

line_length = st.sidebar.selectbox("Слогов в строке:", [8,16,32], 0,
    help="8 = pāda, 16 = ardha-śloka, 32 = śloka")

show_pathya = st.sidebar.checkbox("Выделять Pathyā-anuṣṭubh", True)
show_vipula  = st.sidebar.checkbox("Показывать Vipulā", True)
show_anu     = st.sidebar.checkbox("Показывать Anuprāsa", False)
show_yam     = st.sidebar.checkbox("Показывать Yamaka", False)

vipula_options = ["Nagari","Bhavānī","Śārdūla","Āryā","Vidyunmālā"]
selected_vip = st.sidebar.multiselect("Типы Vipulā:", vipula_options, vipula_options)

st.sidebar.markdown("---")
st.sidebar.write("© Svetlana Kreutzer 2025")

# —————————————————————————————————————————————————————————————————————
# Утилиты разбора
# —————————————————————————————————————————————————————————————————————
VOWELS = set("aeiouāīūṛṝeoau")

def normalize(text: str) -> str:
    t = re.sub(r"[।॥\d]", "", text)
    return unicodedata.normalize("NFC", t.strip())

def split_syllables(txt: str) -> list[str]:
    s = re.sub(r"\s+", "", txt)
    # [optional consonants] + vowel + [ṃ/ḥ]? + [0–2 final consonants]
    pattern = r"([kgṅcjñṭḍṇtdnpbmyrlvśṣshṅ]*[aeiouāīūṛṝeoau](?:ṃ|ḥ)?[kgṅcjñṭḍṇtdnpbmyrlvśṣshṅ]{0,2})"
    return re.findall(pattern, s)

def is_guru(s: str) -> bool:
    if not s:
        return False
    # долгие
    if re.search(r"[āīūṛṝeoau]", s):
        return True
    # анусвара/висарга
    if s.endswith("ṃ") or s.endswith("ḥ"):
        return True
    # закрытый слог — заканчивается на согласную
    if s[-1] not in VOWELS:
        return True
    return False

def get_padas(sylls: list[str]) -> list[list[str]]:
    return [sylls[i*line_length:(i+1)*line_length]
            for i in range(len(sylls)//line_length)]

def is_pathya(sylls: list[str]) -> bool:
    if len(sylls) < 32:
        return False
    p3, p4 = sylls[16:24], sylls[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5])
         and  is_guru(p4[4]) and is_guru(p4[5]))

vipula_map = {
   'lglg':'Nagari','lllg':'Bhavānī','llgg':'Śārdūla',
   'glgg':'Āryā','gglg':'Vidyunmālā'
}
def identify_vipula(half: list[str]) -> str:
    key = "".join('g' if is_guru(x) else 'l' for x in half[:4])
    return vipula_map.get(key, "")

def detect_anuprasa(pada: list[str]) -> set[str]:
    inits = [re.match(r"[^aeiouāīūṛṝeoau]*", x).group(0) for x in pada]
    cnt = Counter(inits)
    return {c for c,n in cnt.items() if c and n>=3}

def detect_yamaka(sylls: list[str]) -> set[tuple[int,int]]:
    coords = set()
    if line_length!=8 or len(sylls)<32:
        return coords
    for a,b in [(0,2),(1,3)]:
        for i in range(8):
            x = sylls[a*8+i]; y = sylls[b*8+i]
            if x and x==y:
                coords.add((a,i)); coords.add((b,i))
    return coords

# —————————————————————————————————————————————————————————————————————
# Основная визуализация
# —————————————————————————————————————————————————————————————————————
text = st.text_area("Вставьте IAST-текст ślok:", height=180)
if not text.strip():
    st.stop()

sylls = split_syllables(normalize(text))
blocks = [sylls[i:i+line_length*line_length]
          for i in range(0, len(sylls), line_length*line_length)]

for bi,blk in enumerate(blocks):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(0,line_length); ax.set_ylim(0,line_length)

    pathya = is_pathya(blk) if show_pathya else False
    vip1 = identify_vipula(blk[:line_length*2])
    vip2 = identify_vipula(blk[line_length*2:line_length*4])
    anu_coords = {}
    yam_coords = detect_yamaka(blk) if show_yam else set()

    for i in range(line_length):
        pada = blk[i*line_length:(i+1)*line_length]
        anu = detect_anuprasa(pada) if show_anu else set()
        for j in range(line_length):
            idx = i*line_length+j
            syl = blk[idx] if idx<len(blk) else ""
            guru = is_guru(syl)
            face = "black" if guru else "white"
            ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                   facecolor=face,edgecolor="gray"))
            ax.text(j+0.5,line_length-1-i+0.5,syl,
                    ha="center",va="center",
                    color="white" if guru else "black",fontsize=8)

            if show_vipula and j<4:
                half = 0 if i<((line_length*2)//line_length) else 1
                label = vip1 if half==0 else vip2
                if label in selected_vip:
                    clr = "#ffa500" if half==0 else "#1e90ff"
                    ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                           facecolor=clr,alpha=0.4))

            if show_anu and re.match(r"[^aeiouāīūṛṝeoau]*",syl).group(0) in anu:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       fill=False,edgecolor="blue",linewidth=2))

            if show_yam and (i,j) in yam_coords:
                ax.add_patch(Rectangle((j,line_length-1-i),1,1,
                                       fill=False,edgecolor="purple",linewidth=2))

    title = f"Block {bi+1}"
    if show_pathya and pathya:
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title,fontsize=10)
    st.pyplot(fig)

# — Legend —
st.markdown("**Legend:**")
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
- **Black** = Guru  
- **White** = Laghu  
- **Blue border** = Anuprāsa  
- **Purple border** = Yamaka
""")
with c2:
    st.markdown("""
- **Orange** = Vipulā (first half)  
- **Blue**   = Vipulā (second half)  
- **Pathyā-anuṣṭubh** = highlighted in title
""")
st.markdown("---")
st.markdown("App by Svetlana Kreuzer 2025 ©")
