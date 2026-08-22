import sys

with open('app/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_sig = "def plot_model(model, show_supports=False, highlight_ids=None):"
new_sig = "def plot_model(model, show_supports=False, highlight_ids=None, highlight_colors=None):"
content = content.replace(old_sig, new_sig)

with open('app/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
