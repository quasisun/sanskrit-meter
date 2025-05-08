import matplotlib.pyplot as plt
import re
import unicodedata
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate, DEVANAGARI, TAMIL, IAST

# Список гласных
short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']
all_vowels = short_vowels + long_vowels
consonants = '[kgṅcjñṭḍṇtdnpbmyrlvśṣsh]'

def detect_script(text):
    if re.search(r'[\u0900-\u097F]', text):
        return DEVANAGARI
    if re.search(r'[\u0B80-\u0BFF]', text):
        return TAMIL
    return IAST

def normalize(text):
    script = detect_script(text)
    if script != IAST:
        text = transliterate(text, script, IAST)
    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[।॥|॥]', '', text)  # удаление данд
    return text.strip()

def split_syllables(text):
    text = re.sub(r'\s+', '', text)
    pattern = r"""
        ([^aeiouāīūṛṝeaiouṃḥ]*         # нач. согласные
         [aeiouāīūṛṝeaiou]             # гласная
         (?:ṃ|ḥ)?                      # анусвара или висарга
         (?:{c}(?!h))?)                # возможная финальная согласная
    """.format(c=consonants)
    syllables = re.findall(pattern, text, re.VERBOSE)
    return [s[0] for s in syllables if s[0]]

def is_guru(syl):
    v = re.search(r'[aeiouāīūṛṝeaiou]', syl)
    if not v:
        return False
    vowel = v.group()

    if vowel in long_vowels:
        return True
    if re.search(r'[ṃḥ]', syl):
        return True
    if re.search(r'[aeiouṛḷ]..', syl):
        return True
    return False

def chunk_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def pad_grid(rows, width):
    for row in rows:
        row += [0] * (width - len(row))
    while len(rows) < width:
        rows.append([0] * width)
    return rows

def syllables_to_grid(syllables, line_length):
    lines = chunk_list(syllables, line_length)
    bin_lines = [[1 if is_guru(s) else 0 for s in line] for line in lines]
    return pad_grid(bin_lines, line_length)

def plot_grid(grid, index, line_length):
    plt.figure(figsize=(4, 4))
    plt.imshow(grid, cmap='gray', interpolation='nearest')
    plt.axis('off')
    plt.title(f'Block {index+1} ({line_length}×{line_length})')
    plt.savefig(f'grid_{line_length}x{line_length}_block_{index+1:02d}.png', bbox_inches='tight', pad_inches=0)
    plt.close()

def process_text(text, line_length):
    text = normalize(text)
    syllables = split_syllables(text)
    block_size = line_length * line_length
    blocks = chunk_list(syllables, block_size)

    for i, block in enumerate(blocks):
        grid = syllables_to_grid(block, line_length)
        plot_grid(grid, i, line_length)

# === Примеры ===

# Деванагари
dev_text = """
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥
"""

# Тамильский (пример — теварам, но ты можешь вставить свой)
tam_text = "ஓம் நமோ நாராயணாய"

# IAST
iast_text = """
vande gurūṇāṁ caraṇāravinde sandārśita svātma sukhāvabodhe
"""

# === Выбор текста ===
input_text = dev_text  # замените на tam_text или iast_text

line_length = 8  # или 16, 32
process_text(input_text, line_length)
