import time
import win32com.client

try:
    s = win32com.client.GetActiveObject("StaadPro.OpenSTAAD")
    osOutput = s.Output
    start = time.time()
    
    # Just test 100 calls
    for beam in range(1, 10):
        for lc in range(17, 27):
            dMin = win32com.client.VARIANT(win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_R8, 0.0)
            dMinPos = win32com.client.VARIANT(win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_R8, 0.0)
            dMax = win32com.client.VARIANT(win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_R8, 0.0)
            dMaxPos = win32com.client.VARIANT(win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_R8, 0.0)
            osOutput.GetMinMaxAxialForce(beam, lc, dMin, dMinPos, dMax, dMaxPos)
            
    print(f"Time for 90 calls: {time.time() - start:.3f} s")
except Exception as e:
    print("Error:", e)
