import plotly.graph_objects as go

def get_group_color(group_name):
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
    return colors.get(group_name, 'black')

def plot_model(model, show_supports=False, highlight_ids=None, highlight_colors=None):
    """
    Plots the StaadModel using Plotly 3D scatter.
    If highlight_ids is provided, those members are drawn in red and thicker,
    while the rest are drawn transparent gray.
    """
    fig = go.Figure()

    # Create a mapping from member to its group
    member_to_group = {}
    for grp_name, mem_list in model.groups.items():
        for m in mem_list:
            member_to_group[m] = grp_name

    # We group lines by group to draw them in a consistent order in the legend.
    group_order = ['_COL', '_COLVIENTO', '_CS', '_CI', '_CS_PERIM', '_CI_PERIM', '_MONTANTES', '_DIAG', '_MONTANTES_PERIM', '_DIAG_PERIM', '_LARGUEROS', '_JOISTGRAL', '_JPUNTAL', '_CVH', '_CS_SEC', '_CI_SEC', '_MONTANTES_SEC', '_DIAG_SEC']
    
    if highlight_ids is not None or highlight_colors is not None:
        lines_by_group = {
            'highlighted': {'x': [], 'y': [], 'z': [], 'color': '#ba281b', 'width': 6},
            'highlighted_green': {'x': [], 'y': [], 'z': [], 'color': '#0b7a0b', 'width': 6},
            'faded': {'x': [], 'y': [], 'z': [], 'color': '#b0b8c0', 'width': 2}
        }
    else:
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
        
        if highlight_ids is not None or highlight_colors is not None:
            if highlight_colors is not None and mid in highlight_colors:
                target_grp = 'highlighted' if highlight_colors[mid] == 'red' else 'highlighted_green'
            elif highlight_ids is not None and mid in highlight_ids:
                target_grp = 'highlighted'
            else:
                target_grp = 'faded'
        else:
            target_grp = member_to_group.get(mid, 'unknown')
            if target_grp not in lines_by_group:
                target_grp = 'unknown'
            
        lines_by_group[target_grp]['x'].extend([x0, x1, None])
        lines_by_group[target_grp]['y'].extend([y0, y1, None])
        lines_by_group[target_grp]['z'].extend([z0, z1, None])

    if highlight_ids is not None or highlight_colors is not None:
        ordered_keys = ['highlighted', 'highlighted_green', 'faded']
        name_map = {
            'highlighted': 'Grupo Seleccionado' if highlight_colors is None else 'Falla (Ratio > 0.5)',
            'highlighted_green': 'Adecuado (Ratio ≤ 0.5)',
            'faded': 'Resto Estructura'
        }
        for grp_name in ordered_keys:
            data = lines_by_group[grp_name]
            if data['x']:
                fig.add_trace(go.Scatter3d(
                    x=data['x'], y=data['z'], z=data['y'],
                    mode='lines',
                    line=dict(color=data['color'], width=data['width']),
                    name=name_map[grp_name],
                    opacity=0.45 if grp_name == 'faded' else 1.0
                ))
    else:
        for grp in group_order:
            data = lines_by_group[grp]
            if data['x']:
                lw = 3 if grp in ['_LARGUEROS', '_JOISTGRAL', '_JPUNTAL'] else 4
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
            ))
        
    # Plot plates if any (Tilt-Up)
    if getattr(model, 'plates', None):
        px, py, pz = [], [], []
        i_idx, j_idx, k_idx = [], [], []
        idx = 0
        
        ox, oy, oz = [], [], [] # Outlines
        
        for pid, (n1, n2, n3, n4) in model.plates.items():
            # Add to mesh
            for n in [n1, n2, n3, n4]:
                x, y, z = model.nodes[n]
                px.append(x / 100.0)
                py.append(z / 100.0) # Plotly Y is Model Z
                pz.append(y / 100.0) # Plotly Z is Model Y
                
            i_idx.extend([idx, idx])
            j_idx.extend([idx+1, idx+2])
            k_idx.extend([idx+2, idx+3])
            idx += 4
            
            # Add to outlines
            for n in [n1, n2, n3, n4, n1]:
                x, y, z = model.nodes[n]
                ox.append(x / 100.0)
                oy.append(z / 100.0)
                oz.append(y / 100.0)
            ox.append(None)
            oy.append(None)
            oz.append(None)
            
        fig.add_trace(go.Mesh3d(
            x=px, y=py, z=pz,
            i=i_idx, j=j_idx, k=k_idx,
            color='lightgray',
            opacity=0.15 if highlight_ids is not None else 0.65,
            name='Muros (Plates)'
        ))
        
        fig.add_trace(go.Scatter3d(
            x=ox, y=oy, z=oz,
            mode='lines',
            line=dict(color='gray', width=2),
            name='Bordes Muros',
            showlegend=False
        ))

    node_opacity = 0.0 if highlight_ids is not None else 1.0
    
    # Also plot nodes as small dots
    fig.add_trace(go.Scatter3d(
        x=[n[0] / 100.0 for n in model.nodes.values()],
        y=[n[2] / 100.0 for n in model.nodes.values()],
        z=[n[1] / 100.0 for n in model.nodes.values()],
        mode='markers',
        marker=dict(size=2, color='black'),
        name='Nodos',
        showlegend=False,
        opacity=node_opacity
    ))

    # Plot supports
    if show_supports and model.base_nodes:
        if model.support_type.upper() == "RESORTE":
            rx, ry, rz = [], [], []
            gx, gy, gz = [], [], []
            bx, by, bz = [], [], []
            L = 0.5   # Longitud de la línea paralela al eje (mitad de antes)
            w = 0.75  # Longitud de la línea perpendicular (75% de antes)
            d = 0.225 # Longitud de las diagonales (75% de antes)
            
            for nid in model.base_nodes:
                nx = model.nodes[nid][0] / 100.0
                ny = model.nodes[nid][2] / 100.0 # Plotly Y is Model Z
                nz = model.nodes[nid][1] / 100.0 # Plotly Z is Model Y
                
                # GREEN (Resorte Y): línea paralela a Z Plotly (Y Model) hacia abajo
                gx.extend([nx, nx, None])
                gy.extend([ny, ny, None])
                gz.extend([nz, nz - L, None])
                # Perpendicular a lo largo de X Plotly
                gx.extend([nx - w/2, nx + w/2, None])
                gy.extend([ny, ny, None])
                gz.extend([nz - L, nz - L, None])
                # 4 Diagonales
                for i in range(4):
                    px = (nx - w/2) + i * (w / 3)
                    gx.extend([px, px - d, None])
                    gy.extend([ny, ny, None])
                    gz.extend([nz - L, nz - L - d, None])
                
                # RED (Resorte X): línea paralela a X Plotly (X Model) hacia atrás (-X)
                rx.extend([nx, nx - L, None])
                ry.extend([ny, ny, None])
                rz.extend([nz, nz, None])
                # Perpendicular a lo largo de Z Plotly (Y Model)
                rx.extend([nx - L, nx - L, None])
                ry.extend([ny, ny, None])
                rz.extend([nz - w/2, nz + w/2, None])
                # 4 Diagonales
                for i in range(4):
                    pz = (nz - w/2) + i * (w / 3)
                    rx.extend([nx - L, nx - L - d, None])
                    ry.extend([ny, ny, None])
                    rz.extend([pz, pz - d, None])
                    
                # BLUE (Resorte Z): línea paralela a Y Plotly (Z Model) hacia atrás (-Y Plotly)
                bx.extend([nx, nx, None])
                by.extend([ny, ny - L, None])
                bz.extend([nz, nz, None])
                # Perpendicular a lo largo de X Plotly
                bx.extend([nx - w/2, nx + w/2, None])
                by.extend([ny - L, ny - L, None])
                bz.extend([nz, nz, None])
                # 4 Diagonales
                for i in range(4):
                    px = (nx - w/2) + i * (w / 3)
                    bx.extend([px, px - d, None])
                    by.extend([ny - L, ny - L - d, None])
                    bz.extend([nz, nz, None])
                    
            fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='lines', line=dict(color='red', width=3), name='Resorte X', legendgroup='resorte', showlegend=False))
            fig.add_trace(go.Scatter3d(x=gx, y=gy, z=gz, mode='lines', line=dict(color='lime', width=3), name='Resorte Y', legendgroup='resorte', showlegend=False))
            fig.add_trace(go.Scatter3d(x=bx, y=by, z=bz, mode='lines', line=dict(color='blue', width=3), name='Apoyos', legendgroup='resorte', showlegend=True))
        else:
            sup_x, sup_y, sup_z = [], [], []
            is_fixed = (model.support_type.upper() == "FIXED")
            
            for nid in model.base_nodes:
                nx = model.nodes[nid][0] / 100.0
                ny = model.nodes[nid][2] / 100.0 # Plotly Y is Model Z
                nz = model.nodes[nid][1] / 100.0 # Plotly Z is Model Y
                
                if is_fixed:
                    w = 1.2
                    h = 0.6
                    sup_x.extend([nx - w/2, nx + w/2, nx + w/2, nx - w/2, nx - w/2, None])
                    sup_y.extend([ny, ny, ny, ny, ny, None])
                    sup_z.extend([nz, nz, nz - h, nz - h, nz, None])
                else:
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
            
        name_support = 'Apoyos (Muro)' if getattr(model, 'wall_type', None) == 'Tilt-Up' else 'Apoyos (Viento)'
        fig.add_trace(go.Scatter3d(
            x=wsup_x,
            y=wsup_y,
            z=wsup_z,
            mode='lines',
            line=dict(color='darkred', width=3),
            name=name_support,
            showlegend=True
        ))

    # Custom grid ticks matching model dimensions
    x_ticks = [i * model.Larm_m for i in range(model.nSpan + 1)] if hasattr(model, 'Larm_m') else None
    y_ticks = [i * model.Ljoist_m for i in range(model.nBay + 1)] if hasattr(model, 'Ljoist_m') else None
    z_ticks = [0, model.HLibre_m, model.HLibre_m + model.HArmad_m] if hasattr(model, 'HLibre_m') else None

    scene_config = dict(
        xaxis=dict(title='X (m)'),
        yaxis=dict(title='Z (m)'),
        zaxis=dict(title='Y (m)'),
        aspectmode='data', # Keeps scale proportional
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=1.2),
            center=dict(x=-0.2, y=0, z=-0.5),
            up=dict(x=0, y=0, z=1)
        )
    )
    if x_ticks is not None: scene_config['xaxis']['tickvals'] = x_ticks
    if y_ticks is not None: scene_config['yaxis']['tickvals'] = y_ticks
    if z_ticks is not None: scene_config['zaxis']['tickvals'] = z_ticks

    fig.update_layout(
        scene=scene_config,
        margin=dict(l=0, r=0, b=0, t=0),
        title="",
        showlegend=True,
        uirevision='model_view',
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
                    dict(label="Iso", method="relayout", args=["scene.camera", dict(eye=dict(x=1.5, y=1.5, z=1.2), center=dict(x=0, y=0, z=-0.5), up=dict(x=0, y=0, z=1))]),
                    dict(label="Planta", method="relayout", args=["scene.camera", dict(eye=dict(x=0, y=0, z=2.5), center=dict(x=0, y=0, z=-0.5), up=dict(x=0, y=1, z=0))]),
                    dict(label="Lat. X", method="relayout", args=["scene.camera", dict(eye=dict(x=0, y=-2.5, z=0), center=dict(x=0, y=0, z=-0.5), up=dict(x=0, y=0, z=1))]),
                    dict(label="Lat. Z", method="relayout", args=["scene.camera", dict(eye=dict(x=-2.5, y=0, z=0), center=dict(x=0, y=0, z=-0.5), up=dict(x=0, y=0, z=1))])
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
