using mozaAPI;
using System.Diagnostics;
using System.Runtime.InteropServices;
using static mozaAPI.mozaAPI;

// P/Invoke to get the console window handle (HWND) without Windows Forms
[DllImport("kernel32.dll")]
static extern IntPtr GetConsoleWindow();

// Run only the live steering angle telemetry loop
MozaSteeringTest();

Console.WriteLine("Program finished.");
return;

void MozaSteeringTest()
{ 
    Console.WriteLine("Starting Live Steering Angle Telemetry...");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    var wheelangle = 0.0;
    Console.Clear();

    while (true)
    {
        var HIDDATA = getHIDData(ref err);
        var Sampledwheelangle = HIDDATA.fSteeringWheelAngle;
        
        if (!float.IsNaN(Sampledwheelangle))
        {
            wheelangle = Sampledwheelangle;
        }

        // Display only the encoder angle live on screen
        Console.WriteLine($"Live Steering Wheel Angle: {wheelangle:F2}°     ");
        
        // Reset cursor to the top line for a clean real-time display effect
        Console.SetCursorPosition(0, 0);
        Thread.Sleep(50); // Small delay to avoid hammering CPU
    }

    removeMozaSDK();
}
