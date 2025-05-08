import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch, Circle
import re
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ===== Настройки цветов =====
vipula_colors = {
    'Nagari': '#FF7F00',
    'Bhavani': '#1E3F66',
    'Shardula': '#2E8B57',
    'Arya': '#8B0000',
    'Vidyunmala': '#9932CC'
}
pathya_color = '#4682B4'  # для подсветки Pathyā-anuṣṭubh

def normalize(text):
    """Конвертация IAST → SLP1"""
    return transliterate(text.strip(), sanscript.IAST, sanscript.SLP1)

def split_syllables_slp1(text):
    pattern = r"""
        ([^aAiIuUfFxXeEoOMH]*
         [aAiIuUfFxXeEoO]
         [MH]?
         [^aAiIuUfFxXeEoOMH]?)
    """
    return [s for s in re.findall(pattern, text, re.VERBOSE) if s]

def is_guru_syllable_slp1(syl):
    m = re.match(r"^([^aAiIuUfFxXeEoOMH]*)([aAiIuUfFxXeEoO])([MH]?)(.*)$", syl)
    if not m:
        return False
    _, vowel, nasal, after = m.groups()
    if vowel in ['A','I','U','F','X','e','E','o','O']:
        return True
    if nasal:
        return True
    if len(after) >= 2:
        return True
    return False

def identify_vipula(first4):
    pattern = ''.join('g' if is_guru_syllable_slp1(s) else 'l' for s in first4)
    mapping = {'lglg':'Nagari','lllg':'Bhavani','llgg':'Shardula','glgg':'Arya','gglg':'Vidyunmala'}
    return mapping.get(pattern)

def classify_anushtubh(syllables):
    if len(syllables) < 32:
        return False
    p3, p4 = syllables[16:24], syllables[24:32]
    if len(p3)<6 or len(p4)<6:
        return False
    l3_5 = is_guru_syllable_slp1(p3[4]); l3_6 = is_guru_syllable_slp1(p3[5])
    l4_5 = is_guru_syllable_slp1(p4[4]); l4_6 = is_guru_syllable_slp1(p4[5])
    return (not l3_5) and l3_6 and l4_5 and l4_6

def detect_anuprasa(line):
    initials = [re.match(r'[^\W\d_]*',s).group(0) for s in line]
    return {s for s in initials if initials.count(s)>1}

def detect_sloka_yamaka(syllables):
    marks=[]
    if len(syllables)>=32:
        p1, p2 = syllables[0:8], syllables[8:16]
        p3, p4 = syllables[16:24], syllables[24:32]
        for i in range(8):
            if p1[i]==p3[i]: marks.append((0,i)); marks.append((2,i))
            if p2[i]==p4[i]: marks.append((1,i)); marks.append((3,i))
    return marks

def visualize_grid(slp1_sylls, iast_sylls, line_len, vipula_sel, show_pathya, show_anuprasa, show_yamaka):
    fig,ax=plt.subplots(figsize=(6,6))
    ax.set_xlim(0,line_len); ax.set_ylim(0,line_len)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal')

    # Guru/Laghu
    rows=[slp1_sylls[i:i+line_len] for i in range(0,len(slp1_sylls),line_len)]
    for i in range(line_len):
        row=rows[i] if i<len(rows) else []
        for j in range(line_len):
            col='black' if j<len(row) and is_guru_syllable_slp1(row[j]) else 'white'
            ax.add_patch(Rectangle((j,line_len-1-i),1,1,facecolor=col,edgecolor='black'))

    # Vipula
    for sh in range(0,len(slp1_sylls),32):
        if sh+32<=len(slp1_sylls):
            vip1=identify_vipula(slp1_sylls[sh:sh+4]); vip2=identify_vipula(slp1_sylls[sh+16:sh+20])
            for idx,vip in enumerate((vip1,vip2)):
                if vip and vip in vipula_sel:
                    row=line_len-1-(sh//line_len) - idx*2
                    for j in range(min(4,line_len)):
                        ax.add_patch(Rectangle((j,row),1,1,facecolor=vipula_colors[vip],alpha=0.5))

    # Pathyā highlight
    if show_pathya and classify_anushtubh(slp1_sylls):
        ax.add_patch(Rectangle((0,0),line_len,line_len,fill=False,edgecolor=pathya_color,linewidth=3))

    # Anuprāsa
    if show_anuprasa:
        for i,row in enumerate(rows):
            reps=detect_anuprasa(row)
            for j,s in enumerate(row):
                init=re.match(r'[^\W\d_]*',s).group(0)
                if init in reps:
                    ax.add_patch(Rectangle((j,line_len-1-i),1,1,fill=False,edgecolor='blue',linewidth=2))

    # Yamaka
    if show_yamaka:
        for i,j in detect_sloka_yamaka(slp1_sylls):
            ax.add_patch(Circle((j+0.5,line_len-1-i+0.5),0.15,color='purple'))

    ax.set_title(f"{line_len}×{line_len} — Pathyā={show_pathya}",fontsize=10)
    # Legend
    legend=[Patch(facecolor='black',edgecolor='black',label='Guru'),Patch(facecolor='white',edgecolor='black',label='Laghu')]
    for vip,col in vipula_colors.items():
        if vip in vipula_sel: legend.append(Patch(facecolor=col,alpha=0.5,label=f'Vipula:{vip}'))
    if show_pathya: legend.append(Patch(facecolor='none',edgecolor=pathya_color,linewidth=2,label='Pathyā'))
    if show_anuprasa: legend.append(Patch(facecolor='none',edgecolor='blue',linewidth=2,label='Anuprāsa'))
    if show_yamaka: legend.append(Patch(facecolor='purple',label='Yamaka',alpha=0.5))
    ax.legend(handles=legend,loc='lower center',bbox_to_anchor=(0.5,-0.25),ncol=3,fontsize=8)
    st.pyplot(fig)

    # IAST под строками
    rows_iast=[iast_sylls[i:i+line_len] for i in range(0,len(iast_sylls),line_len)]
    for row in rows_iast:
        st.write(' '.join(row))

# ===== UI =====
st.title('Shloka Visualizer')
text=st.text_area('Введите шлоки в IAST',height=200)

vipula_sel=st.multiselect('Выберите Vipula',options=list(vipula_colors.keys()),default=list(vipula_colors.keys()))
show_pathya=st.checkbox('Подсветить Pathyā-anuṣṭubh',value=False)
show_anuprasa=st.checkbox('Показать Anuprāsa',value=False)
show_yamaka=st.checkbox('Показать Yamaka',value=False)
line_len=st.selectbox('Слоги в строке',[8,16,32],index=0)

if st.button('Визуализировать'):
    if not text.strip(): st.warning('Введите текст')
    else:
        slp1=normalize(text)
        slp1_syl=split_syllables_slp1(slp1)
        iast_syl=[transliterate(s,sanscript.SLP1,sanscript.IAST) for s in slp1_syl]
        for i in range(0,len(slp1_syl),line_len*line_len):
            st.subheader(f'Блок {i//(line_len*line_len)+1}')
            visualize_grid(slp1_syl[i:i+line_len*line_len],iast_syl[i:i+line_len*line_len],line_len,vipula_sel,show_pathya,show_anuprasa,show_yamaka)
