print(Application.ActiveProjectRoot)
<COMObject <unknown>>
print(dir(Application.ActiveProjectRoot))
['Activate', 'AddRef', 'GetIDsOfNames', 'GetTypeInfo', 'GetTypeInfoCount', 'Invoke', 'PathName', 'Projects', 'QueryInterface', 'Release', 'Remove', '_ApplyTypes_', '_FlagAsMethod', '_LazyAddAttr_', '_NewEnum', '_Release_', '_UpdateWithITypeInfo_', '__AttrToID__', '__LazyMap__', '__bool__', '__call__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__int__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_builtMethods_', '_dir_ole_', '_enum_', '_find_dispatch_type_', '_get_good_object_', '_get_good_single_object_', '_lazydata_', '_make_method_', '_mapCachedItems_', '_oleobj_', '_olerepr_', '_print_details_', '_proc_', '_unicode_to_string_', '_username_', '_wrap_dispatch_']
print(dir(Application.ActiveProjectRoot.Projects))
['Add', 'AddRef', 'Contains', 'Count', 'GetEnumerator', 'GetIDsOfNames', 'GetTypeInfo', 'GetTypeInfoCount', 'Invoke', 'Item', 'OpenFromBackup', 'ProjectRoot', 'QueryInterface', 'Release', '_ApplyTypes_', '_FlagAsMethod', '_LazyAddAttr_', '_NewEnum', '_Release_', '_UpdateWithITypeInfo_', '__AttrToID__', '__LazyMap__', '__bool__', '__call__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__int__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_builtMethods_', '_dir_ole_', '_enum_', '_find_dispatch_type_', '_get_good_object_', '_get_good_single_object_', '_lazydata_', '_make_method_', '_mapCachedItems_', '_oleobj_', '_olerepr_', '_print_details_', '_proc_', '_unicode_to_string_', '_username_', '_wrap_dispatch_']
print(dir(Application.ActiveProjectRoot.Projects.Item))
['__call__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__func__', '__ge__', '__get__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__self__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__']
print(dir(Application.ActiveProjectRoot.Projects.GetIDsOfNames))

['__call__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__func__', '__ge__', '__get__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__self__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__']



import win32com.client
import time
import sys

try:
    cd = win32com.client.Dispatch("ControlDeskNG.Application")
    print("Connected to ControlDesk 7.5!")

    experiment = cd.ActiveExperiment
    if experiment is None:
        print("ERROR: No active experiment open in ControlDesk.")
        sys.exit()

    # SAFE CHECK: Loop through platforms instead of calling Item(1)
    platform = None
    for p in experiment.Platforms:
        platform = p
        break

    if platform is None:
        print("ERROR: No active hardware platform found in this experiment.")
        sys.exit()
        
    print(f"Found Active Hardware Platform: {platform.Name}")

    # SAFE CHECK: Verify the variable description is actually ready
    var_desc = platform.ActiveVariableDescription
    if var_desc is None:
        print("ERROR: Variable description file (.trc) is not loaded. Is ControlDesk Online?")
        sys.exit()

    dataset = var_desc.DataSets.WorkingDataSet
    
    # Change this to a real variable name from your Simulink model
    test_path = "Model Root/Subsystem/MySignal" 

    try:
        my_signal = dataset.Parameter.Item(test_path)
        print("Success! Target variable found.")
    except Exception:
        print(f"\nPath '{test_path}' not found in the live map.")
        print("--------------------------------------------------")
        print("PRINTING RECENT VARIABLES IN YOUR MODEL ENGINE:")
        count = min(10, dataset.Parameter.Count)
        for i in range(1, count + 1):
            print(f"   Valid Path option: {dataset.Parameter.Item(i).Path}")
        print("--------------------------------------------------")
        sys.exit()

    print("\nStreaming real-time data... Press Ctrl+C to stop.\n")
    while True:
        live_value = my_signal.Value
        print(f"Live Variable Value: {live_value}")
        time.sleep(0.01)

except Exception as e:
    print(f"\nExecution Error: {e}")


