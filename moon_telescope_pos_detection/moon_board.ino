const int redPin = 7;
const int greenPin = 5;
const int bluePin = 6;      // Moved from 11 to 6

const int motorPin1 = 9;    // IN1 (H-Bridge)
const int motorPin2 = 10;   // IN2 (H-Bridge)
const int motorEnable = 11; // EN (H-Bridge enable)

bool motorActive = false;   // To prevent repeating motor actions

void setup() {
  Serial.begin(9600);

  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);

  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);
  pinMode(motorEnable, OUTPUT);

  digitalWrite(greenPin, HIGH);  // Initial LED state
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    Serial.println(cmd);

    if (cmd == "not found" && !motorActive) {
      motorActive = true;

      digitalWrite(redPin, HIGH);
      digitalWrite(greenPin, LOW);
      digitalWrite(bluePin, LOW);

      // Spin left
      digitalWrite(motorPin1, HIGH);
      digitalWrite(motorPin2, LOW);
      digitalWrite(motorEnable, HIGH);
      delay(2000);

      // Spin right
      digitalWrite(motorPin1, LOW);
      digitalWrite(motorPin2, HIGH);
      delay(2000);

      // Optionally stop here or keep spinning
      digitalWrite(motorEnable, LOW);
    }
    else if (cmd == "found" && motorActive) {
      motorActive = false;

      digitalWrite(redPin, LOW);
      digitalWrite(greenPin, HIGH);
      digitalWrite(bluePin, LOW);

      // Stop motor
      digitalWrite(motorEnable, LOW);
      digitalWrite(motorPin1, LOW);
      digitalWrite(motorPin2, LOW);
    }
  }
}
