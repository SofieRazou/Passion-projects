
C:\Users\javot\Desktop\MozaIntegration\MozaIntegration>dotnet run -c Release -r win-x64
Unhandled exception. System.DllNotFoundException: Unable to load DLL 'MOZA_API_C.dll' or one of its dependencies: The specified module could not be found. (0x8007007E)
   at mozaAPI.C_SDK_IMPORT.installMozaSDK_C()
   at mozaAPI.C_SDK_IMPORT.installMozaSDK_C()
   at mozaAPI.mozaAPI.installMozaSDK()
   at Program.Main(String[] args) in C:\Users\javot\Desktop\MozaIntegration\MozaIntegration\Program.cs:line 9
