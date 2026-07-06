print(dir(my_platform.VariableDescriptions))
['Add', 'AddFromContainer', 'Contains', 'Count', 'GetEnumerator', 'Item', '_ApplyTypes_', '_FlagAsMethod', '_LazyAddAttr_', '_NewEnum', '_Release_', '_UpdateWithITypeInfo_', '__AttrToID__', '__LazyMap__', '__bool__', '__call__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__int__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_builtMethods_', '_dir_ole_', '_enum_', '_find_dispatch_type_', '_get_good_object_', '_get_good_single_object_', '_lazydata_', '_make_method_', '_mapCachedItems_', '_oleobj_', '_olerepr_', '_print_details_', '_proc_', '_unicode_to_string_', '_username_', '_wrap_dispatch_']


import socket
import struct
import time

# 1. Network Configuration
UDP_IP = "134.105.60.99"
UDP_PORT = 55001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# The UI path string that you copied exactly
VAR_PATH = r'Platform()://Model Root/Subsystem2/Ch16/Out1'

try:
    active_platforms = Application.ActiveExperiment.Platforms
    if len(active_platforms) == 0:
        raise RuntimeError("No active platform found. Ensure your experiment is open.")
        
    my_platform = active_platforms[0]
    
    print(f"Connected to Platform: {my_platform.Name}")
    print(f"Direct memory polling active for: {VAR_PATH}")
    print("Click 'Stop' in the script toolbar to halt.")
    
    # 2. Main UDP Direct Loop
    while True:
        try:
            # Bypasses the .Variables lookup container completely
            raw_val = my_platform.ReadVariable(VAR_PATH)
        except Exception:
            # If the platform layer is busy, wait briefly and try the next tick
            time.sleep(0.01)
            continue
            
        # Ignore frames if the hardware hasn't updated or is temporarily unmapped
        if raw_val is None or "unknown" in str(raw_val).lower():
            time.sleep(0.01)
            continue
            
        live_value = float(raw_val)
        
        # Pack into binary data (8-byte double precision float)
        packet = struct.pack("<d", live_value)
        
        # Stream over network socket
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # 100 Hz refresh loop
        time.sleep(0.01)

except Exception as e:
    import traceback
    print("\n--- SCRIPT EXCEPTION ENCOUNTERED ---")
    print(traceback.format_exc())

