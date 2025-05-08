import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import re, unicodedata

# --- Фильтрация и транслитерация остались прежними ---

def normalize_iast(text):
    # удаляем данды и цифры
    text = re.sub(r'[।॥\d]', '', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def split_syllables(text):
    # упрощённый SLP1-режим или IAST, здесь IAST
    text = re.sub(r'\s+', '', text)
    pattern = r'([^aeiouāīūṛṝeoau]*[aeiouāīūṛṝeoau]+(?:ṃ|ḥ)?(?:[kgṅcjñṭḍṇtdnpbmyrlvśṣsh](?!h))?)'
    return re.findall(pattern, text)

def is_guru(syl):
    # по старым правилам
    ...

def identify_vipula(half):
    ...

def classify_anushtubh(syls):
    ...

# --- Жёсткое Anuprāsa: минимум 3 повторения инициала ---
def detect_strict_anuprasa(line):
    initials = [re.match(r'[^aeiouāīūṛṝeoau]*', syl).group(0) for syl in line]
    counts = {}
    for init in initials:
        counts[init] = counts.get(init, 0) + 1
    # берём только те иницииалы, что ≥3 раз
    return {init for init, c in counts.items() if init and c >= 3}

def detect_sloka_yamaka(all_syllables):
    # зеркальное повторение 1↔3 и 2↔4 pada
    yam = set()
    if len(all_syllables) >= 32:
        p1, p2, p3, p4 = (all_syllables[i:i+8] for i in (0,8,16,24))
        for idx in range(8):
            if p1[idx] == p3[idx]: yam.add( (0,idx) ); yam.add((2,idx))
            if p2[idx] == p4[idx]: yam.add( (1,idx) ); yam.add((3,idx))
    return yam

def visualize_block(syllables, show_vip, show_pathya, show_anu, show_yam):
    n = 8
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(0,n); ax.set_ylim(0,n)

    # классификация
    vip_labels = [identify_vipula(syllables[i*16:(i*16+4)]) for i in (0,1)]
    metre = classify_anushtubh(syllables)

    # yamaka-пары
    yam_positions = detect_sloka_yamaka(syllables) if show_yam else set()

    # строим линии
    lines = [syllables[i*8:(i+1)*8] for i in range(n)]
    for i, line in enumerate(lines):
        row = n-1-i
        # строгий anuprasa
        anu_inits = detect_strict_anuprasa(line) if show_anu else set()

        for j in range(n):
            x,y = j, row
            # базовый цвет
            syl = line[j] if j < len(line) else ''
            guru = is_guru(syl)
            face = 'black' if guru else 'white'
            ax.add_patch(Rectangle((x,y),1,1,facecolor=face,edgecolor='gray'))

            # рисуем слог
            col = 'white' if guru else 'black'
            ax.text(x+0.5, y+0.5, syl, ha='center', va='center', color=col, fontsize=8)

            # Vipula-фон поверх
            if show_vip and ((i in (0,2)) and j<4):
                color = vipula_color_map[vip_labels[i//2]]
                ax.add_patch(Rectangle((x,y),1,1,facecolor=color,alpha=0.6))

            # Anuprasa-рамка
            init = re.match(r'[^aeiouāīūṛṝeoau]*', syl).group(0)
            if show_anu and init in anu_inits:
                ax.add_patch(Rectangle((x,y),1,1,fill=False,edgecolor='blue',linewidth=2))

            # Yamaka-точка
            if show_yam and (i,j) in yam_positions:
                ax.add_patch(Circle((x+0.8,y+0.2),0.1,color='purple'))

    # заголовок
    title = f"Meter: {metre}"
    ax.set_title(title, fontsize=10)

    st.pyplot(fig)

# --- Streamlit-интерфейс ---
st.sidebar.title("Настройки отображения")
show_vip    = st.sidebar.checkbox("Показать Vipula", True)
show_pathya = st.sidebar.checkbox("Показать только Pathyā-anuṣṭubh", False)
show_anu    = st.sidebar.checkbox("Показать Anuprāsa", False)
show_yam    = st.sidebar.checkbox("Показать Yamaka", False)

text = st.text_area("Вставьте IAST-текст шлок", height=200)
if text:
    txt = normalize_iast(text)
    syls = split_syllables(txt)
    visualize_block(syls, show_vip, show_pathya, show_anu, show_yam)
