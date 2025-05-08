import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import re, unicodedata

# --- Нормализация и сегментация в слоги (IAST) ---
def normalize_iast(text):
    text = re.sub(r'[।॥\d]', '', text)
    return unicodedata.normalize('NFC', text.strip())

def split_syllables(text):
    text = re.sub(r'\s+', '', text)
    pat = r'([^aeiouāīūṛṝeoau]*[aeiouāīūṛṝeoau]+(?:ṃ|ḥ)?(?:[kgṅcjñṭḍṇtdnpbmyrlvśṣsh](?!h))?)'
    return re.findall(pat, text)

# --- Функция для разбивки на 4 pāda (по 8 слогов) ---
def get_padas(sylls):
    pads = []
    for i in range(4):
        chunk = sylls[i*8:(i+1)*8]
        if len(chunk)==8:
            pads.append(chunk)
    return pads

# --- Детекторы yamaka-типов ---
def padaanta_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    last = [p[-1] for p in pads]
    return len(set(last))==1

def padadi_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    first = [p[0] for p in pads]
    return len(set(first))==1

def vikranta_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    return pads[0]==pads[2] and pads[1]==pads[3]

def cakravala_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    # last of pad i == first of pad i+1
    for i in range(3):
        if pads[i][-1] != pads[i+1][0]:
            return False
    return True

def samudga_yamaka(sylls):
    # первая половина śloka (16 слогов) повторяется
    return sylls[:16] == sylls[16:32]

def sandasta_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    # первые 2 слога каждого pāda совпадают
    first2 = [tuple(p[:2]) for p in pads]
    return len(set(first2))==1

def amredita_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    # последние 2 слога каждого pāda совпадают
    last2 = [tuple(p[-2:]) for p in pads]
    return len(set(last2))==1

def caturvyavasita_yamaka(sylls):
    pads = get_padas(sylls)
    if len(pads)<4: return False
    # все pāda полностью совпадают
    return all(p==pads[0] for p in pads)

def pancavarna_malayamaka(sylls):
    # mālayamaka: один и тот же согласный с разными гласными в начале слогов
    # находим все инициалы, группируем по consonant skeleton
    inits = [re.match(r'[^aeiouāīūṛṝeoau]+', s).group(0) for s in sylls if s]
    from collections import defaultdict
    buckets = defaultdict(set)
    for s in sylls:
        m = re.match(r'([^aeiouāīūṛṝeoau]+)([aeiouāīūṛṝeoau]+)', s)
        if m:
            cons, vow = m.groups()
            buckets[cons].add(vow)
    # если для какого-то consonant >1 гласных — признак
    return any(len(vs)>1 and cons!='' for cons, vs in buckets.items())

# --- Streamlit UI: yamaka types ---
st.sidebar.header("Yamaka types")
flags = {
    'pādānta': st.sidebar.checkbox("Pādānta", False),
    'pādādi': st.sidebar.checkbox("Pādādi", False),
    'vikrānta': st.sidebar.checkbox("Vikrānta", False),
    'cakravāla': st.sidebar.checkbox("Cakravāla", False),
    'samudga': st.sidebar.checkbox("Samudga", False),
    'sandaṣṭa': st.sidebar.checkbox("Sandaṣṭa", False),
    'pādādi2': st.sidebar.checkbox("Pādādi (alt)", False),  # same as pādādi
    'āmreḍita': st.sidebar.checkbox("Āmreḍita", False),
    'caturvyavasita': st.sidebar.checkbox("Caturvyavasita", False),
    'mālayamaka': st.sidebar.checkbox("Mālāyamaka", False),
}

text = st.text_area("Вставьте IAST-текст (4 pāda по 8 слогов)", height=200)
if text:
    txt = normalize_iast(text)
    sylls = split_syllables(txt)

    # запускаем детекторы
    dm = {
      'pādānta': padaanta_yamaka(sylls),
      'pādādi': padadi_yamaka(sylls),
      'vikrānta': vikranta_yamaka(sylls),
      'cakravāla': cakravala_yamaka(sylls),
      'samudga': samudga_yamaka(sylls),
      'sandaṣṭa': sandasta_yamaka(sylls),
      'āmreḍita': amredita_yamaka(sylls),
      'caturvyavasita': caturvyavasita_yamaka(sylls),
      'mālayamaka': pancavarna_malayamaka(sylls),
    }

    # визуализация одной śloka: 8×8
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([])
    # рисуем гуру/лакху
    for i in range(8):
        row = 7 - i
        for j in range(8):
            s = sylls[i*8+j] if i*8+j < len(sylls) else ''
            guru = bool(re.search(r'[āīūṛṝeoau]|ṃ|ḥ|[aeiou][^aeiou]{2,}', s))
            color = 'black' if guru else 'white'
            ax.add_patch(Rectangle((j,row),1,1,facecolor=color,edgecolor='gray'))
    # подсветка yamaka фоном
    for name, active in flags.items():
        if active and dm.get(name,False):
            ax.add_patch(Rectangle((0,0),8,8,facecolor='yellow',alpha=0.3))

    st.pyplot(fig)
    # показываем, какие yamaka найдены
    st.write({k:v for k,v in dm.items() if v})
