 recent call last):
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\dynamic.py", line 81, in _GetGoodDispatch
    IDispatch = pythoncom.connect(IDispatch)
pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\from_dspace.py", line 5, in <module>
    cd = win32com.client.Dispatch("ControlDesk75.Application")
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\__init__.py", line 116, in Dispatch
    dispatch, userName = dynamic._GetGoodDispatchAndUserName(dispatch, userName, clsctx)
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\dynamic.py", line 101, in _GetGoodDispatchAndUserName
    return (_GetGoodDispatch(IDispatch, clsctx), userName)
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\dynamic.py", line 83, in _GetGoodDispatch
    IDispatch = pythoncom.CoCreateInstance(
pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)

(capt) C:\Users\javot\Desktop\sofia_code>python from_dspace.py
Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\from_dspace.py", line 7, in <module>
    variables = experiment.Variables
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\dynamic.py", line 631, in __getattr__    raise AttributeError(f"{self._username_}.{attr}")
AttributeError: <unknown>.Variables

(capt) C:\Users\javot\Desktop\sofia_code>python from_dspace.py
Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\from_dspace.py", line 7, in <module>
    variables = experiment.Variables
  File "C:\Users\javot\Desktop\capt\lib\site-packages\win32com\client\dynamic.py", line 631, in __getattr__    raise AttributeError(f"{self._username_}.{attr}")
AttributeError: <unknown>.Variables

(capt) C:\Users\javot\Desktop\sofia_code>


import win32com.client
import time


cd = win32com.client.Dispatch("ControlDesk.Application")
experiment = cd.ActiveExperiment
variables = experiment.Variables

torque_signal = variables.Item("Model Root/Subsystem2/Torque")

while True:
    live_value = torque_signal.Value
    print(f"Live Data: {live_value}")
    time.sleep(0.01) # Polls at ~100Hz
