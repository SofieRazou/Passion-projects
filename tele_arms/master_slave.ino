// #include <Servo.h>

// // ---------------- Pins ----------------
// const int masterServoPin = 11;
// const int driverPin      = A0;   // potentiometer
// const int dirPin1        = 9;
// const int dirPin2        = 10;
// const int enPin          = 6;    // PWM pin for motor driver enable
// const int speedPin       = 2;    // interrupt pin on Arduino Uno

// // ---------------- Timing ----------------
// const float Ts = 0.02f;          // 20 ms control period in seconds
// unsigned long lastControlMs = 0;

// // ---------------- Servo ----------------
// Servo master;

// // ---------------- Sensor / encoder ----------------
// volatile long pulseCount = 0;
// long prevPulseCount = 0;
// const float pulsesPerRev = 20.0f;   // change to your disk's true pulses/rev
// const float degPerPulse  = 360.0f / pulsesPerRev;

// // ---------------- Controller gains ----------------
// float Kp = 2.0f;
// float Kd = 0.05f;

// // ---------------- System state ----------------
// struct State {
//   float thetaM;
//   float thetaS;
//   float omegaM;
//   float omegaS;

//   State() : thetaM(0), thetaS(0), omegaM(0), omegaS(0) {}

//   void setMaster(float theta, float omega) {
//     thetaM = theta;
//     omegaM = omega;
//   }

//   void setSlave(float theta, float omega) {
//     thetaS = theta;
//     omegaS = omega;
//   }
// };

// State sys;

// // ---------------- Utilities ----------------
// void countPulse() {
//   pulseCount++;
// }

// float omegaHat(float theta1, float theta0, float Ts_sec) {
//   return (theta1 - theta0) / Ts_sec;   // deg/s
// }

// float rpmFromDeltaPulses(long dPulses, float dtSec) {
//   float revs = (float)dPulses / pulsesPerRev;
//   return (revs / dtSec) * 60.0f;
// }

// void setSpeed(float u) {
//   int pwm = (int)constrain(abs(u), 0, 255);

//   if (u > 0) {
//     digitalWrite(dirPin1, HIGH);
//     digitalWrite(dirPin2, LOW);
//   } else if (u < 0) {
//     digitalWrite(dirPin1, LOW);
//     digitalWrite(dirPin2, HIGH);
//   } else {
//     digitalWrite(dirPin1, LOW);
//     digitalWrite(dirPin2, LOW);
//   }

//   analogWrite(enPin, pwm);
// }

// // ---------------- Master side ----------------
// void imposeMaster() {
//   static float prevThetaM = 0.0f;

//   int val = analogRead(driverPin);
//   float thetaM = map(val, 0, 1023, 0, 180);   // master angle in deg
//   float omegaM = omegaHat(thetaM, prevThetaM, Ts);

//   sys.setMaster(thetaM, omegaM);
//   prevThetaM = thetaM;

//   master.write((int)thetaM);   // servo follows master angle
// }

// // ---------------- Slave estimation ----------------
// void estimateSlave() {
//   noInterrupts();
//   long countNow = pulseCount;
//   interrupts();

//   long dCount = countNow - prevPulseCount;
//   prevPulseCount = countNow;

//   float omegaS_deg = (dCount * degPerPulse) / Ts;   // deg/s
//   float thetaS_deg = countNow * degPerPulse;        // total estimated angle

//   sys.setSlave(thetaS_deg, omegaS_deg);
// }

// // ---------------- Slave control ----------------
// void controlSlave() {
//   float eTheta = sys.thetaM - sys.thetaS;
//   float eOmega = sys.omegaM - sys.omegaS;

//   float u = Kp * eTheta + Kd * eOmega;

//   // optional clamp before motor
//   u = constrain(u, -255, 255); // from simulink saturation block inspo

//   setSpeed(u);
// }

// // ---------------- Debug ----------------
// void getLogs() {
//   float rpm = (sys.omegaS / 360.0f) * 60.0f;

//   Serial.print("thetaM: ");
//   Serial.print(sys.thetaM);
//   Serial.print(" deg, omegaM: ");
//   Serial.print(sys.omegaM);
//   Serial.print(" deg/s, thetaS: ");
//   Serial.print(sys.thetaS);
//   Serial.print(" deg, omegaS: ");
//   Serial.print(sys.omegaS);
//   Serial.print(" deg/s, RPM: ");
//   Serial.println(rpm);
// }

// void setup() {
//   master.attach(masterServoPin);

//   pinMode(driverPin, INPUT);
//   pinMode(speedPin, INPUT_PULLUP);
//   pinMode(enPin, OUTPUT);
//   pinMode(dirPin1, OUTPUT);
//   pinMode(dirPin2, OUTPUT);

//   Serial.begin(115200);

//   attachInterrupt(digitalPinToInterrupt(speedPin), countPulse, RISING);

//   lastControlMs = millis();

//   Serial.println("Serial communication with Arduino Uno established");
// }

// void loop() {
//   unsigned long now = millis();

//   if (now - lastControlMs >= (unsigned long)(Ts * 1000.0f)) {
//     lastControlMs = now;

//     imposeMaster();
//     estimateSlave();
//     controlSlave();
//     getLogs();
//   }
// }
#include <Servo.h>

// ---------------- Pins ----------------
const int masterServoPin = 11;
const int driverPin      = A0;   // potentiometer
const int dirPin1        = 9;
const int dirPin2        = 10;
const int enPin          = 6;    // PWM pin for motor driver enable
const int speedPin       = 2;    // interrupt pin on Arduino Uno

// ---------------- Timing ----------------
const float Ts = 0.02f;          // 20 ms control period in seconds
unsigned long lastControlMs = 0;

// ---------------- Servo ----------------
Servo master;

// ---------------- Sensor / encoder ----------------
volatile long pulseCount = 0;
long prevPulseCount = 0;
const float pulsesPerRev = 20.0f;   // change to your disk's true pulses/rev
const float degPerPulse  = 360.0f / pulsesPerRev;

// ---------------- Controller gains ----------------
float Kp = 2.0f;
float Kd = 0.05f;

// ---------------- Safety limits ----------------
const float slaveThetaMin = 0.0f;      // deg
const float slaveThetaMax = 180.0f;    // deg
const float slaveOmegaMax = 300.0f;    // deg/s, tune as needed
const int   pwmMax        = 50;       // softer than full 255
const float uDeadband     = 8.0f;      // small dead zone

// ---------------- System state ----------------
struct State {
  float thetaM;
  float thetaS;
  float omegaM;
  float omegaS;

  State() : thetaM(0), thetaS(0), omegaM(0), omegaS(0) {}

  void setMaster(float theta, float omega) {
    thetaM = theta;
    omegaM = omega;
  }

  void setSlave(float theta, float omega) {
    thetaS = theta;
    omegaS = omega;
  }
};

State sys;

// ---------------- Utilities ----------------
void countPulse() {
  pulseCount++;
}

float omegaHat(float theta1, float theta0, float Ts_sec) {
  return (theta1 - theta0) / Ts_sec;   // deg/s
}

float rpmFromDeltaPulses(long dPulses, float dtSec) {
  float revs = (float)dPulses / pulsesPerRev;
  return (revs / dtSec) * 60.0f;
}

void stopMotor() {
  digitalWrite(dirPin1, LOW);
  digitalWrite(dirPin2, LOW);
  analogWrite(enPin, 0);
}

void setSpeed(float u) {
  // hard limit on command magnitude
  int pwm = (int)constrain(abs(u), 0, pwmMax);

  // deadband to avoid twitching
  if (abs(u) < uDeadband) {
    stopMotor();
    return;
  }

  if (u > 0) {
    digitalWrite(dirPin1, HIGH);
    digitalWrite(dirPin2, LOW);
  } else {
    digitalWrite(dirPin1, LOW);
    digitalWrite(dirPin2, HIGH);
  }

  analogWrite(enPin, pwm);
}

// ---------------- Master side ----------------
void imposeMaster() {
  static float prevThetaM = 0.0f;

  int val = analogRead(driverPin);
  float thetaM = map(val, 0, 1023, 0, 180);   // master angle in deg
  float omegaM = omegaHat(thetaM, prevThetaM, Ts);

  sys.setMaster(thetaM, omegaM);
  prevThetaM = thetaM;

  master.write((int)thetaM);   // servo follows master angle
}

// ---------------- Slave estimation ----------------
void estimateSlave() {
  noInterrupts();
  long countNow = pulseCount;
  interrupts();

  long dCount = countNow - prevPulseCount;
  prevPulseCount = countNow;

  float omegaS_deg = (dCount * degPerPulse) / Ts;   // deg/s
  float thetaS_deg = countNow * degPerPulse;        // total estimated angle

  sys.setSlave(thetaS_deg, omegaS_deg);
}

// ---------------- Slave control ----------------
void controlSlave() {
  float eTheta = sys.thetaM - sys.thetaS;
  float eOmega = sys.omegaM - sys.omegaS;

  float u = Kp * eTheta + Kd * eOmega;

  // -------- speed protection --------
  if (sys.omegaS > slaveOmegaMax && u > 0) {
    u = 0;
  }
  if (sys.omegaS < -slaveOmegaMax && u < 0) {
    u = 0;
  }

  // -------- position protection --------
  // If slave is at upper angle limit and command wants to increase angle, stop it
  if (sys.thetaS >= slaveThetaMax && u > 0) {
    u = 0;
  }

  // If slave is at lower angle limit and command wants to decrease angle, stop it
  if (sys.thetaS <= slaveThetaMin && u < 0) {
    u = 0;
  }

  // final saturation
  u = constrain(u, -pwmMax, pwmMax);

  setSpeed(u);
}

// ---------------- Debug ----------------
void getLogs() {
  float rpm = (sys.omegaS / 360.0f) * 60.0f;

  Serial.print("thetaM: ");
  Serial.print(sys.thetaM);
  Serial.print(" deg, omegaM: ");
  Serial.print(sys.omegaM);
  Serial.print(" deg/s, thetaS: ");
  Serial.print(sys.thetaS);
  Serial.print(" deg, omegaS: ");
  Serial.print(sys.omegaS);
  Serial.print(" deg/s, RPM: ");
  Serial.println(rpm);
}

void setup() {
  master.attach(masterServoPin);

  pinMode(driverPin, INPUT);
  pinMode(speedPin, INPUT_PULLUP);
  pinMode(enPin, OUTPUT);
  pinMode(dirPin1, OUTPUT);
  pinMode(dirPin2, OUTPUT);

  Serial.begin(115200);

  attachInterrupt(digitalPinToInterrupt(speedPin), countPulse, RISING);

  lastControlMs = millis();

  Serial.println("Serial communication with Arduino Uno established");
}

void loop() {
  unsigned long now = millis();

  if (now - lastControlMs >= (unsigned long)(Ts * 1000.0f)) {
    lastControlMs = now;

    imposeMaster();
    estimateSlave();
    controlSlave();
    getLogs();
  }
}
