// ---------------- PID Parameters ----------------
float Kp = 2.0;
float Ki = 0.5;
float Kd = 0.1;

float setpoint = 50.0;
float input = 0;
float output = 0;

float lastError = 0;
float integral = 0;
unsigned long lastTime = 0;

// ---------------- Arduino Pin Definitions ----------------
int potPin = A0;
int motorPWM = 9;
int motorIn1 = 7;
int motorIn2 = 8;

// ---------------- PID Function ----------------
float PID(float setpoint, float input){
  unsigned long now = millis();
  float deltaTime = (now - lastTime)/1000.0;
  if(deltaTime <= 0.0) deltaTime = 0.001;

  float error = setpoint - input;
  integral += error * deltaTime;
  float derivative = (error - lastError)/deltaTime;

  float Pout = Kp * error;
  float Iout = Ki * integral;
  float Dout = Kd * derivative;

  output = Pout + Iout + Dout;
  output = constrain(output, -255, 255);

  lastError = error;
  lastTime = now;

  return output;
}

// ---------------- Movement Function ----------------
void moveMotor(int durationMs, bool forward) {
  float pidOutput = PID(setpoint, input);
  if(!forward) pidOutput = -pidOutput;

  if(pidOutput >= 0){
    digitalWrite(motorIn1, HIGH);
    digitalWrite(motorIn2, LOW);
  } else {
    digitalWrite(motorIn1, LOW);
    digitalWrite(motorIn2, HIGH);
    pidOutput = -pidOutput;
  }

  analogWrite(motorPWM, (int)pidOutput);
  delay(durationMs);
  analogWrite(motorPWM, 0); // stop motor
}

// ---------------- Setup ----------------
void setup() {
  pinMode(potPin, INPUT);
  pinMode(motorPWM, OUTPUT);
  pinMode(motorIn1, OUTPUT);
  pinMode(motorIn2, OUTPUT);

  Serial.begin(9600);
  lastTime = millis();
  Serial.println("Arduino ready");
}

// ---------------- Loop ----------------
void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'N') {
      Serial.println("Moving North");
      moveMotor(1000, true);
    } else if (command == 'S') {
      Serial.println("Moving South");
      moveMotor(1000, false);
    } else if (command == 'E') {
      Serial.println("Turning East");
      moveMotor(500, true);
    } else if (command == 'W') {
      Serial.println("Turning West");
      moveMotor(500, false);
    }
  }
}
