#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* WIFI_SSID="Bozzelli_2.4";
const char* WIFI_PASSWORD="t@81pa(u51L0";

const int LEFT_PIN=25,CENTER_PIN=26,RIGHT_PIN=27;
const int ANGLE_NONE=0;
const int ANGLE_GROUND=10;
const int ANGLE_KNEE=30;
const int ANGLE_WAIST=60;
const int ANGLE_HEAD=90;

Servo leftServo,centerServo,rightServo;
WebServer server(80);

const char* LEVEL_NAMES[] = {"HEAD", "WAIST", "KNEE", "GROUND"};
const char* LEVEL_KEYS[] = {"head", "waist", "knee", "ground"};
const char* REGION_KEYS[] = {"left", "center", "right"};

// spatialState[level][region]
// level order: HEAD, WAIST, KNEE, GROUND
// region order: LEFT, CENTER, RIGHT
bool spatialState[4][3] = {
  {false, false, false},
  {false, false, false},
  {false, false, false},
  {false, false, false}
};

int currentLeftAngle = -1;
int currentCenterAngle = -1;
int currentRightAngle = -1;

bool parseBoolValue(const String& block, const char* key, bool& value) {
  String token = String("\"") + key + "\"";
  int keyIndex = block.indexOf(token);
  if (keyIndex < 0) return false;

  int colonIndex = block.indexOf(':', keyIndex);
  if (colonIndex < 0) return false;

  String valueText = block.substring(colonIndex + 1);
  valueText.trim();

  if (valueText.startsWith("true")) {
    value = true;
    return true;
  }

  if (valueText.startsWith("false")) {
    value = false;
    return true;
  }

  return false;
}

String extractObjectBlock(const String& payload, const char* key) {
  String token = String("\"") + key + "\"";
  int keyIndex = payload.indexOf(token);
  if (keyIndex < 0) return String();

  int openBrace = payload.indexOf('{', keyIndex);
  if (openBrace < 0) return String();

  int depth = 0;
  for (int index = openBrace; index < payload.length(); ++index) {
    char current = payload.charAt(index);
    if (current == '{') {
      ++depth;
    } else if (current == '}') {
      --depth;
      if (depth == 0) return payload.substring(openBrace, index + 1);
    }
  }

  return String();
}

bool parseLevelState(const String& payload, const char* levelKey, bool values[3]) {
  String block = extractObjectBlock(payload, levelKey);
  if (block.length() == 0) return false;

  return parseBoolValue(block, "left", values[0])
      && parseBoolValue(block, "center", values[1])
      && parseBoolValue(block, "right", values[2]);
}

bool parseSpatialState(const String& payload, bool output[4][3]) {
  bool parsed[4][3] = {
    {false, false, false},
    {false, false, false},
    {false, false, false},
    {false, false, false}
  };

  for (int level = 0; level < 4; ++level) {
    bool values[3] = {false, false, false};
    if (!parseLevelState(payload, LEVEL_KEYS[level], values)) return false;

    for (int region = 0; region < 3; ++region) {
      parsed[level][region] = values[region];
    }
  }

  for (int level = 0; level < 4; ++level) {
    for (int region = 0; region < 3; ++region) {
      output[level][region] = parsed[level][region];
    }
  }

  return true;
}

int angleForRegion(int regionIndex) {
  // Priority order: HEAD > WAIST > KNEE > GROUND
  if (spatialState[0][regionIndex]) return ANGLE_HEAD;
  if (spatialState[1][regionIndex]) return ANGLE_WAIST;
  if (spatialState[2][regionIndex]) return ANGLE_KNEE;
  if (spatialState[3][regionIndex]) return ANGLE_GROUND;
  return ANGLE_NONE;
}

void writeServoIfChanged(Servo& servo, int targetAngle, int& previousAngle) {
  if (targetAngle == previousAngle) return;
  servo.write(targetAngle);
  previousAngle = targetAngle;
}

void updateServosFromSpatialState() {
  int leftAngle = angleForRegion(0);
  int centerAngle = angleForRegion(1);
  int rightAngle = angleForRegion(2);

  writeServoIfChanged(leftServo, leftAngle, currentLeftAngle);
  writeServoIfChanged(centerServo, centerAngle, currentCenterAngle);
  writeServoIfChanged(rightServo, rightAngle, currentRightAngle);

  Serial.println("Servo angles:");
  Serial.print("LEFT   = " ); Serial.println(leftAngle);
  Serial.print("CENTER = " ); Serial.println(centerAngle);
  Serial.print("RIGHT  = " ); Serial.println(rightAngle);
}

void printSpatialState() {
  Serial.println("Received spatial state:");
  for (int level = 0; level < 4; ++level) {
    Serial.print(LEVEL_NAMES[level]);
    Serial.print("   : L=");
    Serial.print(spatialState[level][0] ? 1 : 0);
    Serial.print(" C=");
    Serial.print(spatialState[level][1] ? 1 : 0);
    Serial.print(" R=");
    Serial.println(spatialState[level][2] ? 1 : 0);
  }
}

void handleState(){
  if(!server.hasArg("plain")) {
    server.send(400,"text/plain","Missing JSON body");
    return;
  }

  String payload = server.arg("plain");
  payload.trim();
  if(payload.length()==0) {
    server.send(400,"text/plain","Invalid JSON");
    return;
  }

  bool parsedState[4][3];
  if(!parseSpatialState(payload, parsedState)) {
    server.send(400,"text/plain","Invalid JSON");
    return;
  }

  for (int level = 0; level < 4; ++level) {
    for (int region = 0; region < 3; ++region) {
      spatialState[level][region] = parsedState[level][region];
    }
  }

  printSpatialState();
  updateServosFromSpatialState();
  server.send(200,"text/plain","OK");
}

void handleRoot(){
 String h="<!doctype html><html><meta http-equiv='refresh' content='1'><body><h2>Blind Navigation</h2>";
 h+="<p>LEFT ANGLE: ";h+=String(currentLeftAngle<0?0:currentLeftAngle);h+="</p>";
 h+="<p>CENTER ANGLE: ";h+=String(currentCenterAngle<0?0:currentCenterAngle);h+="</p>";
 h+="<p>RIGHT ANGLE: ";h+=String(currentRightAngle<0?0:currentRightAngle);h+="</p></body></html>";
 server.send(200,"text/html",h);
}

void setup(){
 Serial.begin(115200);
 leftServo.attach(LEFT_PIN);centerServo.attach(CENTER_PIN);rightServo.attach(RIGHT_PIN);
 updateServosFromSpatialState();
 WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
 while(WiFi.status()!=WL_CONNECTED){delay(500);} 
 Serial.println(WiFi.localIP());
 server.on("/",handleRoot);
 server.on("/state",HTTP_POST,handleState);
 server.begin();
}

void loop(){server.handleClient();}
