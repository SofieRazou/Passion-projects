using mozaAPI;
using static mozaAPI.mozaAPI;

class Program
{
    static void Main(string[] args)
    {
        // 1. Initialize the SDK
        installMozaSDK();
        Console.WriteLine("Moza SDK Initialized. Press Ctrl+C to exit.");

        try
        {
            // 2. Simple loop to keep the console alive and read telemetry/status
            while (true)
            {
                // Add your telemetry polling or effect updates here
                Thread.Sleep(100); 
            }
        }
        finally
        {
            // 3. Clean up on exit
            removeMozaSDK();
        }
    }
}
