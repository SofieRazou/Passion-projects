#include <PID_v1.h>

const int photoPIN = A0;
const int red = 12;
const int green = 10;
const int blue = 11;

// PID variables
double in, out;
const double setpoint = 20.0;
double Kp = 0.5;
double Ki = 0.1;
double Kd = 0.1;

PID myPID(&in, &out, &setpoint, Kp, Ki, Kd, DIRECT);


void setup() {
  Serial.begin(9600);
  pinMode(red, OUTPUT);
  pinMode(green, OUTPUT);
  pinMode(blue, OUTPUT);

  in = analogRead(photoPIN);
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 255);  
}
void loop() {
  in = analogRead(photoPIN);
  myPID.Compute();
  
  // Wider, more practical output ranges
  if (out < 85) {              // Low output (0-84)
    digitalWrite(red, HIGH);    // Red
    digitalWrite(green, LOW);
    digitalWrite(blue, LOW);
  } 
  else if (out < 170) {        // Medium output (85-169)
    digitalWrite(red, LOW);
    digitalWrite(green, HIGH);  // Green
    digitalWrite(blue, LOW);
  } 
  else {                       // High output (170-255)
    digitalWrite(red, LOW);
    digitalWrite(green, LOW);
    digitalWrite(blue, HIGH);   // Blue
  }
  
  // Monitoring
  Serial.print("Input: "); Serial.print(in);
  Serial.print(" Output: "); Serial.print(out);
  Serial.print(" Error: "); Serial.println(setpoint - in);
  
  delay(50);
} 