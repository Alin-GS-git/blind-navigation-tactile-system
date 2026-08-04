#include <ESP32Servo.h>

Servo leftServo;
Servo centerServo;
Servo rightServo;

const int LEFT_PIN = 25;
const int CENTER_PIN = 26;
const int RIGHT_PIN = 27;

void setup() {
  Serial.begin(115200);

  leftServo.attach(LEFT_PIN);
  centerServo.attach(CENTER_PIN);
  rightServo.attach(RIGHT_PIN);

  leftServo.write(0);
  centerServo.write(0);
  rightServo.write(0);

  Serial.println("Enter:");
  Serial.println("L   = Left");
  Serial.println("C   = Center");
  Serial.println("R   = Right");
  Serial.println("LC  = Left + Center");
  Serial.println("LR  = Left + Right");
  Serial.println("CR  = Center + Right");
  Serial.println("LCR = All three");
}

void loop() {

  if (Serial.available()) {

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    bool left = false;
    bool center = false;
    bool right = false;

    if (cmd.indexOf('L') >= 0 || cmd.indexOf('l') >= 0)
      left = true;

    if (cmd.indexOf('C') >= 0 || cmd.indexOf('c') >= 0)
      center = true;

    if (cmd.indexOf('R') >= 0 || cmd.indexOf('r') >= 0)
      right = true;

    // Move selected servos together
    if (left) leftServo.write(90);
    if (center) centerServo.write(90);
    if (right) rightServo.write(90);

    delay(1000);

    // Return selected servos together
    if (left) leftServo.write(0);
    if (center) centerServo.write(0);
    if (right) rightServo.write(0);
  }
}