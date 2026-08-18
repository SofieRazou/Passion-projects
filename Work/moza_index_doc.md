
    Environment setup:
    This SDK library is a 32-bit library
    Load MOZA_SDK. lib
    Contains mozaAPI. h header file
    Install MOZA Pit House (SDK version)

    2 Interface usage:
    The first step is to call installMozaSDK() to load the sdk before using other functional interfaces of the sdk. Otherwise, an error code prompt will be returned. If you want to remove the sdk, you can call removeMozaSDK().

    2.1 The devices that can set and obtain parameters are divided into:
    Motor motor; SteeringWheel; DisplayScreen; Pedal pedal; Handbrake
    Obtain/set the parameters of the device separately through get/set (e.g. getMotorLimitAngle)
    The use of the calibration interface is to first call the start calibration interface, wait for the calibration to be completed, and then call the end calibration interface to complete the calibration:
    Pedal clutch calibration: ClutchCalibrateStrat(); Press and fully release the clutch pedal; ClutchCalibrateFinish()
    Pedal and accelerator calibration: AccCalibrateStrat(); Complete pressing and fully releasing the accelerator pedal; AccCalibrateFinish()
    Pedal brake calibration: BrakeCalibrateStrat(); Complete pressing and fully releasing the brake pedal; BrakeCalibrateFinish()
    Hand brake calibration: HandbrakeCalibrateStart(); Press and fully release the handbrake; HandrakeCalibrateFinish()
    Shifter calibration: ShiftCalibrateStart(); Press the gear lever and move it back and forth from the left to the right (note that there is no need to shift into any gear); ShiftCalibrateFinish()

    2.2 The types of force feedback include:
    ConstantFore; Damper; Friction; Inertia; Sine; Spring
    Create them separately through createWheelbaseETXXX, for example (createWheelbaseETConstantFore), return as the manager of the force, set the parameters of the force through the manager, and initiate force feedback through the start() function

    2.3 HID:
    Obtain HID data for this cycle through getHIDData
    Starting the SDK to calling the getHIDData interface is a cycle, with the previous call to getHIDData and the subsequent call to getHIDData being a cycle. Long cycles may cause data loss when the HID ring cache is full. The interface can be used to obtain data loss through error codes.
    The value of the axis is the status value of the last getHIDData;
    HIDButton records the initial state and number of changes during a cycle, which can be obtained through functions such as whether to press (isPressed()), the last press state (lastPressState()), the number of presses (pressNum()), or custom functions to obtain information
    The buttons [128] correspond to 128 key values, and their corresponding numbers correspond to the steering wheel key numbers.
    HIDRocker, HIDKnob, HIDMultiSegmentKnob all record operations within a cycle 
