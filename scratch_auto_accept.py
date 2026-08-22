import sys

with open('app/staad_link/link.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_analyze = """def run_analysis():
    try:
        from openstaad import ops
        s = ops.connect()
        s.Analyze() # Block until done
        return True
    except Exception as e:
        print(f"Error running analysis: {e}")
        return False"""

new_analyze = """def run_analysis():
    try:
        from openstaad import ops
        s = ops.connect()
        
        import threading
        def auto_accept():
            import time
            import ctypes
            import win32gui
            
            # Buscamos durante 15 segundos si aparece la ventana de advertencia de STAAD
            for _ in range(30):
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    # #32770 es la clase de sistema de Windows para un MessageBox/Dialogo
                    if "STAAD.Pro" in title and class_name == "#32770":
                        # Enviar tecla Enter para presionar 'Yes'
                        ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0) # Key down
                        ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0) # Key up
                        break
                time.sleep(0.5)
                
        t = threading.Thread(target=auto_accept)
        t.start()
        
        s.Analyze() # Block until done
        return True
    except Exception as e:
        print(f"Error running analysis: {e}")
        return False"""

content = content.replace(old_analyze, new_analyze)

with open('app/staad_link/link.py', 'w', encoding='utf-8') as f:
    f.write(content)
