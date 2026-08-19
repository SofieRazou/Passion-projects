using mozaAPI;
using System.Diagnostics;
using System.Runtime.InteropServices;
using static mozaAPI.mozaAPI;

// P/Invoke to get the console window handle (HWND) without Windows Forms
[DllImport("kernel32.dll")]
static extern IntPtr GetConsoleWindow();

// Select which test to run:
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

    // Get the window handle for the current console window
    IntPtr hWnd = GetConsoleWindow();

    // Spring Force Test
    var force_mgr = createWheelbaseETSpring(hWnd, ref err);
    force_mgr.setDuration(0xffff);
    try
    {
        force_mgr.start();
        Console.WriteLine("Spring force effect started successfully.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"An unexpected error occurred: {ex.Message}");
    }

    // Keep it running long enough to feel the effect or test
    Thread.Sleep(5000);

    removeMozaSDK();
}

void MozaSteeringTest()
{ 
    Console.WriteLine("Starting Steering Test");
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
        var throttle = HIDDATA.throttle;
        var brake = HIDDATA.brake;
        Console.WriteLine($"Steering wheel angle: {wheelangle}");
        Console.WriteLine($"Throttle: {throttle}");
        Console.WriteLine($"Brake: {brake}");
        Console.SetCursorPosition(0, 0);
        Thread.Sleep(100);
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
    Console.WriteLine($"MOZA Switch device '{device.Path}' is opened.");

    while (device.IsConnected)
    {
        var currentSwitchValues = device.GetStateInfo(out var switcherror);
        var numSwitches = currentSwitchValues.Count;
        for (int i = 0; i <= numSwitches - 1; i++)
            if (currentSwitchValues[i] == 1)
            {
                Console.WriteLine($"Switch {i} = {currentSwitchValues[i]}");
            }
        Thread.Sleep(1000);
        Console.Clear();
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

    const float DEG_TO_RPM_PER_MIN = 60.0f / 360.0f;
    const float DT = 0.005f;
    const float CONSTANT_FORCE_MAX = 800;

    float pos_kp = 1.0f;
    float pos_ki = 0.0f;
    float spd_kp = 2.0f;
    float spd_ki = 200.0f;
    float spd_kd = 0.0f;

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

    // Get the console window handle without Windows Forms
    IntPtr hWnd = GetConsoleWindow();

    float target_pos = steeringWheelAngle;

    var constantForce = createWheelbaseETConstantForce(hWnd, ref err);

    if (constantForce == null)
    {
        Debug.WriteLine("no constantForce");
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
        Debug.WriteLine($"effect：{ex.Message}");
    }

    while (true)
    {
        var d = getHIDData(ref err);

        if (!float.IsNaN(d.fSteeringWheelAngle))
        {
            if (AreFloatsEqualWithinTolerance(d.fSteeringWheelAngle, steeringWheelAngle))
            {
                constantForce.setMagnitude(0);
                Thread.Sleep(5);
                break;
            }

            if (!flag)
            {
                pre_theta = d.fSteeringWheelAngle;
                flag = true;
            }
            float curr_pos = d.fSteeringWheelAngle;

            float delta_theta = curr_pos - pre_theta;
            float current_spd = delta_theta / DT * DEG_TO_RPM_PER_MIN;
            pre_theta = curr_pos;

            pos_error = target_pos - curr_pos;
            pos_err_integ += pos_error * DT * pos_ki;
            float spd_ref = pos_err_integ + pos_kp * pos_error;

            FloatLimit(ref spd_ref, (float)speed);

            spd_err = (spd_ref - current_spd);
            spd_err_integ += spd_err * DT * spd_ki;
            spd_derivative = (spd_err - spd_pre_err) / DT;
            float torque_ref = spd_err_integ + spd_err * spd_kp + spd_derivative * spd_kd;
            spd_pre_err = spd_err;
            float target_ref = -torque_ref;

            FloatLimit(ref target_ref, CONSTANT_FORCE_MAX);

            constantForce.setMagnitude((long)target_ref);

            Console.WriteLine($"error_pos:{pos_error} target_pos:{target_pos} current_spd:{current_spd} target_ref:{target_ref}.");
        }
    }

    void FloatLimit(ref float value, float limit)
    {
        if (value > limit) value = limit;
        if (value < -limit) value = -limit;
    }

    bool AreFloatsEqualWithinTolerance(float f1, float f2, float tolerance = 0.5f)
    {
        return Math.Abs(f1 - f2) < tolerance;
    }
}
