using System;
using System.Threading;

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("Initializing Moza SDK...");

        // Note: Actual method names depend on the Moza C# wrapper classes/namespaces provided in the SDK.
        // Typically, you'll call an initialization function like this:
        // MozaAPI.Init();

        while (true)
        {
            // TODO: Call telemetry data retrieval functions provided by MOZA_API_CSharp.dll
            // e.g., var telemetry = MozaAPI.GetTelemetryData();
            // Console.WriteLine($"Current Torque: {telemetry.Torque}");

            Thread.Sleep(100); // Poll every 100ms
        }
    }
}
