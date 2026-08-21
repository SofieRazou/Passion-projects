using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
using static mozaAPI.mozaAPI;

class Program
{
    [DllImport("kernel32.dll")]
    static extern IntPtr GetConsoleWindow();

    static void Main(string[] args)
    {
        // Run the live telemetry and physics loop
        RunPhysicsTelemetryLoop();

        Console.WriteLine("Program finished.");
    }

    static void RunPhysicsTelemetryLoop()
    {
        Console.WriteLine("Starting Moza Physics & Telemetry Loop...");
        installMozaSDK();
        ERRORCODE err = ERRORCODE.NORMAL;

        IntPtr hWnd = GetConsoleWindow();

        var wheelangle = 0.0f;
        var wheelvel = 0.0f;
        var wheelaccel = 0.0f;
        
        string csvFilePath = "moza_telemetry_log.csv";
        Stopwatch sw = Stopwatch.StartNew();

        // Using a try-finally block guarantees removeMozaSDK() is called upon exit
        try
        {
            using (StreamWriter writer = new StreamWriter(csvFilePath, false))
            {
                // Write the CSV Header
                writer.WriteLine("Time_s,SteeringAngle_deg,Velocity_deg_s,Acceleration_deg_s2,Inertia_pct,InertiaRatio_pct,SpringStrength,Throttle,Brake");

                Console.Clear();

                while (true)
                {
                    // Allow breaking the loop gracefully if a key is pressed (e.g., ESC or Q)
                    if (Console.KeyAvailable)
                    {
                        var key = Console.ReadKey(true);
                        if (key.Key == ConsoleKey.Q || key.Key == ConsoleKey.Escape)
                        {
                            break;
                        }
                    }

                    var HIDDATA = getHIDData(ref err);
                    
                    if (!float.IsNaN(HIDDATA.fSteeringWheelAngle))
                    {
                        wheelangle = HIDDATA.fSteeringWheelAngle;      
                    }
                    if (!float.IsNaN(HIDDATA.fSteeringWheelVelocity))
                    {
                        wheelvel = HIDDATA.fSteeringWheelVelocity;      
                    }  
                    if (!float.IsNaN(HIDDATA.fSteeringWheelAcceleration))
                    {
                        wheelaccel = HIDDATA.fSteeringWheelAcceleration;      
                    }
                
                    var NaturalInertia = getMotorNaturalInertia(ref err);
                    var inertRatio = getMotorNaturalInertiaRatio(ref err);
                    var spring = getMotorSpringStrength(ref err);
                    
                    var throttle = HIDDATA.throttle;
                    var brake = HIDDATA.brake;
                    
                    double currentTime = sw.Elapsed.TotalSeconds;

                    // Write telemetry row to the CSV file
                    writer.WriteLine($"{currentTime:F4},{wheelangle:F4},{wheelvel:F4},{wheelaccel:F4},{NaturalInertia:F4},{inertRatio:F4},{spring:F4},{throttle},{brake}");

                    // Display telemetry live on screen
                    Console.WriteLine($"--- MOZA Physics & Telemetry ---");
                    Console.WriteLine($"Logging to            : {csvFilePath}");
                    Console.WriteLine($"Press 'Q' or 'ESC' to exit safely.          ");
                    Console.WriteLine($"Steering Angle        : {wheelangle,6:F2}°     ");
                    Console.WriteLine($"Natural Inertia       : {NaturalInertia,6:F2}%     ");
                    Console.WriteLine($"Natural Inertia ratio : {inertRatio,6:F2}%     ");
                    Console.WriteLine($"Spring strength       : {spring,6:F2}        ");
                    Console.WriteLine($"Steering Velocity     : {wheelvel,6:F2}°/s   ");
                    Console.WriteLine($"Steering Acceleration : {wheelaccel,6:F2}°/s²  ");
                    Console.WriteLine($"Throttle              : {throttle,6}        ");
                    Console.WriteLine($"Brake                 : {brake,6}          ");
           
                    Console.SetCursorPosition(0, 0);
                    Thread.Sleep(5); // ~200Hz physics loop tick rate
                }
            }
        }
        finally
        {
            // This code block always runs, ensuring proper SDK cleanup
            Console.Clear();
            Console.WriteLine("Cleaning up and removing Moza SDK...");
            removeMozaSDK();
        }
    }
}
// Example placeholder for your custom physics/steering rack calculation
// float CalculateSteeringRackForce(float currentAngle, float pastAngle = 0.0f, float deltaTime = 0.005f)
// {
//     // Example: simple centering spring force proportional to angle deviation
//     float J = 0.0007f; // hypothetical moment of inertia
    
//     return wheelvel;
// }


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

    var wheelangle = 0.0f;
    var  wheelvel = 0.0f;
    var  wheelaccel = 0.0f;
    var wheeltor = 0.0f;
    Console.Clear();

    while (true)
    {
        // 1. Read incoming hardware telemetry (steering angle, pedals)
        var HIDDATA = getHIDData(ref err);
        
        if (!float.IsNaN(HIDDATA.fSteeringWheelAngle))
        {
            wheelangle = HIDDATA.fSteeringWheelAngle;       
        }
        if (!float.IsNaN(HIDDATA.fSteeringWheelVelocity))
        {
            wheelvel = HIDDATA.fSteeringWheelVelocity;       
        }  
        if (!float.IsNaN(HIDDATA.fSteeringWheelAcceleration))
        {
            wheelaccel = HIDDATA.fSteeringWheelAcceleration;       
        }
    
        var NaturalInertia = getMotorNaturalInertia(err);

        var throttle = HIDDATA.throttle;
        var brake = HIDDATA.brake;


        // Display telemetry and commanded torque live on screen
        Console.WriteLine($"--- MOZA Physics & Telemetry ---");
        Console.WriteLine($"Steering Angle   : {wheelangle,6:F2}°     ");
        Console.WriteLine($"Natural Inertia  : {NaturalInertia,6:F2}°     ");
        Console.WriteLine($"Steering Velocity : {wheelvel,6:F2}°/s   ");
        Console.WriteLine($"Steering Acceleration : {wheelaccel,6:F2}°/s²   ");
        Console.WriteLine($"Throttle         : {throttle,6}        ");
        Console.WriteLine($"Brake            : {brake,6}           ");
   
    
        // Reset cursor to the top line for real-time refreshing
        Console.SetCursorPosition(0, 0);
        Thread.Sleep(5); // ~200Hz physics loop tick rate
    }
    removeMozaSDK();
}

// Example placeholder for your custom physics/steering rack calculation
// float CalculateSteeringRackForce(float currentAngle, float pastAngle = 0.0f, float deltaTime = 0.005f)
// {
//     // Example: simple centering spring force proportional to angle deviation
//     float J = 0.0007f; // hypothetical moment of inertia
    
//     return wheelvel;
// }
