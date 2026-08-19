using mozaAPI;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms; 
using static mozaAPI.mozaAPI;

// Call the steering test here so it actually runs!
MozaSteeringTest();

Console.WriteLine("Program finished.");
return; // Any code placed AFTER this return line is unreachable
