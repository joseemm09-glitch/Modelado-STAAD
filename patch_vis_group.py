import re

with open('app/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the loop to group largueros and hide 'Otros'
old_loop = """        for grp in group_order:
            data = lines_by_group[grp]
            if data['x']:
                lw = 3 if (grp.startswith('_LARGUEROS') or grp in ['_JOISTGRAL', '_JPUNTAL']) else 4
                hidden_legend_groups = ['_CS', '_CI', '_CS_PERIM', '_CI_PERIM', '_MONTANTES', '_DIAG', '_MONTANTES_PERIM', '_DIAG_PERIM', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
                fig.add_trace(go.Scatter3d(
                    x=data['x'],
                    y=data['z'],
                    z=data['y'],
                    mode='lines',
                    line=dict(color=data['color'], width=lw),
                    name=grp,
                    showlegend=(grp not in hidden_legend_groups)
                ))
                
        if lines_by_group['unknown']['x']:
            data = lines_by_group['unknown']
            fig.add_trace(go.Scatter3d(
                x=data['x'],
                y=data['z'],
                z=data['y'],
                mode='lines',
                line=dict(color=data['color'], width=4),
                name='Otros'
            ))"""

new_loop = """        largueros_added = False
        for grp in group_order:
            data = lines_by_group[grp]
            if data['x']:
                lw = 3 if (grp.startswith('_LARGUEROS') or grp in ['_JOISTGRAL', '_JPUNTAL']) else 4
                hidden_legend_groups = ['_CS', '_CI', '_CS_PERIM', '_CI_PERIM', '_MONTANTES', '_DIAG', '_MONTANTES_PERIM', '_DIAG_PERIM', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
                
                is_larguero = grp.startswith('_LARGUEROS')
                show_leg = (grp not in hidden_legend_groups)
                trace_name = grp
                leg_group = None
                
                if is_larguero:
                    trace_name = '_LARGUEROS'
                    leg_group = '_LARGUEROS'
                    if largueros_added:
                        show_leg = False
                    else:
                        largueros_added = True
                        show_leg = True
                        
                fig.add_trace(go.Scatter3d(
                    x=data['x'],
                    y=data['z'],
                    z=data['y'],
                    mode='lines',
                    line=dict(color=data['color'], width=lw),
                    name=trace_name,
                    showlegend=show_leg,
                    legendgroup=leg_group
                ))
                
        if lines_by_group['unknown']['x']:
            data = lines_by_group['unknown']
            fig.add_trace(go.Scatter3d(
                x=data['x'],
                y=data['z'],
                z=data['y'],
                mode='lines',
                line=dict(color=data['color'], width=4),
                name='Otros',
                showlegend=False
            ))"""

content = content.replace(old_loop, new_loop)

with open('app/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch successful!")
