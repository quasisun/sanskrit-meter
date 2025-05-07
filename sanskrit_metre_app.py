
import streamlit as st
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import re
import unicodedata
import matplotlib.pyplot as plt
import numpy as np

short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']

def normalize_iast(text):
    return unicodedata.normalize('NFC', text.lower())

def dev_to_iast(text):
    return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)

def split_syllables(text):
    syllables = re.findall(r'[^aeiouṛḷāīūṝeoau]*[aeiouṛḷāīūṝeoau]+(?:[ṃḥ]?)', text)
    return syllables

def is_guru(syllable):
    for lv in long_vowels:
        if lv in syllable:
            return True
    if syllable.endswith('ṃ') or syllable.endswith('ḥ'):
        return True
    return False

def process_verse(text, transliterate_from_dev=True):
    if transliterate_from_dev:
        text = dev_to_iast(text)
    text = normalize_iast(text)
    lines = text.strip().split('\n')
    grid = []
    for line in lines:
        syllables = split_syllables(line)
        row = [1 if is_guru(syl) else 0 for syl in syllables]
        grid.append(row)
    return grid

def plot_grid(grid):
    max_len = max(len(row) for row in grid)
    padded = [row + [0] * (max_len - len(row)) for row in grid]
    arr = np.array(padded)

    fig, ax = plt.subplots(figsize=(max_len, len(grid)))
    ax.imshow(arr, cmap='gray', interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    st.pyplot(fig)

st.title("Санскрит: анализ гуру и лакху")
st.markdown("Определи тяжёлые и лёгкие слоги в шлоке санскритской поэзии (IAST или Деванагари).")

input_text = st.text_area("Введи текст на санскрите (IAST или Деванагари):", height=200)
is_devanagari = st.checkbox("Это текст в Деванагари?", value=True)

if st.button("Анализировать"):
    if not input_text.strip():
        st.warning("Пожалуйста, введите текст.")
    else:
        grid = process_verse(input_text, transliterate_from_dev=is_devanagari)
        st.success("Вот визуализация слогов:")
        plot_grid(grid)
