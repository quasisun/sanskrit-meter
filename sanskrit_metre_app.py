import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import re
import unicodedata
from typing import List, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Преобразование IAST → SLP1 =====
def normalize(text: str) -> str:
    t = unicodedata.normalize('NFC', text.strip())
    t = re.sub(r'[।॥|\d]', '', t)
    return transliterate(t, sanscript.IAST, sanscript.SLP1)

# ===== Сегментация на слоги =====
def split_syllables_slp1(text: str) -> List[str]:
    s = re.sub(r"\s+", "", text)
    vowels = set('aAiIuUfFxXeEoO')
    n, out, i = len(s), [], 0
    while i < n:
        j = i
        while j < n and s[j] not in vowels: j += 1
        if j >= n: break
        k = j + 1
        if k < n and s[k] in 'MH': k += 1
        c = k
        while c < n and s[c] not in vowels: c += 1
        cut = c if c - k <= 1 else k + 1
        out.append(s[i:cut]); i = cut
    if i < n:
        if out: out[-1] += s[i:]
        else: out = [s[i:]]
    return out

# ===== Guru / Laghu =====
long_v = set('AIUFXeEoO')

def is_guru(s: str) -> bool:
    m = re.match(r'^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$', s)
    if not m: return False
    _, v, nas, aft = m.groups()
    return v in long_v or nas or len(aft) >= 2

# ===== Vipula =====
vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}

def identify_vipula(syls: List[str]) -> Optional[str]:
    if len(syls) < 4: return None
    pat = ''.join('g' if is_guru(s) else 'l' for s in syls[:4])
    return {
        'lglg': 'Nagari', 'lllg': 'Bhavani',
        'llgg': 'Shardula', 'glgg': 'Arya', 'gglg': 'Vidyunmala'
    }.get(pat)

# ===== Метрики =====
def classify_pathya(block: List[str]) -> bool:
    return len(block) >= 32 and not is_guru(block[20]) and is_guru(block[21]) and is_guru(block[28]) and is_guru(block[29])

def detect_padayadi_yamaka(b: List[str]) -> bool:
    return len(b) >= 32 and len({b[i*8] for i in range(4)}) == 1

def detect_padaanta_yamaka(b: List[str]) -> bool:
    return len(b) >= 32 and len({b[i*8+7] for i in range(4)}) == 1

def detect_vrttyanuprasa(line: List[str]) -> bool:
    if len(line) < 7: return False
    ons = [re.match(r'^([^aAiIuUfFxXeEoO]+)', s).group(1) if re.match(r'^([^aAiIuUfFxXeEoO]+)', s) else '' for s in line[4:7]]
    return len(set(ons)) == 1 and ons[0]

# ===== Визуализация =====

def visualize_lines(lines: List[List[str]]):
    rows = len(lines); cols = max(map(len, lines)) if rows else 0
    if not rows or not cols:
        st.error('Нет данных'); return
    disp = [[transliterate(s, sanscript.SLP1, sanscript.IAST) for s in r] for r in lines]
    flat = [s for r in lines for s in r]

    fig, ax = plt.subplots(figsize=(cols/8*6, rows/8*6))
    ax.set(xlim=(0, cols), ylim=(0, rows)); ax.axis('off'); ax.set_aspect('equal')

    # клетки + текст
    for r,row in enumerate(lines):
        y = rows-1-r
        for c,syl in enumerate(row):
            guru = is_guru(syl)
            ax.add_patch(Rectangle((c,y),1,1,facecolor='black' if guru else 'white', edgecolor='gray', zorder=1))
            ax.text(c+0.5,y+0.5,disp[r][c],ha='center',va='center',color='white' if guru else 'black',fontsize=10,zorder=2)

    # vipula fill, anuprāsa border
    for r,row in enumerate(lines):
        y = rows-1-r
        vip = identify_vipula(row)
        if vip:
            ax.add_patch(Rectangle((0,y),min(4,len(row)),1,facecolor=vipula_colors[vip],alpha=0.35,zorder=3))
        if detect_vrttyanuprasa(row):
            ax.add_patch(Rectangle((0,y),len(row),1,fill=False,edgecolor='purple',linewidth=2,zorder=4))

    # śloka‑level borders
    for i in range(0,len(flat),32):
        blk = flat[i:i+32]
        if len(blk)<32: break
        r_base = i//cols; yb = rows-1-r_base-1
        if yb<0: continue
        w = min(cols,8)
        if classify_pathya(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='blue',lw=2.5,zorder=5))
        if detect_padayadi_yamaka(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='green',lw=2,linestyle='--',zorder=5))
        if detect_padaanta_yamaka(blk):
            ax.add_patch(Rectangle((0,yb),w,2,fill=False,edgecolor='red',lw=2,linestyle=':',zorder=5))

    # легенда справа
    patches=[Patch(facecolor='black',label='Guru'),Patch(facecolor='white',label='Laghu')]
    for n,c in vipula_colors.items(): patches.append(Patch(facecolor=c,alpha=0.35,label=f'Vipula {n}'))
    patches+= [Patch(edgecolor='purple',facecolor='none',lw=2,label='Vṛtti Anuprāsa'),
               Patch(edgecolor='blue',facecolor='none',lw=2.5,label='Pathya'),
               Patch(edgecolor='green',facecolor='none',lw=2,linestyle='--',label='Pāda‑ādi Yamaka'),
               Patch(edgecolor='red',facecolor='none',lw=2,linestyle=':',label='Pāda‑anta Yamaka')]
    ax.legend(handles=patches,loc='center left',bbox_to_anchor=(1.02,0.5),fontsize=10)
    st.pyplot(fig)
    plt.close(fig)

# ===== UI =====
st.title('Sloka Meter Visualizer')
text=st.text_area('Введите IAST‑текст, строки через danda (। или ॥):',height=200)
if st.button('Показать'):
    parts=[p.strip() for p in re.split(r'[।॥|]+',text) if p.strip()]
    if not parts:
        st.error('Нет строк');
    else:
        lines=[split_syllables_slp1(normalize(p)) for p in parts]
        visualize_lines(lines)
