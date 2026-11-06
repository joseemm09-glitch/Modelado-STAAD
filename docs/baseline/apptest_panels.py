"""Abre cada panel de la app con streamlit AppTest (headless) y reporta excepciones."""
import os
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN = os.path.join(ROOT, "app", "main.py")

for panel in ["Main", "Geometría", "Cargas", "Prediseño", "Cimentación"]:
    try:
        at = AppTest.from_file(MAIN, default_timeout=120)
        at.session_state["current_panel"] = panel
        at.run()
        errs = [e.value for e in at.exception]
        st_err = [e.value for e in at.error]
        print(f"[{panel}] excepciones={len(errs)} errores_ui={len(st_err)}")
        for e in (errs + st_err)[:3]:
            print("   ->", str(e)[:300].replace("\n", " | "))
    except Exception as ex:  # noqa: BLE001
        print(f"[{panel}] FALLO AppTest: {type(ex).__name__}: {str(ex)[:300]}")
