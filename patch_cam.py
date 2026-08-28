import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

detect_logic = """# Import configurations
is_mobile_client = False
try:
    import js
    if js.window.innerWidth <= 768:
        is_mobile_client = True
except Exception:
    pass
"""

# Insert detect_logic after imports but before main layout
old_imports = """import json
import base64
from visualizer import plot_model"""

new_imports = old_imports + "\n\n" + detect_logic

content = content.replace(old_imports, new_imports)

# Update first plot (Prediseño)
old_plot1 = """        # Cube aspect ratio to prevent clipping, and zoomed out slightly
        fig.update_layout(
            scene_camera=dict(eye=dict(x=1.8, y=1.8, z=1.8)),"""

new_plot1 = """        # Cube aspect ratio to prevent clipping, and zoomed out slightly
        cam_zoom = 3.6 if is_mobile_client else 1.8
        fig.update_layout(
            scene_camera=dict(eye=dict(x=cam_zoom, y=cam_zoom, z=cam_zoom)),"""

content = content.replace(old_plot1, new_plot1)

# Update second plot (Main visualizer)
old_plot2 = """        fig = plot_model(model, show_supports=show_sup, highlight_ids=highlight_ids)
        st.plotly_chart(fig, use_container_width=True, config={"""

new_plot2 = """        fig = plot_model(model, show_supports=show_sup, highlight_ids=highlight_ids)
        
        if is_mobile_client:
            fig.update_layout(
                scene_camera=dict(eye=dict(x=3.0, y=3.0, z=3.0))
            )
            
        st.plotly_chart(fig, use_container_width=True, config={"""

content = content.replace(old_plot2, new_plot2)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch for mobile camera zoom successful!")
