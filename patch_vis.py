import re

with open('app/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update get_group_color to handle dynamic group names
old_color_logic = """def get_group_color(group_name):
    colors = {
        '_COL': 'dodgerblue',
        '_COLVIENTO': 'limegreen',
        '_CS': 'red',
        '_CI': 'orange',
        '_CS_PERIM': 'red',
        '_CI_PERIM': 'orange',
        '_MONTANTES': 'green',
        '_DIAG': 'purple',
        '_MONTANTES_PERIM': 'green',
        '_DIAG_PERIM': 'purple',
        '_LARGUEROS': 'gray',
        '_JOISTGRAL': 'gray',
        '_JPUNTAL': 'darkslategray',
        '_CVH': 'black',
        '_CS_SEC': 'red',
        '_CI_SEC': 'orange',
        '_MONTANTES_SEC': 'green',
        '_DIAG_SEC': 'purple'
    }
    return colors.get(group_name, 'black')"""

new_color_logic = """def get_group_color(group_name):
    if group_name.startswith('_LARGUEROS'):
        return 'gray'
        
    colors = {
        '_COL': 'dodgerblue',
        '_COLVIENTO': 'limegreen',
        '_CS': 'red',
        '_CI': 'orange',
        '_CS_PERIM': 'red',
        '_CI_PERIM': 'orange',
        '_MONTANTES': 'green',
        '_DIAG': 'purple',
        '_MONTANTES_PERIM': 'green',
        '_DIAG_PERIM': 'purple',
        '_JOISTGRAL': 'gray',
        '_JPUNTAL': 'darkslategray',
        '_CVH': 'black',
        '_CS_SEC': 'red',
        '_CI_SEC': 'orange',
        '_MONTANTES_SEC': 'green',
        '_DIAG_SEC': 'purple'
    }
    return colors.get(group_name, 'black')"""

content = content.replace(old_color_logic, new_color_logic)

# 2. In plot_structure_3d, we need to gather all groups dynamically
# group_order currently hardcodes '_LARGUEROS'. 
# We should change it so that we don't rely on group_order for _LARGUEROS_X.
old_order_logic = """    group_order = ['_COL', '_COLVIENTO', '_CS', '_CI', '_CS_PERIM', '_CI_PERIM', '_MONTANTES', '_DIAG', '_MONTANTES_PERIM', '_DIAG_PERIM', '_LARGUEROS', '_JOISTGRAL', '_JPUNTAL', '_CVH', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
    
    if highlight_ids is not None or highlight_colors is not None:"""

new_order_logic = """    # Find all LARGUEROS groups and append them
    largueros_groups = [g for g in lines_by_group.keys() if g.startswith('_LARGUEROS')]
    group_order = ['_COL', '_COLVIENTO', '_CS', '_CI', '_CS_PERIM', '_CI_PERIM', '_MONTANTES', '_DIAG', '_MONTANTES_PERIM', '_DIAG_PERIM'] + largueros_groups + ['_JOISTGRAL', '_JPUNTAL', '_CVH', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
    
    if highlight_ids is not None or highlight_colors is not None:"""

content = content.replace(old_order_logic, new_order_logic)

# 3. Fix width logic for LARGUEROS_X
old_width_logic = """                lw = 3 if grp in ['_LARGUEROS', '_JOISTGRAL', '_JPUNTAL'] else 4"""
new_width_logic = """                lw = 3 if (grp.startswith('_LARGUEROS') or grp in ['_JOISTGRAL', '_JPUNTAL']) else 4"""

content = content.replace(old_width_logic, new_width_logic)

with open('app/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Visualizer patch successful!")
