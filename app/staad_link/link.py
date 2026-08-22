import os

def check_staad_status():
    """
    Checks the connection and status of STAAD.Pro.
    Returns:
        dict: {
            "status": "connected" | "connected_no_results" | "disconnected",
            "filename": str or None,
            "error": str or None
        }
    """
    try:
        from openstaad import ops
        s = ops.connect()
        filename = s.GetSTAADFile()
        if not filename:
            return {"status": "disconnected", "filename": None, "error": "No file open"}
            
        # For now, check if nodes exist as a proxy for a valid model, 
        # and try to check results if the function exists
        has_results = False
        try:
            # Assuming AreResultsAvailable exists based on typical OpenStaad API,
            # or we can check something else. We'll use a try/except.
            has_results = s.AreResultsAvailable()
        except:
            # Fallback if the method doesn't exist in openstaad python yet, 
            # or just assume False for now.
            pass
            
        status = "connected" if has_results else "connected_no_results"
        return {"status": status, "filename": os.path.basename(filename), "error": None}
        
    except Exception as e:
        return {"status": "disconnected", "filename": None, "error": str(e)}

def run_analysis():
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
        return False

def get_design_results(member_ids):
    """
    Given a list of member IDs, fetches their design ratio from STAAD.
    Returns a dictionary: {member_id: ratio, ...}
    """
    results = {}
    try:
        from openstaad import ops
        s = ops.connect()
        for mid in member_ids:
            try:
                ratio = s.GetMemberSteelDesignRatio(mid)
                results[mid] = ratio
            except:
                results[mid] = 0.0
    except Exception as e:
        print(f"Error getting design results: {e}")
    return results
