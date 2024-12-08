#include <Wire.h>
#include <DS3231.h>
#include <Servo.h>

Servo myServo;  // Create a servo object to control the servo motor
DS3231 rtc;      // Create an RTC object to interface with the DS3231 RTC module

const int SERVOpin = 9;       // Pin connected to the servo
const int CaliPin = 2;        // Pin to read the calibration input
const int redPin = 5;         // Red LED for warning or event indication
const int bluePin = 6;        // Blue LED for another event or indication
const int greenPin = 7;       // Green LED for normal operation

int CaliVal = 0;              // Variable to store the calibration state

void setup() {
  myServo.attach(SERVOpin);   // Attach the servo to the designated pin
  pinMode(CaliPin, INPUT);    // Set calibration pin as input
  pinMode(redPin, OUTPUT);    // Set LED pins as output
  pinMode(bluePin, OUTPUT);   
  pinMode(greenPin, OUTPUT);
  
  Serial.begin(9600);         // Start serial communication for debugging

  rtc.begin();                // Initialize the RTC module
  rtc.setDate(23, 11, 2024);  // Set current date - example
  rtc.setTime(12, 0, 0);      // Set current time - example: 12:00 PM
}

void loop() {
  CaliVal = digitalRead(CaliPin);  // Read the calibration state from the input pin
  
  // Get the current time from the RTC
  int hour = rtc.getHour(true);    // Get the current hour in 24-hour format
  int minute = rtc.getMinute();    // Get the current minute

  if (CaliVal == LOW) {   // If calibration switch is pressed, reset state
    digitalWrite(greenPin, HIGH);   // Turn on green LED to indicate normal operation
    Serial.println("Calibration Mode: Starting Simulation");

    // Simulate Antikythera-like movement based on current hour (Sun/Moon simulation)
    int servoPosition = map(hour, 0, 23, 0, 180);  // Map hours to servo range 0-180 degrees
    myServo.write(servoPosition);                     // Move servo based on time
    delay(1000);                                      // Wait for 1 second to stabilize the servo movement
  } else {
    // Simulation of a celestial event using LEDs based on minute
    digitalWrite(redPin, HIGH);    // Turn on red LED to indicate celestial event
    delay(2000);                   // Wait for 2 seconds
    
    digitalWrite(bluePin, HIGH);   // Turn on blue LED for another event
    myServo.write(90);             // Move the servo to the middle position
    delay(1000);                   // Wait for 1 second
    digitalWrite(redPin, LOW);     // Turn off red LED
    delay(3000);                   // Wait for 3 seconds
    digitalWrite(bluePin, LOW);    // Turn off blue LED
    digitalWrite(greenPin, LOW);   // Turn off green LED (end of event)
  }

  // Optionally, use the minute data to fine-tune the servo position or simulate more detailed behavior
  // For example, you can map the minutes to the servo for a more granular simulation
  int minutePosition = map(minute, 0, 59, 0, 180);  // Map minutes to servo position
  myServo.write(minutePosition);                      // Move servo based on the minute
  delay(1000);                                        // Wait for 1 second to show movement
}
