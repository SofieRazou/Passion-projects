// using mozaAPI;
// using System.Diagnostics;
// using System.Runtime.InteropServices;
// using static mozaAPI.mozaAPI;

// // P/Invoke to get the console window handle (HWND) without Windows Forms
// [DllImport("kernel32.dll")]
// static extern IntPtr GetConsoleWindow();

// // Run only the live steering angle telemetry loop
// MozaSteeringTest();

// Console.WriteLine("Program finished.");
// return;

// void MozaSteeringTest()
// { 
//     Console.WriteLine("Starting Live Steering Angle Telemetry...");
//     installMozaSDK();
//     ERRORCODE err = ERRORCODE.NORMAL;

//     var wheelangle = 0.0;
//     Console.Clear();

//     while (true)
//     {
//         var HIDDATA = getHIDData(ref err);
//         var Sampledwheelangle = HIDDATA.fSteeringWheelAngle;
        
//         if (!float.IsNaN(Sampledwheelangle))
//         {
//             wheelangle = Sampledwheelangle;
//         }

//         // Display only the encoder angle live on screen
//         Console.WriteLine($"Live Steering Wheel Angle: {wheelangle:F2}°     ");
        
//         // Reset cursor to the top line for a clean real-time display effect
//         Console.SetCursorPosition(0, 0);
//         Thread.Sleep(50); // Small delay to avoid hammering CPU
//     }

//     removeMozaSDK();
// }
using mozaAPI;
using System.Diagnostics;
using System.Runtime.InteropServices;
using static mozaAPI.mozaAPI;

[DllImport("kernel32.dll")]
static extern IntPtr GetConsoleWindow();

// Run the live telemetry stream
MozaLiveTelemetryTest();

Console.WriteLine("Program finished.");
return;

void MozaLiveTelemetryTest()
{ 
    Console.WriteLine("Starting Live Telemetry Stream...");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    IntPtr hWnd = GetConsoleWindow();

    var wheelangle = 0.0f;
    Console.Clear();

    // Variable to track your target or commanded torque locally
    float commandedTorque = 0.0f;

    while (true)
    {
        var HIDDATA = getHIDData(ref err);
        
        // Update steering angle if valid
        if (!float.IsNaN(HIDDATA.fSteeringWheelAngle))
        {
            wheelangle = HIDDATA.fSteeringWheelAngle;
        }

        var throttle = HIDDATA.throttle;
        var brake = HIDDATA.brake;

        // Display valid telemetry and your tracked torque value live on screen
        Console.WriteLine($"--- MOZA Live Telemetry ---");
        Console.WriteLine($"Steering Angle   : {wheelangle,6:F2}°     ");
        Console.WriteLine($"Throttle         : {throttle,6}        ");
        Console.WriteLine($"Brake            : {brake,6}           ");
        Console.WriteLine($"Commanded Torque : {commandedTorque,6:F2}  ");
        
        // Reset cursor to the top line for a smooth real-time refresh effect
        Console.SetCursorPosition(0, 0);
        Thread.Sleep(50); 
    }

    removeMozaSDK();
}
