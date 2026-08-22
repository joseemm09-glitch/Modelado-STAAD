import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_sleep = """                    import time
                    time.sleep(1)
                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name"""

new_sleep = """                    import time
                    time.sleep(5)
                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name"""

content = content.replace(old_sleep, new_sleep)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
