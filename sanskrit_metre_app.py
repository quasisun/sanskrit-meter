import matplotlib.pyplot as plt
import re
import unicodedata

# Упрощённый список санскритских гласных
short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[।॥|॥]', '', text)  # убираем данды
    return text.strip()

def split_syllables(text):
    # Очень упрощённое разбиение на слоги
    return re.findall(r'[^aeiouṛḷāīūṝeoau]*[aeiouṛḷāīūṝeoau]+(?:[ṃḥ])?', text)

def is_guru(syllable):
    for lv in long_vowels:
        if lv in syllable:
            return True
    if syllable.endswith('ṃ') or syllable.endswith('ḥ'):
        return True
    return False

def chunk_syllables(syllables, line_length):
    # Делит слоги на строки по line_length слогов
    return [syllables[i:i + line_length] for i in range(0, len(syllables), line_length)]

def pad_grid(rows, width):
    for row in rows:
        row += [0] * (width - len(row))
    while len(rows) < width:
        rows.append([0] * width)
    return rows

def syllables_to_grid(lines, width):
    grid = []
    for line in lines:
        row = [1 if is_guru(s) else 0 for s in line]
        grid.append(row)
    return pad_grid(grid, width)

def plot_grid(grid, index, width):
    plt.figure(figsize=(4, 4))
    plt.imshow(grid, cmap='gray', interpolation='nearest')
    plt.axis('off')
    plt.title(f'Block {index+1} ({width}×{width})')
    plt.savefig(f'grid_{width}x{width}_block_{index+1:02d}.png', bbox_inches='tight', pad_inches=0)
    plt.close()

def process_text(text, line_length):
    text = normalize(text)
    syllables = split_syllables(text)

    # Один блок = квадрат line_length x line_length слогов
    block_size = line_length * line_length
    blocks = [syllables[i:i + block_size] for i in range(0, len(syllables), block_size)]

    for i, block in enumerate(blocks):
        lines = chunk_syllables(block, line_length)
        grid = syllables_to_grid(lines, line_length)
        plot_grid(grid, i, line_length)

# === ПРИМЕР ===
iast_text = """
vande gurūṇāṁ caraṇāravinde sandārśita svātma sukhāvabodhe
niḥśreyase jāṅgalikāyamāne saṁsāra hālāhala mohaśāntyai
guruḥ kṛpātmā daiva-svarūpaḥ śiṣya-priyānanda-vighāta-śāntiḥ
"""

# ==== ВЫБОР ====
# 8  = пада (1 строка = 8 слогов, 1 шлока = 4 строки)
# 16 = половина шлоки
# 32 = целая шлока в строку

line_length = 8  # ← измени на 16 или 32 по желанию

process_text(iast_text, line_length)
