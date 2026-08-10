/*
  Phase 2 - ESP32 Web Server (communication test)

  Connects to Wi-Fi, starts an HTTP server, and listens for:
    /state

  When a request comes in, it prints the corresponding spatial
  state to the Serial Monitor. No servo control here - that is
  handled later in Phase 3.

  Setup:
    1. Install the "WiFi" and "WebServer" libraries (bundled with the
       ESP32 board package in Arduino IDE - Boards Manager > esp32).
    2. Fill in WIFI_SSID and WIFI_PASSWORD below.
    3. Upload to the ESP32, then open Serial Monitor at 115200 baud.
    4. Note the IP address it prints - use that as esp32_ip in
       communication.py / main.py on the Python side.
*/

#include <WiFi.h>
#include <WebServer.h>

const char* WIFI_SSID = "All_in";
const char* WIFI_PASSWORD = "98765432";

WebServer server(80);

const char* LEVEL_NAMES[] = {"HEAD", "WAIST", "KNEE", "GROUND"};
const char* LEVEL_KEYS[] = {"head", "waist", "knee", "ground"};
bool spatialState[4][3] = {
  {false, false, false},
  {false, false, false},
  {false, false, false},
  {false, false, false}
};

bool parseBoolValue(const String& block, const char* key, bool& value) {
  String token = String(""") + key + """;
  int keyIndex = block.indexOf(token);
  if (keyIndex < 0) {
    return false;
  }

  int colonIndex = block.indexOf(':', keyIndex);
  if (colonIndex < 0) {
    return false;
  }

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
  String token = String(""") + key + """;
  int keyIndex = payload.indexOf(token);
  if (keyIndex < 0) {
    return String();
  }

  int openBrace = payload.indexOf('{', keyIndex);
  if (openBrace < 0) {
    return String();
  }

  int depth = 0;
  for (int index = openBrace; index < payload.length(); ++index) {
    char current = payload.charAt(index);
    if (current == '{') {
      ++depth;
    } else if (current == '}') {
      --depth;
      if (depth == 0) {
        return payload.substring(openBrace, index + 1);
      }
    }
  }

  return String();
}

bool parseLevelState(const String& payload, const char* levelKey, bool values[3]) {
  String block = extractObjectBlock(payload, levelKey);
  if (block.length() == 0) {
    return false;
  }

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
    if (!parseLevelState(payload, LEVEL_KEYS[level], values)) {
      return false;
    }

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

void printSpatialState() {
  for (int level = 0; level < 4; ++level) {
    Serial.print(LEVEL_NAMES[level]);
    Serial.println(":");
    Serial.print("  LEFT=");
    Serial.println(spatialState[level][0] ? "ON" : "OFF");
    Serial.print("  CENTER=");
    Serial.println(spatialState[level][1] ? "ON" : "OFF");
    Serial.print("  RIGHT=");
    Serial.println(spatialState[level][2] ? "ON" : "OFF");
  }
}

void handleState() {
  if (!server.hasArg("plain")) {
    server.send(400, "text/plain", "Missing JSON body");
    return;
  }

  String payload = server.arg("plain");
  payload.trim();

  if (payload.length() == 0) {
    server.send(400, "text/plain", "Invalid JSON");
    return;
  }

  bool parsedState[4][3];
  if (!parseSpatialState(payload, parsedState)) {
    server.send(400, "text/plain", "Invalid JSON");
    return;
  }

  for (int level = 0; level < 4; ++level) {
    for (int region = 0; region < 3; ++region) {
      spatialState[level][region] = parsedState[level][region];
    }
  }

  printSpatialState();
  server.send(200, "text/plain", "OK");
}

void handleNotFound() {
  server.send(404, "text/plain", "Unknown endpoint");
}

void setup() {
  Serial.begin(115200);
  delay(200);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Use this IP as esp32_ip on the Python side.");

  server.on("/state", HTTP_POST, handleState);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}
