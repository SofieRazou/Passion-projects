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

// Run the live telemetry and physics loop
RunPhysicsTelemetryLoop();

Console.WriteLine("Program finished.");
return;

void RunPhysicsTelemetryLoop()
{ 
    Console.WriteLine("Starting Moza Physics & Telemetry Loop...");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    IntPtr hWnd = GetConsoleWindow();

    // Initialize a constant force effect for dynamic FFB updates
    var constantForce = createWheelbaseETConstantForce(hWnd, ref err);
    if (constantForce == null)
    {
        Console.WriteLine("Failed to create constant force effect.");
        removeMozaSDK();
        return;
    }

    constantForce.setDuration(0xffff);
    constantForce.setMagnitude(0);
    
    try
    {
        constantForce.start();
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Failed to start force effect: {ex.Message}");
    }

    var wheelangle = 0.0f;
    Console.Clear();

    while (true)
    {
        // 1. Read incoming hardware telemetry (steering angle, pedals)
        var HIDDATA = getHIDData(ref err);
        
        if (!float.IsNaN(HIDDATA.fSteeringWheelAngle))
        {
            wheelangle = HIDDATA.fSteeringWheelAngle;
        }

        var throttle = HIDDATA.throttle;
        var brake = HIDDATA.brake;

        // 2. Calculate your target torque force based on your physics logic (e.g., -800 to 800)
        float calculatedTorque = CalculateSteeringRackForce(wheelangle);

        // 3. Push that direct force command to the Moza hardware via effect magnitude
        constantForce.setMagnitude((long)calculatedTorque);

        // Display telemetry and commanded torque live on screen
        Console.WriteLine($"--- MOZA Physics & Telemetry ---");
        Console.WriteLine($"Steering Angle   : {wheelangle,6:F2}°     ");
        Console.WriteLine($"Throttle         : {throttle,6}        ");
        Console.WriteLine($"Brake            : {brake,6}           ");
        Console.WriteLine($"Calculated Torque: {calculatedTorque,6:F2}  ");
        
        // Reset cursor to the top line for real-time refreshing
        Console.SetCursorPosition(0, 0);
        Thread.Sleep(5); // ~200Hz physics loop tick rate
    }

    constantForce.setMagnitude(0);
    removeMozaSDK();
}

// Example placeholder for your custom physics/steering rack calculation
float CalculateSteeringRackForce(float currentAngle)
{
    // Example: simple centering spring force proportional to angle deviation
    float springCoeff = 2.0f;
    float targetTorque = -currentAngle * springCoeff;
    
    // Clamp to safe maximum limits
    if (targetTorque > 800) targetTorque = 800;
    if (targetTorque < -800) targetTorque = -800;
    
    return targetTorque;
}
