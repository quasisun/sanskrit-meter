import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import re, unicodedata
from collections import Counter, defaultdict

# —————————————————————————————————————————————————————————————————————
# 1. Инструкции
# —————————————————————————————————————————————————————————————————————

st.title("Sanskrit Śloka Visualizer")
st.markdown("""
**Инструкция по использованию**  
1. Вставьте текст ślok в поле ниже в **IAST** (без `।`, `॥` и цифр).  
2. В сайдбаре выберите опции визуализации:  
   - **Guru/Laghu** (основа метрического разбора),  
   - **Vipulā** (Nagari, Bhavānī, Śārdūla, Āryā, Vidyunmālā),  
   - **Anuprāsa** (lāṭānuprāsa, chekānuprāsa, vṛttyānuprāsa, antyānuprāsa-pāda, antyānuprāsa-śloka, śṛtyānuprāsa-dantya),  
   - **Yamaka** (pādānta, kāñci, samudga, vikrānta, cakravāla, sandaṣṭa, pādādi, āmreḍita, caturvyavasita, mālāyamaka).  
3. После нажатия Enter приложение покажет график 8×8 для первой śloka (32 слога) и легенду.  
""")

# —————————————————————————————————————————————————————————————————————
# 2. Sidebar: опции Anuprāsa и Yamaka
# —————————————————————————————————————————————————————————————————————

st.sidebar.header("Anuprāsa vidhīni (आलङ्काराः)")
lata_opt   = st.sidebar.checkbox("lāṭānuprāsa", False)
cheka_opt  = st.sidebar.checkbox("chekānuprāsa", False)
vrtty_opt  = st.sidebar.checkbox("vṛttyānuprāsa", False)
antyp_opt  = st.sidebar.checkbox("antyānuprāsa-pāda", False)
antys_opt  = st.sidebar.checkbox("antyānuprāsa-śloka", False)
srtyd_opt  = st.sidebar.checkbox("śṛtyānuprāsa-dantya", False)

st.sidebar.header("Yamaka vidhīni (यमकाः)")
flag_padaanta      = st.sidebar.checkbox("pādānta yamaka", False)
flag_padadi        = st.sidebar.checkbox("pādādi yamaka", False)
flag_samudga       = st.sidebar.checkbox("samudga yamaka", False)
flag_vikranta      = st.sidebar.checkbox("vikrānta yamaka", False)
flag_cakravala     = st.sidebar.checkbox("cakravāla yamaka", False)
flag_sandashta     = st.sidebar.checkbox("sandaṣṭa yamaka", False)
flag_padadi2       = st.sidebar.checkbox("pādādi yamaka (alt)", False)
flag_amredita      = st.sidebar.checkbox("āmreḍita yamaka", False)
flag_caturvyav     = st.sidebar.checkbox("caturvyavasita yamaka", False)
flag_malayamaka    = st.sidebar.checkbox("mālāyamaka", False)

# —————————————————————————————————————————————————————————————————————
# 3. Утилиты для метрика и звуковых украшений
# —————————————————————————————————————————————————————————————————————

def normalize_iast(text: str) -> str:
    # удаляем данды, цифры и нормализуем Unicode
    text = re.sub(r'[।॥\d]', '', text)
    return unicodedata.normalize('NFC', text.strip())

def split_syllables(text: str) -> list[str]:
    # разбиваем на слоги в IAST
    text = re.sub(r'\s+', '', text)
    pattern = r'([^aeiouāīūṛṝeoau]*[aeiouāīūṛṝeoau]+(?:ṃ|ḥ)?(?:[kgṅcjñṭḍṇtdnpbmyrlvśṣsh](?!h))?)'
    return re.findall(pattern, text)

def is_guru(syl: str) -> bool:
    # долгий гласный, анусвара/висарга или короткий+кластер ≥2
    if not syl:
        return False
    if re.search(r'[āīūṛṝeoau]', syl):
        return True
    if re.search(r'[ṃḥ]', syl):
        return True
    if re.search(r'[aeiou][^aeiou]{2,}', syl):
        return True
    return False

def get_padas(sylls: list[str]) -> list[list[str]]:
    # делим на четыре pāda по 8 слогов
    return [sylls[i*8:(i+1)*8] for i in range(4) if len(sylls[i*8:(i+1)*8])==8]

def identify_vipula(half: list[str]) -> str:
    pattern = ''.join('g' if is_guru(s) else 'l' for s in half[:4])
    vip = {
        'lglg':'Nagari','lllg':'Bhavānī','llgg':'Śārdūla',
        'glgg':'Āryā','gglg':'Vidyunmālā'
    }
    return vip.get(pattern, '')

def classify_anushtubh(sylls: list[str]) -> str:
    # Pathyā-anuṣṭubh: 3rd pāda (5th laghu, 6th guru), 4th pāda (5th guru,6th guru)
    pads = get_padas(sylls)
    if len(pads)==4:
        p3, p4 = pads[2], pads[3]
        if (not is_guru(p3[4])) and is_guru(p3[5]) and is_guru(p4[4]) and is_guru(p4[5]):
            return 'Pathyā-anuṣṭubh'
    return ''

def get_initial(syl: str) -> str:
    m = re.match(r'[^aeiouāīūṛṝeoau]+', syl)
    return m.group(0) if m else ''

def get_final(syl: str) -> str:
    m = re.search(r'[^aeiouāīūṛṝeoau]+$', syl)
    return m.group(0) if m else ''

# Anuprāsa detectors
def detect_lata(s: list[str]) -> bool:
    pads = get_padas(s)
    return any(p for p in pads) and all(get_initial(syl)==get_initial(pads[0][0]) for syl in pads[0])

def detect_cheka(s: list[str]) -> bool:
    pads = get_padas(s)
    inits = [get_initial(p[0]) for p in pads]
    return len(set(inits))==1 and inits[0] != ''

def detect_vrtty(s: list[str]) -> bool:
    half = s[:16]
    cnt = Counter(get_initial(x) for x in half)
    return any(c>=3 and init!='' for init,c in cnt.items())

def detect_antya_pada(s: list[str]) -> bool:
    pads = get_padas(s)
    return any(len(set(get_final(x) for x in p))==1 for p in pads)

def detect_antya_sloka(s: list[str]) -> bool:
    block = s[:32]
    fins = [get_final(x) for x in block]
    return len(fins)==32 and len(set(fins))==1 and fins[0] != ''

def detect_srtya_dantya(s: list[str]) -> bool:
    pads = get_padas(s)
    if len(pads)>=2:
        return get_final(pads[0][-1])==get_initial(pads[1][0])!=''
    return False

# Yamaka detectors
def padaanta_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and len({p[-1] for p in pads})==1

def padadi_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and len({p[0] for p in pads})==1

def samudga_yamaka(s: list[str]) -> bool:
    return s[:16]==s[16:32]

def vikranta_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and pads[0]==pads[2] and pads[1]==pads[3]

def cakravala_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and all(pads[i][-1]==pads[i+1][0] for i in range(3))

def sandasta_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and len({tuple(p[:2]) for p in pads})==1

def amredita_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and len({tuple(p[-2:]) for p in pads})==1

def caturvyavasita_yamaka(s: list[str]) -> bool:
    pads = get_padas(s)
    return len(pads)==4 and all(p==pads[0] for p in pads)

def malayamaka(s: list[str]) -> bool:
    buckets = defaultdict(set)
    for syl in s:
        m = re.match(r'([^aeiouāīūṛṝeoau]+)([aeiouāīūṛṝeoau]+)', syl)
        if m:
            c,v = m.groups()
            buckets[c].add(v)
    return any(len(vs)>1 for vs in buckets.values())

# —————————————————————————————————————————————————————————————————————
# 4. Основной блок визуализации
# —————————————————————————————————————————————————————————————————————

text = st.text_area("IAST śloka text (4×8 sloka)", height=180)
if text:
    txt = normalize_iast(text)
    sylls = split_syllables(txt)
    pads = get_padas(sylls)

    # готовим detektоры
    anups = {
      'lāṭānuprāsa': (lata_opt,   detect_lata(sylls)),
      'chekānuprāsa':(cheka_opt,  detect_cheka(sylls)),
      'vṛttyānuprāsa':(vrtty_opt, detect_vrtty(sylls)),
      'antyānuprāsa-pāda':(antyp_opt, detect_antya_pada(sylls)),
      'antyānuprāsa-śloka':(antys_opt, detect_antya_sloka(sylls)),
      'śṛtyānuprāsa-dantya':(srtyd_opt, detect_srtya_dantya(sylls)),
    }
    yams = {
      'pādānta':(flag_padaanta, padaanta_yamaka(sylls)),
      'pādādi': (flag_padadi,   padadi_yamaka(sylls)),
      'samudga':(flag_samudga, samudga_yamaka(sylls)),
      'vikrānta':(flag_vikranta, vikranta_yamaka(sylls)),
      'cakravāla':(flag_cakravala, cakravala_yamaka(sylls)),
      'sandaṣṭa':(flag_sandashta, sandasta_yamaka(sylls)),
      'pādādi₂':(flag_padadi2, padadi_yamaka(sylls)),
      'āmreḍita':(flag_amredita, amredita_yamaka(sylls)),
      'caturvyavasita':(flag_caturvyav, caturvyavasita_yamaka(sylls)),
      'mālāyamaka':(flag_malayamaka, malayamaka(sylls)),
    }

    # визуализация Guru/Laghu
    fig, ax = plt.subplots(figsize=(4,4))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(0,8); ax.set_ylim(0,8)
    for i in range(8):
        for j in range(8):
            idx = i*8+j
            syl = sylls[idx] if idx < len(sylls) else ''
            face = 'black' if is_guru(syl) else 'white'
            ax.add_patch(Rectangle((j,7-i),1,1,facecolor=face,edgecolor='gray'))
            ax.text(j+0.5,7-i+0.5,syl, ha='center', va='center',
                    color='white' if face=='black' else 'black', fontsize=8)

    # фон Anuprāsa сверху
    for name,(enabled,det) in anups.items():
        if enabled and det:
            ax.add_patch(Rectangle((0,0),8,8,facecolor='orange',alpha=0.3))

    # фон Yamaka сверху
    for name,(enabled,det) in yams.items():
        if enabled and det:
            ax.add_patch(Rectangle((0,0),8,8,facecolor='yellow',alpha=0.3))

    st.pyplot(fig)

    # —————————————————————————————————————————————————————————————————————
    # 5. Легенда
    # —————————————————————————————————————————————————————————————————————
    st.markdown("**Legend:**")
    st.markdown("- **Guru** = чорна клітинка; **Laghu** = біла клітинка")
    st.markdown("- **Vipulā**: Nagari, Bhavānī, Śārdūla, Āryā, Vidyunmālā (синий фон)")
    st.markdown("- **Pathyā-anuṣṭubh** = строгий метр (зелёная рамка)")
    st.markdown("- **Anuprāsa** (lāṭā, chekā, vṛttyā, antyā-pāda, antyā-śloka, śṛtyā-dantya) (оранжевый фон)")
    st.markdown("- **Yamaka** (pādānta, pādādi, samudga, vikrānta, cakravāla, sandaṣṭa, āmreḍita, caturvyavasita, mālāyamaka) (жёлтый фон)")
    # —————————————————————————————————————————————————————————————————————
    # 6. Авторство внизу
    # —————————————————————————————————————————————————————————————————————
    st.markdown("---")
    st.markdown("App by Svetlana Kreutzer 2025 ©")
