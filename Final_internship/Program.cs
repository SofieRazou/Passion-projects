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

RunInertiaTorqueLoop();

Console.WriteLine("Program finished.");
return;

void RunInertiaTorqueLoop()
{ 
    Console.WriteLine("Starting Moza Inertia-Based Torque Loop...");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    IntPtr hWnd = GetConsoleWindow();

    var constantForce = createWheelbaseETConstantForce(hWnd, ref err);
    if (constantForce == null)
    {
        Console.WriteLine("Failed to create constant force effect.");
        removeMozaSDK();
        return;
    }

    constantForce.setDuration(0xffff);
    constantForce.setMagnitude(0);
    constantForce.start();

    // Physics tracking variables
    float previousAngle = 0.0f;
    float previousVelocity = 0.0f;
    DateTime lastTime = DateTime.Now;
    
    // Constants for your physics model
    const float inertia = 0.0007f;
    const float damping = 0.01f;
    const float springCoeff = 1.5f;

    Console.Clear();

    while (true)
    {
        var HIDDATA = getHIDData(ref err);
        
        if (!float.IsNaN(HIDDATA.fSteeringWheelAngle))
        {
            float currentAngle = HIDDATA.fSteeringWheelAngle;
            
            DateTime now = DateTime.Now;
            float deltaTime = (float)(now - lastTime).TotalSeconds;
            
            if (deltaTime > 0)
            {
                // 1. Derive Kinematics
                float currentVelocity = (currentAngle - previousAngle) / deltaTime;
                float currentAcceleration = (currentVelocity - previousVelocity) / deltaTime;
                
                // 2. Calculate Torque using Inertia, Damping, and Spring forces
                // Torque = (I * alpha) + (damping * velocity) + (spring * angle)
                float calculatedTorque = (inertia * currentAcceleration) 
                                       + (damping * currentVelocity) 
                                       + (springCoeff * currentAngle);

                // Scale/clamp to safe motor command limits (adjust multiplier as needed for feel)
                float finalMagnitude = calculatedTorque * 100.0f;
                if (finalMagnitude > 800) finalMagnitude = 800;
                if (finalMagnitude < -800) finalMagnitude = -800;

                // 3. Command the hardware
                constantForce.setMagnitude((long)finalMagnitude);

                // Update tracking states
                previousAngle = currentAngle;
                previousVelocity = currentVelocity;
                lastTime = now;

                // Display live data
                Console.WriteLine($"--- MOZA Physics Engine ---");
                Console.WriteLine($"Angle         : {currentAngle,6:F2}°     ");
                Console.WriteLine($"Velocity      : {currentVelocity,6:F2} °/s  ");
                Console.WriteLine($"Acceleration  : {currentAcceleration,6:F2} °/s²");
                Console.WriteLine($"Torque Cmd    : {finalMagnitude,6:F2} Nm   ");
                
                Console.SetCursorPosition(0, 0);
            }
        }
        
        Thread.Sleep(5); // ~200Hz loop tick rate
    }

    constantForce.setMagnitude(0);
    removeMozaSDK();
}
