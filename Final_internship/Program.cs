/*************************************************************************************
 * This file is an example code on how to use MOZA Shifter device-related interfaces with MOZA SDK C#
 *
 * For other APIs in MOZA SDK, please refer to the example code file `sdk_api_test.cc` in the MOZA SDK C++ version.
 * You can also refer to the API documentation of the C++ version, located at `docsEng/index.html`.
 * The API in the MOZA SDK C# version is almost identical to the C++ version in terms of function names and input parameters.
*************************************************************************************/


using mozaAPI;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms; // Windows Forms can be used to get a valid window handle (HWND)
using static mozaAPI.mozaAPI;


//MozaShifterTest();
//MozaSwitchTest();
//MozaSteeringTest();
ffb_test();
//MoveTo(90, 100);
Console.WriteLine("Program finished.");
return;


void ffb_test()
{
    Console.WriteLine("Starting FFB Test");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    // In C#, we use a Form/Control to get a valid HWND (Window Handle)
    Form dummyForm = new Form();
    dummyForm.Show();
    IntPtr hWnd = dummyForm.Handle;

    // Spring Force Test
    var force_mgr = createWheelbaseETSpring(hWnd, ref err);
    force_mgr.setDuration(0xffff);
    //force_mgr.setDuration(1000);
    try
    {
        force_mgr.start();
    }
    catch (Exception ex)
    {
        // Handle any other unexpected exceptions
        Console.WriteLine($"An unexpected error occurred: {ex.Message}");
    }


    /*
    // Constant Force Test
    var force_mgr = createWheelbaseETConstantForce(hWnd, ref err);
    force_mgr.setMagnitude(100);
    force_mgr.setDuration(10000);
    try
    {
        force_mgr.start();
    }
    catch (Exception ex)
    {
        // Handle any other unexpected exceptions
        Console.WriteLine($"An unexpected error occurred: {ex.Message}");
    }
    */

    removeMozaSDK();
}

void MozaSteeringTest()
{ 
    Console.WriteLine("Starting Steering Test");
    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;

    var wheelangle = 0.0;
    Console.Clear(); // Clears the console  

    while (true)
    {
        var HIDDATA = getHIDData(ref err);
        var Sampledwheelangle = HIDDATA.fSteeringWheelAngle;
        if (!float.IsNaN(Sampledwheelangle))
        {
            wheelangle = Sampledwheelangle;
        }
        var throttle = HIDDATA.throttle;
        var brake = HIDDATA.brake;
        Console.WriteLine($"Steering wheel angle: {wheelangle}");
        Console.WriteLine($"Throttle: {throttle}");
        Console.WriteLine($"Brake: {brake}");
        //Thread.Sleep(100);
        //Console.Clear(); // Clears the console
        Console.SetCursorPosition(0, 0);
    }

    removeMozaSDK();
}

void MozaSwitchTest()
{
    Console.WriteLine("Starting Switch Test");
    var devices = EnumSwitchesDevices(out var error);
    if (error != ERRORCODE.NORMAL || devices.Count == 0)
    {
        Console.WriteLine($"No MOZA Switch device found, error = {error}");
        return;
    }
    var device = devices[0];
    if (!device.Open())
    {
        Console.WriteLine("Device open failed.");
        return;
    }
    Console.WriteLine($"MOZA Stitch device '{device.Path}' is opened.");

    while (device.IsConnected)
    {
        var currentSwitchValues = device.GetStateInfo(out var switcherror);
        var numSwitches = currentSwitchValues.Count;
        //Console.WriteLine($"current Switch count {numSwitches}");
        for (int i = 0; i <= numSwitches-1; i++)
            if (currentSwitchValues[i] == 1)
            {
                Console.WriteLine($"Switch {i} = {currentSwitchValues[i]}");
            }
        Thread.Sleep(1000);
        Console.Clear(); // Clears the console  

    }
}

void MozaShifterTest()
{
    var devices = EnumShifterDevices(out var error);
    if (error != ERRORCODE.NORMAL || devices.Count == 0)
    {
        Console.WriteLine($"No MOZA Shifter device found, error = {error}");
        return;
    }

    var device = devices[0];
    if (!device.Open())
    {
        Console.WriteLine("Device open failed.");
        return;
    }

    Console.WriteLine($"MOZA Shifter device '{device.Path}' is opened.");

    var gear = 0;
    while (device.IsConnected)
    {
        // The `GetCurrentGear` function waits for the HID report while reading data, until valid data is received or an error occurs.
        // This means the execution time of this function may be relatively long, and it is not recommended to call it in the main thread.
        var currentGear = device.GetCurrentGear();
        if (gear == currentGear) continue;
        Console.WriteLine($"The gear has been switched from {gear} to {currentGear}");
        gear = currentGear;
    }

    Console.WriteLine("The device has been disconnected.");
}

void MoveTo(short steeringWheelAngle, short speed)
{
    Console.WriteLine("Running MoveTo.");

    // Define necessary constants used in the original C++ code
    const float DEG_TO_RPM_PER_MIN = 60 / 360; // Simplified constant, adjust as needed
    const float DT = 0.005f; // 5ms delay in loop
    const float CONSTANT_FORCE_MAX = 800; // Placeholder value


    // R9
    //float spd_kp = 2.0f;
    //float spd_ki = 200.f;

    // R16
    //float spd_kp = 2.0f;
    //float spd_ki = 40.0f;

    // R12
    // PID constants
    float pos_kp = 1.0f;
    float pos_ki = 0.0f;
    float spd_kp = 2.0f;
    float spd_ki = 200.0f;
    float spd_kd = 0.0f;

    // State variables
    bool flag = false;
    float pre_theta = 0.0f;
    float pos_error = 0.0f;
    float pos_err_integ = 0.0f;
    float spd_err = 0.0f;
    float spd_err_integ = 0.0f;
    float spd_derivative = 0.0f;
    float spd_pre_err = 0.0f;

    installMozaSDK();
    ERRORCODE err = ERRORCODE.NORMAL;
    // In C#, we use a Form/Control to get a valid HWND (Window Handle)
    Form dummyForm = new Form();
    dummyForm.Show();
    IntPtr hWnd = dummyForm.Handle;

    float target_pos = steeringWheelAngle;

    var constantForce = createWheelbaseETConstantForce(hWnd, ref err);

    if (constantForce == null)
    {
        Debug.WriteLine("no constantForce");
        dummyForm.Close(); // Clean up dummy form
        return;
    }

    //Thread.Sleep(500);

    constantForce.setDuration(0xffff);
    constantForce.setMagnitude(0);
    try
    {
        constantForce.start();
    }
    catch (Exception ex)
    {
        Debug.WriteLine($"effect：{ex.Message}");
    }

    while (true)
    {
        // \Getting HID data struct
        var d = getHIDData(ref err);

        // Check if data is valid
        if (!float.IsNaN(d.fSteeringWheelAngle))
        {
            if (AreFloatsEqualWithinTolerance(d.fSteeringWheelAngle, steeringWheelAngle))
            {
                constantForce.setMagnitude(0);
                Thread.Sleep(5);
                break; // Exit the while loop
            }

            if (!flag)
            {
                pre_theta = d.fSteeringWheelAngle;
                flag = true;
            }
            float curr_pos = d.fSteeringWheelAngle;

            // PID Calculations (Direct port of C++ logic)
            float delta_theta = curr_pos - pre_theta;
            float current_spd = delta_theta / DT * DEG_TO_RPM_PER_MIN;
            pre_theta = curr_pos;

            // Position control
            pos_error = target_pos - curr_pos;
            pos_err_integ += pos_error * DT * pos_ki;
            float spd_ref = pos_err_integ + pos_kp * pos_error;

            FloatLimit(ref spd_ref, (float)speed);

            // Speed loop control
            spd_err = (spd_ref - current_spd);
            spd_err_integ += spd_err * DT * spd_ki;
            spd_derivative = (spd_err - spd_pre_err) / DT;
            float torque_ref = spd_err_integ + spd_err * spd_kp + spd_derivative * spd_kd;
            spd_pre_err = spd_err;
            float target_ref = -torque_ref;

            FloatLimit(ref target_ref, CONSTANT_FORCE_MAX);

            constantForce.setMagnitude((long)target_ref);

            // Console logging equivalent
            Console.WriteLine($"error_pos:{pos_error} target_pos:{target_pos} current_spd:{current_spd} target_ref:{target_ref}.");
        }
        //Thread.Sleep(5);
    }


    // Helper method to limit a float value
    void FloatLimit(ref float value, float limit)
    {
        if (value > limit) value = limit;
        if (value < -limit) value = -limit;
    }

    // Helper method to compare floats with a tolerance
    bool AreFloatsEqualWithinTolerance(float f1, float f2, float tolerance = 0.5f)
    {
        return Math.Abs(f1 - f2) < tolerance;
    }
}
