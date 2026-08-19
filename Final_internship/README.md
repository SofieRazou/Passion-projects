
C:\Users\javot\Desktop\MozaIntegration\MozaIntegration>dotnet run -c Release -r win-x64
Unhandled exception. System.DllNotFoundException: Unable to load DLL 'MOZA_API_C.dll' or one of its dependencies: The specified module could not be found. (0x8007007E)
   at mozaAPI.C_SDK_IMPORT.installMozaSDK_C()
   at mozaAPI.C_SDK_IMPORT.installMozaSDK_C()
   at mozaAPI.mozaAPI.installMozaSDK()
   at Program.Main(String[] args) in C:\Users\javot\Desktop\MozaIntegration\MozaIntegration\Program.cs:line 9


CMake Error at C:\Users\javot\Downloads\MOZA_SDK(2)\MOZA_SDK\1.0.1.8\MSVC2022-64\example\CMakeLists.txt:6 (find_package): ...


Build started at 5:26 PM...
1>------ Skipped Build: Project: ConsoleApp1, Configuration: Release x64 ------
1>Project not selected to build for this solution configuration 
========== Build: 0 succeeded or up-to-date, 0 failed, 1 skipped ==========
========== Build completed at 5:26 PM and took 00.064 seconds ==========
