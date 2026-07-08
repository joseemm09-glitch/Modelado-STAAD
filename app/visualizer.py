import plotly.graph_objects as go

def get_group_color(group_name):
    colors = {
        '_COL': 'dodgerblue',
        '_COLVIENTO': 'limegreen',
        '_CS': 'red',
        '_CI': 'orange',
        '_MONTANTES': 'green',
        '_DIAG': 'purple',
        '_LARGUEROS': 'gray',
        '_JOISTGRAL': 'gray',
        '_JPUNTAL': 'dimgray',
        '_CVH': 'black',
        '_CS_SEC': 'red',
        '_CI_SEC': 'orange',
        '_MONTANTES_SEC': 'green',
        '_DIAG_SEC': 'purple'
    }
    return colors.get(group_name, 'black')

def plot_model(model, show_supports=False):
    """
    Returns a plotly figure representing the 3D STAAD model.
    """
    fig = go.Figure()

    # Create a mapping from member to its group
    member_to_group = {}
    for grp_name, mem_list in model.groups.items():
        for m in mem_list:
            member_to_group[m] = grp_name

    # We group lines by group to draw them in a consistent order in the legend.
    # We initialize lines for each group to ensure they are added in the correct order.
    group_order = ['_COL', '_COLVIENTO', '_CS', '_CI', '_MONTANTES', '_DIAG', '_LARGUEROS', '_JOISTGRAL', '_JPUNTAL', '_CVH', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
    lines_by_group = {grp: {'x': [], 'y': [], 'z': [], 'color': get_group_color(grp)} for grp in group_order}
    lines_by_group['unknown'] = {'x': [], 'y': [], 'z': [], 'color': 'black'}

    for mid, (n1, n2) in model.members.items():
        if n1 not in model.nodes or n2 not in model.nodes:
            continue
            
        x0, y0, z0 = model.nodes[n1]
        x1, y1, z1 = model.nodes[n2]
        
        # Convert cm back to meters for visualization purposes
        x0, y0, z0 = x0 / 100.0, y0 / 100.0, z0 / 100.0
        x1, y1, z1 = x1 / 100.0, y1 / 100.0, z1 / 100.0
        
        grp = member_to_group.get(mid, 'unknown')
        if grp not in lines_by_group:
            grp = 'unknown'
            
        lines_by_group[grp]['x'].extend([x0, x1, None])
        lines_by_group[grp]['y'].extend([y0, y1, None])
        lines_by_group[grp]['z'].extend([z0, z1, None])

    for grp in group_order:
        data = lines_by_group[grp]
        if data['x']:
            lw = 3 if grp in ['_LARGUEROS', '_JOISTGRAL', '_JPUNTAL'] else 4
            fig.add_trace(go.Scatter3d(
                x=data['x'],
                y=data['z'], # Plotly Z is up by default in some views, but we'll map Y to Z for better default camera
                z=data['y'],
                mode='lines',
                line=dict(color=data['color'], width=lw),
                name=grp
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
        ))

    # Also plot nodes as small dots
    fig.add_trace(go.Scatter3d(
        x=[n[0] / 100.0 for n in model.nodes.values()],
        y=[n[2] / 100.0 for n in model.nodes.values()],
        z=[n[1] / 100.0 for n in model.nodes.values()],
        mode='markers',
        marker=dict(size=2, color='black'),
        name='Nodos',
        showlegend=False
    ))

    # Plot supports
    if show_supports and model.base_nodes:
        sup_x, sup_y, sup_z = [], [], []
        
        is_fixed = (model.support_type.upper() == "FIXED")
        
        for nid in model.base_nodes:
            nx = model.nodes[nid][0] / 100.0
            ny = model.nodes[nid][2] / 100.0 # Plotly Y is Model Z
            nz = model.nodes[nid][1] / 100.0 # Plotly Z is Model Y (height, usually 0 at base)
            
            if is_fixed:
                # Rectángulo hueco: alto la mitad del ancho. W=1.2, H=0.6
                w = 1.2
                h = 0.6
                sup_x.extend([nx - w/2, nx + w/2, nx + w/2, nx - w/2, nx - w/2, None])
                sup_y.extend([ny, ny, ny, ny, ny, None])
                sup_z.extend([nz, nz, nz - h, nz - h, nz, None])
            else:
                # Triángulo hueco. W=1.2, H=1.0
                w = 1.2
                h = 1.0
                sup_x.extend([nx, nx + w/2, nx - w/2, nx, None])
                sup_y.extend([ny, ny, ny, ny, None])
                sup_z.extend([nz, nz - h, nz - h, nz, None])
                
        fig.add_trace(go.Scatter3d(
            x=sup_x,
            y=sup_y,
            z=sup_z,
            mode='lines',
            line=dict(color='black', width=3),
            name='Apoyos',
            showlegend=True
        ))

    # Plot wind column supports (Articulaciones / Triángulos rojo oscuro)
    if show_supports and getattr(model, 'wind_base_nodes', None):
        wsup_x, wsup_y, wsup_z = [], [], []
        w = 1.2
        h = 1.0
        for nid in model.wind_base_nodes:
            nx = model.nodes[nid][0] / 100.0
            ny = model.nodes[nid][2] / 100.0 # Plotly Y is Model Z
            nz = model.nodes[nid][1] / 100.0 # Plotly Z is Model Y
            
            # Triángulo hueco. W=1.2, H=1.0
            wsup_x.extend([nx, nx + w/2, nx - w/2, nx, None])
            wsup_y.extend([ny, ny, ny, ny, None])
            wsup_z.extend([nz, nz - h, nz - h, nz, None])
            
        fig.add_trace(go.Scatter3d(
            x=wsup_x,
            y=wsup_y,
            z=wsup_z,
            mode='lines',
            line=dict(color='darkred', width=3),
            name='Apoyos (Viento)',
            showlegend=True
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Z (m)',
            zaxis_title='Y (m)',
            aspectmode='data' # Keeps scale proportional
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        title="",
        showlegend=True,
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.7)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                showactive=True,
                buttons=[
                    dict(label="Iso", method="relayout", args=["scene.camera", dict(eye=dict(x=1.5, y=1.5, z=1.2), up=dict(x=0, y=0, z=1))]),
                    dict(label="Planta", method="relayout", args=["scene.camera", dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))]),
                    dict(label="Lat. X", method="relayout", args=["scene.camera", dict(eye=dict(x=0, y=-2.5, z=0), up=dict(x=0, y=0, z=1))]),
                    dict(label="Lat. Z", method="relayout", args=["scene.camera", dict(eye=dict(x=-2.5, y=0, z=0), up=dict(x=0, y=0, z=1))])
                ]
            )
        ],
        legend=dict(
            bgcolor='rgba(255, 255, 255, 0.65)',
            bordercolor='rgba(255, 255, 255, 0.9)',
            borderwidth=1,
            yanchor="top",
            y=0.95,
            xanchor="right",
            x=0.95
        ),
        height=680
    )

    return fig
