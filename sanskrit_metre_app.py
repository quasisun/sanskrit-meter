import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
import re
import unicodedata
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate

# Define syllable categories
short_vowels = ['a', 'i', 'u', 'ṛ', 'ḷ']
long_vowels = ['ā', 'ī', 'ū', 'ṝ', 'e', 'ai', 'o', 'au']

def normalize_text(text):
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[।॥|॥]', '', text)
    return text.strip()

def detect_script(text):
    if any('\u0B80' <= c <= '\u0BFF' for c in text):
        return 'tamil'
    elif any('\u0900' <= c <= '\u097F' for c in text):
        return 'devanagari'
    else:
        return 'iast'  # assume default

def transliterate_to_iast(text):
    script = detect_script(text)
    if script == 'iast':
        return text.lower()
    else:
        return transliterate(text, script, 'iast').lower()

def split_syllables(text):
    # Very simple syllable splitter
    return re.findall(r'[^aeiouṛḷāīūṝeoau]*[aeiouṛḷāīūṝeoau]+(?:[ṃḥ])?', text)

def is_guru(syl):
    if any(v in syl for v in long_vowels):
        return True
    if syl.endswith('ṃ') or syl.endswith('ḥ'):
        return True
    return False

def make_blocks(syllables, row_length, rows_per_block=8):
    block_size = row_length * rows_per_block
    return [syllables[i:i+block_size] for i in range(0, len(syllables), block_size)]

def syllables_to_grid(syllables, row_length):
    grid = []
    for i in range(0, len(syllables), row_length):
        row = syllables[i:i+row_length]
        binary = [1 if is_guru(s) else 0 for s in row]
        binary += [0]*(row_length - len(binary))  # pad
        grid.append(binary)
    while len(grid) < 8:
        grid.append([0]*row_length)
    return grid

def plot_grid(grid, index, row_length):
    plt.figure(figsize=(row_length/2, 4))
    plt.imshow(grid, cmap='gray', interpolation='nearest')
    plt.axis('off')
    plt.title(f'Block {index+1} ({row_length}×8)')
    plt.savefig(f"block_{row_length}_{index+1:02d}.png", bbox_inches='tight', pad_inches=0)
    plt.close()

def process_text(text, row_length):
    text = normalize_text(transliterate_to_iast(text))
    syllables = split_syllables(text)
    blocks = make_blocks(syllables, row_length)
    for i, block in enumerate(blocks):
        grid = syllables_to_grid(block, row_length)
        plot_grid(grid, i, row_length)
    return len(blocks)

# === GUI ===

def on_generate():
    text = text_input.get("1.0", tk.END)
    if not text.strip():
        messagebox.showwarning("No Input", "Please enter some Sanskrit or Tamil text.")
        return
    try:
        row_length = int(syllable_choice.get())
        blocks_generated = process_text(text, row_length)
        messagebox.showinfo("Success", f"{blocks_generated} blocks generated and saved as PNG.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create main window
root = tk.Tk()
root.title("Sanskrit Meter Visualizer")

# Text input
tk.Label(root, text="Enter Sanskrit/Tamil text:").pack()
text_input = tk.Text(root, height=10, width=70, font=("Courier", 12))
text_input.pack(padx=10, pady=5)

# Options
tk.Label(root, text="Select syllables per row:").pack()
syllable_choice = ttk.Combobox(root, values=["8", "16", "32"])
syllable_choice.set("8")
syllable_choice.pack(pady=5)

# Generate button
generate_btn = tk.Button(root, text="Generate", command=on_generate)
generate_btn.pack(pady=10)

root.mainloop()
