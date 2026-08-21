def _create_plot(self, title: str, y_label: str, color: str) -> pg.PlotWidget:
        """Helper to create and style a standard PyQtGraph plot widget."""
        plot = pg.PlotWidget(title=f"<span style='color:#ffffff; font-size:12pt;'>{title}</span>")
        plot.setBackground("#181b22")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel("bottom", "Time (s)", color="#9ca3af")
        plot.setLabel("left", y_label, color="#9ca3af")
        
        # Link X-axis zooming across all plots for easy synchronous scrolling
        if hasattr(self, "plot_angle"):
            plot.setXLink(self.plot_angle)
            
        return plot

    def load_telemetry_csv(self):
        """Open a file dialog to load and render saved telemetry CSV data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Moza Telemetry CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        # Load CSV into Pandas DataFrame
        df = pd.read_csv(file_path)

        if "Timestamp" not in df.columns:
            return

        time = df["Timestamp"].values

        # 1. Plot Steering Angle
        self.plot_angle.clear()
        if "Angle_deg" in df.columns:
            self.plot_angle.plot(time, df["Angle_deg"].values, pen=pg.mkPen("#00d2ff", width=2))

        # 2. Plot Velocity
        self.plot_vel.clear()
        if "Velocity_deg_s" in df.columns:
            self.plot_vel.plot(time, df["Velocity_deg_s"].values, pen=pg.mkPen("#10b981", width=2))

        # 3. Plot Acceleration
        self.plot_acc.clear()
        if "Acceleration_deg_s2" in df.columns:
            self.plot_acc.plot(time, df["Acceleration_deg_s2"].values, pen=pg.mkPen("#ef4444", width=2))

        # 4. Plot Torque / Spring Strength
        self.plot_torque.clear()
        if "SpringStrength" in df.columns:
            self.plot_torque.plot(time, df["SpringStrength"].values, pen=pg.mkPen("#f59e0b", width=2))






using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using static mozaAPI.mozaAPI;

class Program
{
    [DllImport("kernel32.dll")]
    static extern IntPtr GetConsoleWindow();

    static void Main(string[] args)
    {
        Console.WriteLine("Starting Moza Physics & Telemetry Loop...");
        installMozaSDK();

        IntPtr hWnd = GetConsoleWindow();

        float wheelangle = 0.0f;
        float wheelvel = 0.0f;
        float wheelaccel = 0.0f;
        
        // Create a unique CSV filename based on the current timestamp
        string csvFileName = $"moza_telemetry_{DateTime.Now:yyyyMMdd_HHmmss}.csv";

        // Initialize the StreamWriter with AutoFlush enabled to prevent data loss
        using (StreamWriter writer = new StreamWriter(csvFileName, append: false))
        {
            writer.AutoFlush = true;

            // Write the CSV header row
            writer.WriteLine("Timestamp,Angle_deg,Velocity_deg_s,Acceleration_deg_s2,NaturalInertia_pct,InertiaRatio_pct,SpringStrength,Throttle,Brake");

            Console.Clear();

            Stopwatch stopwatch = Stopwatch.StartNew();

            while (true)
            {
                // Use default enum value to match the exact SDK expected reference type
                mozaAPI.ERRORCODE errCode = default;

                // 1. Read incoming hardware telemetry
                var HIDDATA = getHIDData(ref errCode);
                
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
            
                var NaturalInertia = getMotorNaturalInertia(ref errCode);
                var inertRatio = getMotorNaturalInertiaRatio(ref errCode);
                var spring = getMotorSpringStrength(ref errCode);
                
                var throttle = HIDDATA.throttle;
                var brake = HIDDATA.brake;

                // Get elapsed time in seconds since loop started
                double timestamp = stopwatch.Elapsed.TotalSeconds;

                // Write current telemetry frame to the CSV file
                writer.WriteLine($"{timestamp:F4},{wheelangle},{wheelvel},{wheelaccel},{NaturalInertia},{inertRatio},{spring},{throttle},{brake}");

                // Display telemetry live on screen
                Console.SetCursorPosition(0, 0);
                Console.WriteLine("--- MOZA Physics & Telemetry ---");
                Console.WriteLine($"File Saving To        : {csvFileName}     ");
                Console.WriteLine($"Steering Angle        : {wheelangle,6:F2}°     ");
                Console.WriteLine($"Natural Inertia       : {NaturalInertia,6:F2}%     ");
                Console.WriteLine($"Natural Inertia ratio : {inertRatio,6:F2}%     ");
                Console.WriteLine($"Spring strength       : {spring,6:F2}        ");
                Console.WriteLine($"Steering Velocity     : {wheelvel,6:F2}°/s   ");
                Console.WriteLine($"Steering Acceleration : {wheelaccel,6:F2}°/s²  ");
                Console.WriteLine($"Throttle              : {throttle,6}        ");
                Console.WriteLine($"Brake                 : {brake,6}          ");
       
                Thread.Sleep(5); // ~200Hz physics loop tick rate
            }
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
