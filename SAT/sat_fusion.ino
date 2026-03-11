// #include "sat_by_markov.hpp"
// #include <Servo.h>
// #include <Wire.h>
// #include <MPU6050.h>
// #include <ArduinoQueue.h>
// #include <Vector.h>
// #include <math.h>

// using sat = MChain;
// using namespace std;

// // =====================================================
// //                    GLOBAL OBJECTS
// // =====================================================
// Servo s;
// MPU6050 mpu;

// struct Pair {
//     int first;
//     int second;
// };
// // =====================================================
// //                    PIN DEFINITIONS
// // =====================================================
// const int IR1pin   = A0;
// const int IR2pin   = A1;
// const int trigPin  = 9;
// const int echoPin  = 10;
// const int servoPin = 6;

// // =====================================================
// //                    THRESHOLDS
// // =====================================================
// const float WDIST = 25.0f;        // warning distance in cm
// const int IR_THRESHOLD = 500;     // tune experimentally
// const float TUMBLE_ANGLE = 45.0f; // degrees
// const float GYRO_SMOOTH_THRESHOLD = 12000.0f;

// // =====================================================
// //                  GLOBAL STATE
// // =====================================================
// struct globalState {
//     float distance;
//     float ax, ay, az;
//     float gx, gy, gz;
//     Pair irRaw; // first = IR1, second = IR2

//     bool followsLine;
//     bool onTrack;
//     bool obstacle;
//     bool Dobstacle;
//     bool smooth;
//     bool tumbled;

//     globalState(
//         float d = 999.0f,
//         float a1 = 0, float a2 = 0, float a3 = 0,
//         float g1 = 0, float g2 = 0, float g3 = 0,
//         int r1 = 1023, int r2 = 1023
//     )
//         : distance(d), ax(a1), ay(a2), az(a3),
//           gx(g1), gy(g2), gz(g3), irRaw({r1, r2}) {
//         followsLine = false;
//         onTrack = false;
//         obstacle = false;
//         Dobstacle = false;
//         smooth = true;
//         tumbled = false;
//     }

//     void update_pos(
//         float d,
//         float a1, float a2, float a3,
//         float g1, float g2, float g3,
//         int r1, int r2
//     ) {
//         distance = d;
//         ax = a1; ay = a2; az = a3;
//         gx = g1; gy = g2; gz = g3;
//         irRaw = {r1, r2};
//     }

//     float getRotation() const {
//         return sqrt(gx * gx + gy * gy + gz * gz);
//     }

//     float getAcceleration() const {
//         return sqrt(ax * ax + ay * ay + az * az);
//     }

//     float getPitchDeg() const {
//         return atan2(ax, sqrt(ay * ay + az * az)) * 180.0f / PI;
//     }

//     float getRollDeg() const {
//         return atan2(ay, sqrt(ax * ax + az * az)) * 180.0f / PI;
//     }

//     void update() {
//         bool leftOnLine  = (irRaw.first  < IR_THRESHOLD);
//         bool rightOnLine = (irRaw.second < IR_THRESHOLD);

//         followsLine = leftOnLine || rightOnLine;
//         onTrack = leftOnLine && rightOnLine;

//         obstacle = (distance <= WDIST);

//         // "Dynamic obstacle" by your logic:
//         // obstacle exists and motion is not smooth
//         smooth = (getRotation() < GYRO_SMOOTH_THRESHOLD);
//         Dobstacle = obstacle && !smooth;

//         float pitch = getPitchDeg();
//         float roll  = getRollDeg();
//         tumbled = (fabs(pitch) > TUMBLE_ANGLE || fabs(roll) > TUMBLE_ANGLE);
//     }
// };

// globalState gs;

// // =====================================================
// //                    MOTION HELPER
// // =====================================================
// bool smoothRot(globalState &gs, int /*maxSteps*/) {
//     // With only the current state available, use the state’s measured smoothness.
//     // A temporal version could compare previous IMU snapshots.
//     return (gs.getRotation() < GYRO_SMOOTH_THRESHOLD);
// }

// // =====================================================
// //                SENSOR AND ACTION TYPES
// // =====================================================
// enum SensorType {
//     IMU,
//     IR,
//     ULTRA
// };

// enum ACTION {
//     IDLE = 1,
//     BACK_UP = 2,
//     PROCEED_CAUTION = 3,
//     DYNAMIC_OBSTACLE = 4,
//     TUMBLED = 5,
//     LOST = 6,
//     FOLLOWS_LINE = 7
// };

// // =====================================================
// //                 MESSAGE STRUCTURES
// // =====================================================
// struct ImuValue {
//     float ax, ay, az;
//     float gx, gy, gz;
// };

// struct IrValue {
//     int left;
//     int right;
// };

// struct UltraValue {
//     float distance;
// };

// struct Msg {
//     SensorType type;
//     unsigned long t;
//     ImuValue imu;
//     IrValue ir;
//     UltraValue ultra;

//     Msg() : type(IMU), t(0) {
//         imu = {0,0,0,0,0,0};
//         ir = {1023,1023};
//         ultra = {999.0f};
//     }
// };

// ArduinoQueue<Msg> Q;
// volatile bool dataReady = false;

// // =====================================================
// //                    PUBLISHERS
// // =====================================================
// void publishIMU(float ax, float ay, float az, float gx, float gy, float gz) {
//     Msg m;
//     m.type = IMU;
//     m.t = millis();
//     m.imu = {ax, ay, az, gx, gy, gz};

//     noInterrupts();
//     Q.push(m);
//     dataReady = true;
//     interrupts();
// }

// void publishIR(int left, int right) {
//     Msg m;
//     m.type = IR;
//     m.t = millis();
//     m.ir = {left, right};

//     noInterrupts();
//     Q.push(m);
//     dataReady = true;
//     interrupts();
// }

// void publishULTRA(float distance) {
//     Msg m;
//     m.type = ULTRA;
//     m.t = millis();
//     m.ultra = {distance};

//     noInterrupts();
//     Q.push(m);
//     dataReady = true;
//     interrupts();
// }

// // =====================================================
// //              PROCESS COMMUNICATION
// // =====================================================
// void processCom() {
//     if (!dataReady) return;

//     while (true) {
//         noInterrupts();
//         if (Q.empty()) {
//             dataReady = false;
//             interrupts();
//             break;
//         }

//         Msg m = Q.front();
//         Q.pop();
//         interrupts();

//         switch (m.type) {
//             case IMU:
//                 gs.ax = m.imu.ax;
//                 gs.ay = m.imu.ay;
//                 gs.az = m.imu.az;
//                 gs.gx = m.imu.gx;
//                 gs.gy = m.imu.gy;
//                 gs.gz = m.imu.gz;
//                 break;

//             case IR:
//                 gs.irRaw = {m.ir.left, m.ir.right};
//                 break;

//             case ULTRA:
//                 gs.distance = m.ultra.distance;
//                 break;
//         }
//     }

//     gs.update();
// }

// // =====================================================
// //                  SENSOR READINGS
// // =====================================================
// float read_ultra(int echoPin_, int trigPin_) {
//     digitalWrite(trigPin_, LOW);
//     delayMicroseconds(2);

//     digitalWrite(trigPin_, HIGH);
//     delayMicroseconds(10);
//     digitalWrite(trigPin_, LOW);

//     long duration = pulseIn(echoPin_, HIGH, 30000);
//     if (duration == 0) return 999.0f;

//     float d = duration * 0.0343f / 2.0f;
//     return d;
// }

// int read_ir(int irPin) {
//     return analogRead(irPin);
// }

// void read_imu(float &ax, float &ay, float &az, float &gx, float &gy, float &gz) {
//     int16_t rax, ray, raz, rgx, rgy, rgz;
//     mpu.getMotion6(&rax, &ray, &raz, &rgx, &rgy, &rgz);

//     ax = (float)rax;
//     ay = (float)ray;
//     az = (float)raz;
//     gx = (float)rgx;
//     gy = (float)rgy;
//     gz = (float)rgz;
// }

// // =====================================================
// //                  SAT VARIABLES
// // =====================================================
// // 1-based indexing for CNF literals
// enum SATVAR {
//     V_FOLLOWS_LINE = 1,
//     V_ON_TRACK     = 2,
//     V_OBSTACLE     = 3,
//     V_DOBSTACLE    = 4,
//     V_SMOOTH       = 5,
//     V_TUMBLED      = 6,

//     V_ACT_IDLE     = 7,
//     V_ACT_BACK     = 8,
//     V_ACT_CAUTION  = 9,
//     V_ACT_DYNAMIC  = 10,
//     V_ACT_TUMBLED  = 11,
//     V_ACT_LOST     = 12,
//     V_ACT_FOLLOW   = 13
// };

// const int NUM_VARS = 13;

// void addFact(vector<vector<int>>& cnf, int var, bool val) {
//     cnf.push_back({ val ? var : -var });
// }

// // =====================================================
// //             SAT FORMULATION FROM YOUR LOGIC
// // =====================================================
// vector<vector<int>> formulate() {
//     vector<vector<int>> cnf;

//     // Sensor-derived facts
//     addFact(cnf, V_FOLLOWS_LINE, gs.followsLine);
//     addFact(cnf, V_ON_TRACK,     gs.onTrack);
//     addFact(cnf, V_OBSTACLE,     gs.obstacle);
//     addFact(cnf, V_DOBSTACLE,    gs.Dobstacle);
//     addFact(cnf, V_SMOOTH,       gs.smooth);
//     addFact(cnf, V_TUMBLED,      gs.tumbled);

//     // Rules from your intended logic:

//     // 1. If tumbled -> ACT_TUMBLED
//     cnf.push_back({ -V_TUMBLED, V_ACT_TUMBLED });

//     // 2. If dynamic obstacle -> ACT_DYNAMIC
//     cnf.push_back({ -V_DOBSTACLE, V_ACT_DYNAMIC });

//     // 3. If obstacle and not dynamic -> ACT_CAUTION
//     // obstacle AND !dynamic -> caution
//     cnf.push_back({ -V_OBSTACLE, V_DOBSTACLE, V_ACT_CAUTION });

//     // 4. If follows line and on track and no obstacle and not tumbled -> ACT_FOLLOW
//     cnf.push_back({ -V_FOLLOWS_LINE, -V_ON_TRACK, V_OBSTACLE, V_TUMBLED, V_ACT_FOLLOW });

//     // 5. If not follows line and no obstacle and not tumbled -> ACT_LOST
//     cnf.push_back({ V_FOLLOWS_LINE, V_OBSTACLE, V_TUMBLED, V_ACT_LOST });

//     // 6. If not smooth and obstacle -> ACT_BACK
//     cnf.push_back({ V_SMOOTH, -V_OBSTACLE, V_ACT_BACK });

//     // 7. If smooth and no obstacle and not lost and not tumbled -> IDLE allowed
//     cnf.push_back({ -V_SMOOTH, V_OBSTACLE, V_TUMBLED, V_FOLLOWS_LINE, V_ACT_IDLE });

//     // Mutual exclusion between actions
//     int acts[] = {
//         V_ACT_IDLE, V_ACT_BACK, V_ACT_CAUTION, V_ACT_DYNAMIC,
//         V_ACT_TUMBLED, V_ACT_LOST, V_ACT_FOLLOW
//     };

//     for (int i = 0; i < 7; ++i) {
//         for (int j = i + 1; j < 7; ++j) {
//             cnf.push_back({ -acts[i], -acts[j] });
//         }
//     }

//     // At least one action
//     cnf.push_back({
//         V_ACT_IDLE, V_ACT_BACK, V_ACT_CAUTION, V_ACT_DYNAMIC,
//         V_ACT_TUMBLED, V_ACT_LOST, V_ACT_FOLLOW
//     });

//     return cnf;
// }

// // =====================================================
// //                     FUSION
// // =====================================================
// vector<int> fusion() {
//     vector<vector<int>> cnf = formulate();

//     sat solver(300, 0.15);
//     solver.setCNF(NUM_VARS, cnf);
//     solver.solve();

//     return solver.getAssignment();
// }

// // =====================================================
// //                  APPLY COMMANDS
// // =====================================================
// void applyCommands(const vector<int>& sol) {
//     if ((int)sol.size() < NUM_VARS) {
//         Serial.println("No valid SAT assignment size");
//         s.write(90);
//         return;
//     }

//     if (sol[V_ACT_TUMBLED - 1]) {
//         Serial.println("ACTION: TUMBLED");
//         s.write(150);   // strong assist / alarm position
//     }
//     else if (sol[V_ACT_DYNAMIC - 1]) {
//         Serial.println("ACTION: DYNAMIC_OBSTACLE");
//         s.write(130);
//     }
//     else if (sol[V_ACT_CAUTION - 1]) {
//         Serial.println("ACTION: PROCEED_CAUTION");
//         s.write(110);
//     }
//     else if (sol[V_ACT_BACK - 1]) {
//         Serial.println("ACTION: BACK_UP");
//         s.write(60);
//     }
//     else if (sol[V_ACT_LOST - 1]) {
//         Serial.println("ACTION: LOST");
//         s.write(40);
//         delay(150);
//         s.write(140);
//         delay(150);
//         s.write(90);
//     }
//     else if (sol[V_ACT_FOLLOW - 1]) {
//         Serial.println("ACTION: FOLLOWS_LINE");
//         s.write(90);
//     }
//     else {
//         Serial.println("ACTION: IDLE");
//         s.write(90);
//     }
// }

// // =====================================================
// //                    DEBUG PRINT
// // =====================================================
// void printState() {
//     Serial.print("Dist=");
//     Serial.print(gs.distance);

//     Serial.print(" | IR=(");
//     Serial.print(gs.irRaw.first);
//     Serial.print(",");
//     Serial.print(gs.irRaw.second);
//     Serial.print(")");

//     Serial.print(" | Acc=(");
//     Serial.print(gs.ax); Serial.print(",");
//     Serial.print(gs.ay); Serial.print(",");
//     Serial.print(gs.az); Serial.print(")");

//     Serial.print(" | Gyro=(");
//     Serial.print(gs.gx); Serial.print(",");
//     Serial.print(gs.gy); Serial.print(",");
//     Serial.print(gs.gz); Serial.print(")");

//     Serial.print(" | followsLine=");
//     Serial.print(gs.followsLine);
//     Serial.print(" onTrack=");
//     Serial.print(gs.onTrack);
//     Serial.print(" obstacle=");
//     Serial.print(gs.obstacle);
//     Serial.print(" Dobstacle=");
//     Serial.print(gs.Dobstacle);
//     Serial.print(" smooth=");
//     Serial.print(gs.smooth);
//     Serial.print(" tumbled=");
//     Serial.println(gs.tumbled);
// }

// // =====================================================
// //                      SETUP
// // =====================================================
// void setup() {
//     pinMode(IR1pin, INPUT);
//     pinMode(IR2pin, INPUT);
//     pinMode(trigPin, OUTPUT);
//     pinMode(echoPin, INPUT);

//     s.attach(servoPin);
//     s.write(90);

//     Serial.begin(9600);
//     Serial.println("Serial connection established");

//     Wire.begin();
//     mpu.initialize();

//     if (mpu.testConnection()) {
//         Serial.println("MPU6050 connected");
//     } else {
//         Serial.println("MPU6050 connection failed");
//     }
// }

// // =====================================================
// //                       LOOP
// // =====================================================
// void loop() {
//     static unsigned long lastIR = 0;
//     static unsigned long lastUltra = 0;
//     static unsigned long lastIMU = 0;
//     static unsigned long lastSAT = 0;

//     unsigned long now = millis();

//     if (now - lastIR >= 20) {
//         lastIR = now;
//         int left = read_ir(IR1pin);
//         int right = read_ir(IR2pin);
//         publishIR(left, right);
//     }

//     if (now - lastUltra >= 60) {
//         lastUltra = now;
//         float d = read_ultra(echoPin, trigPin);
//         publishULTRA(d);
//     }

//     if (now - lastIMU >= 40) {
//         lastIMU = now;
//         float ax, ay, az, gx, gy, gz;
//         read_imu(ax, ay, az, gx, gy, gz);
//         publishIMU(ax, ay, az, gx, gy, gz);
//     }

//     processCom();

//     if (now - lastSAT >= 100) {
//         lastSAT = now;

//         gs.smooth = smoothRot(gs, 3);
//         gs.update();

//         printState();

//         vector<int> sol = fusion();
//         applyCommands(sol);

//         Serial.println("----------------------------");
//     }
// }
#include <Servo.h>
#include <Wire.h>
#include <MPU6050.h>
#include <math.h>

Servo s;
MPU6050 mpu;

// ---------------- Pins ----------------
const byte IR1pin   = A0;
const byte IR2pin   = A1;
const byte trigPin  = 9;
const byte echoPin  = 10;
const byte servoPin = 6;

// ---------------- Thresholds ----------------
const int IR_THRESHOLD = 500;
const int WDIST_CM = 25;
const int TUMBLE_DEG = 45;

// Use squared threshold to avoid extra sqrt for gyro magnitude
const long GYRO_SMOOTH_THRESHOLD_SQ = 144000000L; // 12000^2

// ---------------- Action enum ----------------
enum Action : byte {
  ACT_IDLE = 0,
  ACT_BACK,
  ACT_CAUTION,
  ACT_DYNAMIC,
  ACT_TUMBLED,
  ACT_LOST,
  ACT_FOLLOW
};

// ---------------- Compact global state ----------------
struct State {
  int distanceCm;
  int irLeft;
  int irRight;

  int16_t ax;
  int16_t ay;
  int16_t az;
  int16_t gx;
  int16_t gy;
  int16_t gz;

  bool followsLine;
  bool onTrack;
  bool obstacle;
  bool dynamicObstacle;
  bool smooth;
  bool tumbled;
};

State gs;

// ---------------- Ultrasonic ----------------
static int readUltraCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 25000UL);
  if (duration == 0) return 999;

  // cm ≈ duration * 0.0343 / 2
  return (int)(duration / 58UL);
}

// ---------------- IMU ----------------
static void readIMU() {
  mpu.getMotion6(&gs.ax, &gs.ay, &gs.az, &gs.gx, &gs.gy, &gs.gz);
}

// ---------------- Derived state ----------------
static void updateState() {
  bool leftOnLine  = (gs.irLeft  < IR_THRESHOLD);
  bool rightOnLine = (gs.irRight < IR_THRESHOLD);

  gs.followsLine = leftOnLine || rightOnLine;
  gs.onTrack = leftOnLine && rightOnLine;
  gs.obstacle = (gs.distanceCm <= WDIST_CM);

  long gx = gs.gx;
  long gy = gs.gy;
  long gz = gs.gz;
  long rotSq = gx * gx + gy * gy + gz * gz;

  gs.smooth = (rotSq < GYRO_SMOOTH_THRESHOLD_SQ);
  gs.dynamicObstacle = gs.obstacle && !gs.smooth;

  // Keep tumble detection, but only compute 2 atan2 values once per cycle
  float pitch = atan2((float)gs.ax, sqrt((float)gs.ay * gs.ay + (float)gs.az * gs.az)) * 57.2958f;
  float roll  = atan2((float)gs.ay, sqrt((float)gs.ax * gs.ax + (float)gs.az * gs.az)) * 57.2958f;

  gs.tumbled = (fabs(pitch) > TUMBLE_DEG || fabs(roll) > TUMBLE_DEG);
}

// ---------------- Decision logic ----------------
static Action decideAction() {
  if (gs.tumbled) {
    return ACT_TUMBLED;
  }

  if (gs.dynamicObstacle) {
    return ACT_DYNAMIC;
  }

  if (gs.obstacle && !gs.dynamicObstacle) {
    return ACT_CAUTION;
  }

  if (!gs.smooth && gs.obstacle) {
    return ACT_BACK;
  }

  if (gs.followsLine && gs.onTrack && !gs.obstacle && !gs.tumbled) {
    return ACT_FOLLOW;
  }

  if (!gs.followsLine && !gs.obstacle && !gs.tumbled) {
    return ACT_LOST;
  }

  return ACT_IDLE;
}

// ---------------- Actuation ----------------
static void applyAction(Action a) {
  switch (a) {
    case ACT_TUMBLED:
      s.write(150);
      break;

    case ACT_DYNAMIC:
      s.write(130);
      break;

    case ACT_CAUTION:
      s.write(110);
      break;

    case ACT_BACK:
      s.write(60);
      break;

    case ACT_LOST:
      s.write(45);
      delay(80);
      s.write(135);
      delay(80);
      s.write(90);
      break;

    case ACT_FOLLOW:
    case ACT_IDLE:
    default:
      s.write(90);
      break;
  }
}

// ---------------- Tiny debug ----------------
static void printMini(Action a) {
  Serial.print(F("D="));
  Serial.print(gs.distanceCm);
  Serial.print(F(" L="));
  Serial.print(gs.irLeft);
  Serial.print(F(" R="));
  Serial.print(gs.irRight);
  Serial.print(F(" A="));
  Serial.println((byte)a);
}

// ---------------- Setup ----------------
void setup() {
  pinMode(IR1pin, INPUT);
  pinMode(IR2pin, INPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  gs.distanceCm = 999;
  gs.irLeft = 1023;
  gs.irRight = 1023;
  gs.ax = gs.ay = gs.az = 0;
  gs.gx = gs.gy = gs.gz = 0;
  gs.followsLine = false;
  gs.onTrack = false;
  gs.obstacle = false;
  gs.dynamicObstacle = false;
  gs.smooth = true;
  gs.tumbled = false;

  s.attach(servoPin);
  s.write(90);

  Serial.begin(9600);
  Serial.println(F("Start"));

  Wire.begin();
  mpu.initialize();

  if (mpu.testConnection()) {
    Serial.println(F("MPU OK"));
  } else {
    Serial.println(F("MPU FAIL"));
  }
}

// ---------------- Loop ----------------
void loop() {
  static unsigned long lastIR = 0;
  static unsigned long lastUltra = 0;
  static unsigned long lastIMU = 0;
  static unsigned long lastLogic = 0;

  unsigned long now = millis();

  if (now - lastIR >= 40) {
    lastIR = now;
    gs.irLeft = analogRead(IR1pin);
    gs.irRight = analogRead(IR2pin);
  }

  if (now - lastUltra >= 100) {
    lastUltra = now;
    gs.distanceCm = readUltraCm();
  }

  if (now - lastIMU >= 70) {
    lastIMU = now;
    readIMU();
  }

  if (now - lastLogic >= 160) {
    lastLogic = now;

    updateState();
    Action a = decideAction();
    applyAction(a);

    // Comment this out for even lower memory / more stability
    printMini(a);
  }
}
