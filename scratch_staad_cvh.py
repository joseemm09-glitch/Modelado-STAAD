import sys
import re

with open('app/staad_writer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify write_staad signature
old_sig = "def write_staad(model: StaadModel, selected_profiles: dict = None) -> str:"
new_sig = "def write_staad(model: StaadModel, selected_profiles: dict = None, cvh_props: dict = None) -> str:"
content = content.replace(old_sig, new_sig)

# 2. Modify CVH property assignment
old_cvh_prop = """    if cv_str:
        out.append("** CVH **")
        out.append(build_lines(cv_str.split(" ") + ["TABLE ST PIPE OD 1.905 ID 0"], 72))"""

new_cvh_prop = """    if cv_str:
        out.append("** CVH **")
        if cvh_props:
            diam_groups = {}
            for m in model.groups.get('_CVH', []):
                d = cvh_props.get(m, 1.905)
                diam_groups.setdefault(d, []).append(m)
            for d, mids in diam_groups.items():
                d_str = group_ranges(mids)
                out.append(build_lines(d_str.split(" ") + [f"TABLE ST PIPE OD {d} ID 0"], 72))
        else:
            out.append(build_lines(cv_str.split(" ") + ["TABLE ST PIPE OD 1.905 ID 0"], 72))"""

content = content.replace(old_cvh_prop, new_cvh_prop)

with open('app/staad_writer.py', 'w', encoding='utf-8') as f:
    f.write(content)
