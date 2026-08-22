import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    import time
                    time.sleep(1)
                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name
                    st.session_state.current_panel = "Diseño"
                    st.rerun()

                    # Abrir archivo automáticamente (en Windows usa la app predeterminada para .std)
                    if os.name == 'nt':
                        os.startfile(full_path)
                    else:
                        subprocess.call(('open', full_path))"""

new_block = """                    # Abrir archivo automáticamente (en Windows usa la app predeterminada para .std)
                    if os.name == 'nt':
                        os.startfile(full_path)
                    else:
                        import subprocess
                        subprocess.call(('open', full_path))
                        
                    import time
                    time.sleep(1)
                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name
                    st.session_state.current_panel = "Diseño"
                    st.rerun()"""

content = content.replace(old_block, new_block)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
