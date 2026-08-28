import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_css = """<style>
/* iOS Liquid Glass Effect for containers */"""

new_css = """<style>
/* Mobile layout adjustments for Plotly 3D Viewer */
@media screen and (max-width: 768px) {
    div[data-testid="stPlotlyChart"],
    div[data-testid="stPlotlyChart"] iframe,
    div[data-testid="stPlotlyChart"] .js-plotly-plot, 
    div[data-testid="stPlotlyChart"] .plot-container.plotly, 
    div[data-testid="stPlotlyChart"] .svg-container {
        height: 450px !important;
        min-height: 450px !important;
        max-height: 450px !important;
    }
}

/* iOS Liquid Glass Effect for containers */"""

content = content.replace(old_css, new_css)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch successful!")
