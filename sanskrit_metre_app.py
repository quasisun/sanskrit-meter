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
sb = st.sidebar
sb.header("Настройки визуализации")

line_length = sb.selectbox(
    "Слогов в строке:",
    options=[8, 16, 32],
    index=0,
    help="8 = pāda, 16 = ardha-śloka, 32 = śloka"
)

show_pathya = sb.checkbox("Выделять Pathyā-anuṣṭubh", True)
show_vipula  = sb.checkbox("Показывать Vipulā", True)
show_anu     = sb.checkbox("Показывать Anuprāsa", False)
show_yam     = sb.checkbox("Показывать Yamaka", False)

vipula_options = ["Nagari", "Bhavānī", "Śārdūla", "Āryā", "Vidyunmālā"]
selected_vip = sb.multiselect(
    "Типы Vipulā:", options=vipula_options, default=vipula_options
)

sb.markdown("---")
sb.write("© Svetlana Kreutzer 2025")

# —————————————————————————————————————————————————————————————————————
# Утилиты разбора и метрические правила
# —————————————————————————————————————————————————————————————————————
CONSONANTS = "kgṅcjñṭḍṇtdnpbmyrlvśṣshṅ"
# Долгие гласные и дифтонги
LONG_VOWELS = ["ā", "ī", "ū", "ṝ", "e", "o", "ai", "au"]
# Все гласные (для закрытого слога)
VOWELS = set(LONG_VOWELS + ["a", "i", "u", "ṛ", "ḷ"])

def normalize(text: str) -> str:
    # удаляем danda (।, ॥) и цифры, нормализуем Unicode
    txt = re.sub(r"[।॥\d]", "", text)
    return unicodedata.normalize("NFC", txt.strip())

def split_syllables(txt: str) -> list[str]:
    # убираем пробелы
    s = re.sub(r"\s+", "", txt)
    # шаблон: кластер согл. + (дифтонг|гласная) + анусвара/висарга? + 0–2 согл.
    vowel_alts = "|".join(LONG_VOWELS + ["a", "i", "u", "ṛ", "ḷ"])
    pattern = rf"([{CONSONANTS}]*)" \
              rf"(?:{vowel_alts})" \
              rf"(?:ṃ|ḥ)?" \
              rf"[{CONSONANTS}]{{0,2}}"
    return re.findall(pattern, s)

def is_guru(syl: str) -> bool:
    if not syl:
        return False
    # долгий гласный или дифтонг
    for lv in LONG_VOWELS:
        if lv in syl:
            return True
    # анусвара/висарга
    if syl.endswith("ṃ") or syl.endswith("ḥ"):
        return True
    # закрытый слог — заканчивается на согласную
    if syl[-1] not in VOWELS:
        return True
    return False

def is_pathya(sylls: list[str]) -> bool:
    # Pathyā-anuṣṭubh: 3rd pāda 5th=laghu,6th=guru & 4th pāda 5,6 = guru
    if len(sylls) < 32:
        return False
    p3, p4 = sylls[16:24], sylls[24:32]
    return (not is_guru(p3[4]) and is_guru(p3[5])
         and  is_guru(p4[4]) and is_guru(p4[5]))

vipula_map = {
    "lglg": "Nagari", "lllg": "Bhavānī",
    "llgg": "Śārdūla", "glgg": "Āryā",
    "gglg": "Vidyunmālā"
}
def identify_vipula(half: list[str]) -> str:
    key = "".join("g" if is_guru(s) else "l" for s in half[:4])
    return vipula_map.get(key, "")

def detect_anuprasa(pada: list[str]) -> set[str]:
    # повтор инициала ≥3
    inits = [re.match(rf"[{CONSONANTS}]*", s).group(0) for s in pada]
    cnt = Counter(inits)
    return {c for c,n in cnt.items() if c and n >= 3}

def detect_yamaka(sylls: list[str]) -> set[tuple[int,int]]:
    coords = set()
    if line_length != 8 or len(sylls) < 32:
        return coords
    for a, b in [(0,2), (1,3)]:
        for i in range(8):
            x = sylls[a*8 + i]; y = sylls[b*8 + i]
            if x and x == y:
                coords |= {(a,i), (b,i)}
    return coords

# —————————————————————————————————————————————————————————————————————
# Основная визуализация
# —————————————————————————————————————————————————————————————————————
text = st.text_area("Вставьте IAST-текст ślok:", height=200)
if not text.strip():
    st.stop()

sylls = split_syllables(normalize(text))
blocks = [
    sylls[i : i + line_length*line_length]
    for i in range(0, len(sylls), line_length*line_length)
]

for bi, block in enumerate(blocks):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(0, line_length); ax.set_ylim(0, line_length)

    pathya = is_pathya(block) if show_pathya else False
    vip1 = identify_vipula(block[:line_length*2])
    vip2 = identify_vipula(block[line_length*2:line_length*4])
    yam_coords = detect_yamaka(block) if show_yam else set()

    for i in range(line_length):
        pada = block[i*line_length : (i+1)*line_length]
        anu_inits = detect_anuprasa(pada) if show_anu else set()
        for j in range(line_length):
            idx = i*line_length + j
            syl = block[idx] if idx < len(block) else ""
            guru = is_guru(syl)
            face = "black" if guru else "white"
            ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                   facecolor=face, edgecolor="gray"))
            ax.text(j+0.5, line_length-1-i+0.5, syl,
                    ha="center", va="center",
                    color="white" if guru else "black",
                    fontsize=8)

            # Vipulā highlight
            if show_vipula and j < 4:
                half_idx = 0 if i < (line_length*2)//line_length else 1
                label = vip1 if half_idx == 0 else vip2
                if label in selected_vip:
                    clr = "#FFA500" if half_idx == 0 else "#1E90FF"
                    ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                           facecolor=clr, alpha=0.4))

            # Anuprāsa border
            if show_anu:
                init = re.match(rf"[{CONSONANTS}]*", syl).group(0)
                if init in anu_inits:
                    ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                           fill=False, edgecolor="blue", linewidth=2))

            # Yamaka border
            if show_yam and (i, j) in yam_coords:
                ax.add_patch(Rectangle((j, line_length-1-i), 1, 1,
                                       fill=False, edgecolor="purple", linewidth=2))

    title = f"Block {bi+1}"
    if show_pathya and pathya:
        title += " — Pathyā-anuṣṭubh"
    ax.set_title(title, fontsize=10)
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
""")
st.markdown("---")
st.markdown("App by Svetlana Kreutzer 2025 ©")
