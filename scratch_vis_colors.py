import sys
import re

with open('app/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Modify def plot_model
content = content.replace("def plot_model(model, show_supports=True, highlight_ids=None):", "def plot_model(model, show_supports=True, highlight_ids=None, highlight_colors=None):")

# Modify highlight grouping
old_highlight = """    if highlight_ids is not None:
        lines_by_group = {
            'highlighted': {'x': [], 'y': [], 'z': [], 'color': 'red', 'width': 6},
            'normal_cols': {'x': [], 'y': [], 'z': [], 'color': get_group_color('_COL'), 'width': 4},
            'normal_wind_cols': {'x': [], 'y': [], 'z': [], 'color': get_group_color('_COLVIENTO'), 'width': 4},
            'faded': {'x': [], 'y': [], 'z': [], 'color': '#b0b0b0', 'width': 2}
        }
    else:"""

new_highlight = """    if highlight_ids is not None or highlight_colors is not None:
        lines_by_group = {
            'highlighted': {'x': [], 'y': [], 'z': [], 'color': 'red', 'width': 6},
            'highlighted_green': {'x': [], 'y': [], 'z': [], 'color': '#0b7a0b', 'width': 6},
            'normal_cols': {'x': [], 'y': [], 'z': [], 'color': get_group_color('_COL'), 'width': 4},
            'normal_wind_cols': {'x': [], 'y': [], 'z': [], 'color': get_group_color('_COLVIENTO'), 'width': 4},
            'faded': {'x': [], 'y': [], 'z': [], 'color': '#e0e0e0', 'width': 1}
        }
    else:"""

content = content.replace(old_highlight, new_highlight)

# Modify member loop
old_loop = """        if highlight_ids is not None:
            if mid in highlight_ids:
                target_grp = 'highlighted'
            elif member_to_group.get(mid) == '_COL':
                target_grp = 'normal_cols'
            elif member_to_group.get(mid) == '_COLVIENTO':
                target_grp = 'normal_wind_cols'
            else:
                target_grp = 'faded'
        else:"""

new_loop = """        if highlight_ids is not None or highlight_colors is not None:
            if highlight_colors is not None and mid in highlight_colors:
                target_grp = 'highlighted' if highlight_colors[mid] == 'red' else 'highlighted_green'
            elif highlight_ids is not None and mid in highlight_ids:
                target_grp = 'highlighted'
            elif member_to_group.get(mid) == '_COL':
                target_grp = 'normal_cols'
            elif member_to_group.get(mid) == '_COLVIENTO':
                target_grp = 'normal_wind_cols'
            else:
                target_grp = 'faded'
        else:"""

content = content.replace(old_loop, new_loop)

# Modify the legend names
old_trace = """    for grp, data in lines_by_group.items():
        if not data['x']: continue
        
        name_map = {
            'highlighted': 'Grupo Seleccionado',
            'normal_cols': 'Resto Columnas',
            'normal_wind_cols': 'Resto Columnas Viento',
            'faded': 'Resto Estructura'
        }"""

new_trace = """    for grp, data in lines_by_group.items():
        if not data['x']: continue
        
        name_map = {
            'highlighted': 'Falla (Ratio > 0.5)' if highlight_colors else 'Grupo Seleccionado',
            'highlighted_green': 'Pasa (Ratio <= 0.5)',
            'normal_cols': 'Resto Columnas',
            'normal_wind_cols': 'Resto Columnas Viento',
            'faded': 'Resto Estructura'
        }"""

content = content.replace(old_trace, new_trace)

with open('app/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
