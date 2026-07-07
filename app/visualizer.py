import plotly.graph_objects as go

def get_group_color(group_name):
    colors = {
        '_COL': 'blue',
        '_CS': 'red',
        '_CI': 'orange',
        '_MONTANTES': 'green',
        '_DIAG': 'purple',
        '_LARGUEROS': 'gray',
        '_CVH': 'black'
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

    # We can group lines by color to make plotting faster
    # instead of adding one trace per member.
    lines_by_color = {}

    for mid, (n1, n2) in model.members.items():
        if n1 not in model.nodes or n2 not in model.nodes:
            continue
            
        x0, y0, z0 = model.nodes[n1]
        x1, y1, z1 = model.nodes[n2]
        
        # Convert cm back to meters for visualization purposes
        x0, y0, z0 = x0 / 100.0, y0 / 100.0, z0 / 100.0
        x1, y1, z1 = x1 / 100.0, y1 / 100.0, z1 / 100.0
        
        grp = member_to_group.get(mid, 'unknown')
        color = get_group_color(grp)
        
        if color not in lines_by_color:
            lines_by_color[color] = {'x': [], 'y': [], 'z': [], 'name': grp}
            
        lines_by_color[color]['x'].extend([x0, x1, None])
        lines_by_color[color]['y'].extend([y0, y1, None])
        lines_by_color[color]['z'].extend([z0, z1, None])

    for color, data in lines_by_color.items():
        fig.add_trace(go.Scatter3d(
            x=data['x'],
            y=data['z'], # Plotly Z is up by default in some views, but we'll map Y to Z for better default camera
            z=data['y'],
            mode='lines',
            line=dict(color=color, width=4),
            name=data['name']
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

    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Z (m)',
            zaxis_title='Y (m)',
            aspectmode='data' # Keeps scale proportional
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        title="",
        showlegend=True,
        height=850
    )

    return fig
