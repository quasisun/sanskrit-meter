import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
import re, unicodedata
from collections import Counter

# --- УТИЛИТЫ ---
def normalize_iast(text):
    # Убираем данды и цифры, нормализуем Unicode
    text = re.sub(r'[।॥\d]', '', text)
    return unicodedata.normalize('NFC', text).strip()

def split_syllables(text):
    # Упрощённое, но надёжное разбиение на санскритские слоги в IAST
    # (начальные согласные) + гласная+ возможный знак + одна согл.
    text = re.sub(r'\s+', '', text)
    pat = r'([^aeiouāīūṛṝeoau]*[aeiouāīūṛṝeoau]+(?:ṃ|ḥ)?(?:[kgṅcjñṭḍṇtdnpbmyrlvśṣsh](?!h))?)'
    return [s for s in re.findall(pat, text) if s]

def is_guru(syl):
    # Нормализованный слог без пробелов
    m = re.match(r'^([^aeiouāīūṛṝeoau]*)([aeiouāīūṛṝeoau]+)(ṃ|ḥ)?(.*)$', syl)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    long_v = set(['ā','ī','ū','ṝ','e','ai','o','au'])
    # долгий гласный
    if vowel in long_v:
        return True
    # анусвара/висарга
    if nasal:
        return True
    # кластер из ≥2 согл. после краткого гласного
    if re.match(r'^[^aeiouāīūṛṝeoau]{2,}', after):
        return True
    return False

def identify_vipula(half):
    # Первая половина śloka: список из 16 слогов
    seq = ''.join('g' if is_guru(s) else 'l' for s in half[:4])
    return {
        'lglg':'Nāgarī',
        'lllg':'Bhavānī',
        'llgg':'Śārdūla',
        'glgg':'Āryā',
        'gglg':'Vidyunmālā',
    }.get(seq, None)

def classify_anushtubh(syllables):
    # Только для 32-слоговой śloka
    if len(syllables) < 32:
        return None
    p3 = syllables[16:24]
    p4 = syllables[24:32]
    # 3-я pada: 5-й laghu, 6-й guru
    cond3 = (not is_guru(p3[4])) and is_guru(p3[5])
    # 4-я pada: 5-й и 6-й guru
    cond4 = is_guru(p4[4]) and is_guru(p4[5])
    return 'Pathyā-anuṣṭubh' if (cond3 and cond4) else None

# --- Anuprāsa TYPES ---
def get_initial(syl):
    m = re.match(r'[^aeiouāīūṛṝeoau]+', syl)
    return m.group(0) if m else ''

def get_final(syl):
    m = re.search(r'[^aeiouāīūṛṝeoau]+$', syl)
    return m.group(0) if m else ''

def detect_lata(block):
    # lāṭānuprāsa: все initial в śloka одинаковы
    inits = [get_initial(s) for s in block[:32]]
    inits = [i for i in inits if i]
    return len(inits)>0 and len(set(inits))==1

def detect_cheka(block):
    # chekānuprāsa: одинаковое initial в каждой pada
    inits = []
    for k in (0,8,16,24):
        pad = [get_initial(s) for s in block[k:k+8]]
        pad = [i for i in pad if i]
        if not pad:
            return False
        inits.append(pad[0])
    return len(set(inits))==1

def detect_vrtty(block):
    # vṛttyānuprāsa: initial первых 16 слогов повторяется минимум 3 раза
    inits = [get_initial(s) for s in block[:16] if get_initial(s)]
    cnt = Counter(inits)
    return any(c>=3 for c in cnt.values())

def detect_antya_pada(block):
    # antyānuprāsa pada: в каком-то pada все final одинаковы
    for k in (0,8,16,24):
        finals = [get_final(s) for s in block[k:k+8] if get_final(s)]
        if finals and len(set(finals))==1:
            return True
    return False

def detect_antya_sloka(block):
    # antyānuprāsa śloka: все final в śloka одинаковы
    finals = [get_final(s) for s in block[:32] if get_final(s)]
    return finals and len(set(finals))==1

def detect_srtya_dantya(block):
    # śṛtyānuprāsa dantya: final pada1 == initial pada2
    if len(block)>=16:
        f = get_final(block[7])
        i = get_initial(block[8])
        return f and i and (f==i)
    return False

# --- Sloka-Yamaka (зеркальное) ---
def detect_yamaka(block):
    pairs = set()
    if len(block) < 32:
        return pairs
    p1 = block[0:8]; p2 = block[8:16]; p3 = block[16:24]; p4 = block[24:32]
    for idx in range(8):
        if p1[idx]==p3[idx]:
            pairs.add((0,idx)); pairs.add((2,idx))
        if p2[idx]==p4[idx]:
            pairs.add((1,idx)); pairs.add((3,idx))
    return pairs

# --- Цвета ---
VIP_COLORS = {
    'Nāgarī':'#FFA500', 'Bhavānī':'#1E90FF', 'Śārdūla':'#32CD32',
    'Āryā':'#FF4500','Vidyunmālā':'#9932CC'
}
ANU_COLORS = {
    'lāṭānuprāsa':'#DAA520', 'chekānuprāsa':'#4682B4', 'vṛttyānuprāsa':'#32CD32',
    'antyānuprāsa pada':'#FF4500','antyānuprāsa śloka':'#9932CC','śṛtyānuprāsa dantya':'#FF69B4'
}

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.title("Настройки отображения")
grid_size = st.sidebar.selectbox("Grid size (слогов в строке)", [8,16,32], index=0)
show_pathya = st.sidebar.checkbox("Highlight Pathyā-anuṣṭubh", True)
vipula_choices = st.sidebar.multiselect("Vipula to show", list(VIP_COLORS.keys()), default=list(VIP_COLORS.keys()))
anuprasa_choices = st.sidebar.multiselect("Anuprāsa to show", list(ANU_COLORS.keys()), default=[])
show_yam = st.sidebar.checkbox("Show Śloka-Yamaka", False)

text = st.text_area("Вставьте IAST-текст шлок", height=200)
if not text.strip():
    st.warning("Пожалуйста, введите текст.")
    st.stop()

# --- Подготовка слогов и блоков ---
txt = normalize_iast(text)
sylls = split_syllables(txt)
block_size = grid_size * grid_size
blocks = [sylls[i:i+block_size] for i in range(0, len(sylls), block_size)]

for bi, block in enumerate(blocks):
    # Classification
    vip_labels = []
    if len(block) >= 32:
        vip_labels = [identify_vipula(block[0:16]), identify_vipula(block[16:32])]
    pathya = classify_anushtubh(block)

    # Создаём фигуру
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(0, grid_size); ax.set_ylim(0, grid_size)
    ax.set_aspect('equal')

    # Если выделяем Pathyā-anuṣṭubh рамкой всего блока
    if show_pathya and pathya=='Pathyā-anuṣṭubh':
        ax.add_patch(Rectangle((0,0), grid_size, grid_size, fill=False, edgecolor='red', linewidth=3))

    # Yamaka-позиции
    yam_positions = detect_yamaka(block) if show_yam else set()

    # Рисуем клетки
    for i in range(grid_size):
        for j in range(grid_size):
            idx = i*grid_size + j
            x, y = j, grid_size-1-i
            syl = block[idx] if idx < len(block) else ''
            guru = is_guru(syl)
            face = 'black' if guru else 'white'
            ax.add_patch(Rectangle((x,y),1,1,facecolor=face,edgecolor='gray'))

            # текст слога
            if syl:
                color = 'white' if guru else 'black'
                ax.text(x+0.5, y+0.5, syl, ha='center', va='center', color=color, fontsize=8)

    # Наложение Vipula (поверх)
    # Випулы первые 4 ячейки каждой половины śloka (только для grid_size>=8)
    if grid_size>=8:
        for half_index, label in enumerate(vip_labels):
            if label and label in vipula_choices:
                rows = [grid_size-1, grid_size-1-2] if half_index==0 else [grid_size-1-4, grid_size-1-6]
                for r in rows:
                    for c in range(4):
                        ax.add_patch(Rectangle((c,r),1,1,facecolor=VIP_COLORS[label],alpha=0.5))

    # Наложение Anuprāsa
    # Только для первой śloka в блоке
    if block and any(anuprasa_choices):
        for name, fn in [
            ('lāṭānuprāsa', detect_lata),
            ('chekānuprāsa', detect_cheka),
            ('vṛttyānuprāsa', detect_vrtty),
            ('antyānuprāsa pada', detect_antya_pada),
            ('antyānuprāsa śloka', detect_antya_sloka),
            ('śṛtyānuprāsa dantya', detect_srtya_dantya),
        ]:
            if name in anuprasa_choices and fn(block):
                ax.add_patch(Rectangle((0,0),grid_size,grid_size,
                                       facecolor=ANU_COLORS[name],alpha=0.4))

    # Наложение Yamaka
    for (pi, pj) in yam_positions:
        # pi = pada index 0..3, pj = pos in pada 0..7
        gi = pi*8 + pj
        bx = pj; by = grid_size-1 - pi*8/ (grid_size/8) - int(pi*8/ (grid_size/8))
        # simplify: for grid_size 8 use by=grid_size-1-pi
        if grid_size==8:
            by = grid_size-1 - pi
        ax.add_patch(Circle((bx+0.8, by+0.2),0.1,color='purple'))

    # Заголовок и легенда
    ax.set_title(f"Block {bi+1} — {pathya or 'Non-Pathyā'}", fontsize=12)
    legend_elems = [
        Patch(facecolor='black',edgecolor='gray',label='Guru'),
        Patch(facecolor='white',edgecolor='gray',label='Laghu')
    ]
    for label,color in VIP_COLORS.items():
        if label in vipula_choices:
            legend_elems.append(Patch(facecolor=color,alpha=0.5,label=f'Vipula {label}'))
    for name,color in ANU_COLORS.items():
        if name in anuprasa_choices:
            legend_elems.append(Patch(facecolor=color,alpha=0.4,label=name))
    if show_pathya:
        legend_elems.append(Patch(facecolor='none',edgecolor='red',label='Pathyā-anuṣṭubh',linewidth=3))
    if show_yam:
        legend_elems.append(Patch(facecolor='purple',label='Yamaka'))
    ax.legend(handles=legend_elems, bbox_to_anchor=(1.05,1), loc='upper left', borderaxespad=0.,fontsize=8)

    st.pyplot(fig)
