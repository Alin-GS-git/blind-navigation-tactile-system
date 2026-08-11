/*
  Phase 2 - ESP32 Web Server (communication test)

  Connects to Wi-Fi, starts an HTTP server, and listens for:
  /state

  Receives the 3x4 spatial state from Phase 2 and prints it
  to the Serial Monitor.

  No servo control here - that is handled later in Phase 3.
*/

#include <WiFi.h>
#include <WebServer.h>

const char* WIFI_SSID = "Bozzelli_2.4";
const char* WIFI_PASSWORD = "t@81pa(u51L0";

WebServer server(80);

const char* LEVEL_NAMES[] = {
  "HEAD",
  "WAIST",
  "KNEE",
  "GROUND"
};

const char* LEVEL_KEYS[] = {
  "head",
  "waist",
  "knee",
  "ground"
};

// spatialState[level][region]
// region: 0 = left, 1 = center, 2 = right
bool spatialState[4][3] = {
  {false, false, false},
  {false, false, false},
  {false, false, false},
  {false, false, false}
};


// ------------------------------------------------------------
// Parse a boolean value for a given key from a JSON object
// ------------------------------------------------------------
bool parseBoolValue(const String& block, const char* key, bool& value) {

  String token = String("\"") + key + "\"";

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


// ------------------------------------------------------------
// Extract the JSON object belonging to a specific level
// ------------------------------------------------------------
String extractObjectBlock(const String& payload, const char* key) {

  String token = String("\"") + key + "\"";

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
    }
    else if (current == '}') {

      --depth;

      if (depth == 0) {
        return payload.substring(openBrace, index + 1);
      }
    }
  }

  return String();
}


// ------------------------------------------------------------
// Parse one vertical level
// ------------------------------------------------------------
bool parseLevelState(
  const String& payload,
  const char* levelKey,
  bool values[3]
) {

  String block = extractObjectBlock(payload, levelKey);

  if (block.length() == 0) {
    return false;
  }

  return parseBoolValue(block, "left", values[0])
      && parseBoolValue(block, "center", values[1])
      && parseBoolValue(block, "right", values[2]);
}


// ------------------------------------------------------------
// Parse complete 4x3 spatial state
// ------------------------------------------------------------
bool parseSpatialState(
  const String& payload,
  bool output[4][3]
) {

  bool parsed[4][3] = {
    {false, false, false},
    {false, false, false},
    {false, false, false},
    {false, false, false}
  };

  for (int level = 0; level < 4; ++level) {

    bool values[3] = {
      false,
      false,
      false
    };

    if (!parseLevelState(
          payload,
          LEVEL_KEYS[level],
          values
        )) {

      return false;
    }

    for (int region = 0; region < 3; ++region) {
      parsed[level][region] = values[region];
    }
  }

  for (int level = 0; level < 4; ++level) {

    for (int region = 0; region < 3; ++region) {

      output[level][region] =
        parsed[level][region];
    }
  }

  return true;
}


// ------------------------------------------------------------
// Print the current spatial state
// ------------------------------------------------------------
void printSpatialState() {

  Serial.println();
  Serial.println("Received spatial state:");

  for (int level = 0; level < 4; ++level) {

    Serial.print(LEVEL_NAMES[level]);
    Serial.println(":");

    Serial.print("  LEFT=");
    Serial.println(
      spatialState[level][0] ? "ON" : "OFF"
    );

    Serial.print("  CENTER=");
    Serial.println(
      spatialState[level][1] ? "ON" : "OFF"
    );

    Serial.print("  RIGHT=");
    Serial.println(
      spatialState[level][2] ? "ON" : "OFF"
    );
  }

  Serial.println();
}


// ------------------------------------------------------------
// Handle POST /state
// ------------------------------------------------------------
void handleState() {

  if (!server.hasArg("plain")) {

    server.send(
      400,
      "text/plain",
      "Missing JSON body"
    );

    return;
  }

  String payload = server.arg("plain");
  payload.trim();

  if (payload.length() == 0) {

    server.send(
      400,
      "text/plain",
      "Invalid JSON"
    );

    return;
  }

  bool parsedState[4][3];

  if (!parseSpatialState(
        payload,
        parsedState
      )) {

    server.send(
      400,
      "text/plain",
      "Invalid JSON"
    );

    return;
  }

  // Copy parsed state into global state
  for (int level = 0; level < 4; ++level) {

    for (int region = 0; region < 3; ++region) {

      spatialState[level][region] =
        parsedState[level][region];
    }
  }

  printSpatialState();

  server.send(
    200,
    "text/plain",
    "OK"
  );
}


// ------------------------------------------------------------
// Handle unknown URLs
// ------------------------------------------------------------
void handleNotFound() {

  server.send(
    404,
    "text/plain",
    "Unknown endpoint"
  );
}


// ------------------------------------------------------------
// Setup
// ------------------------------------------------------------
void setup() {

  Serial.begin(115200);

  delay(200);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {

    delay(400);

    Serial.print(".");
  }

  Serial.println();

  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println(
    "Use this IP as esp32_ip on the Python side."
  );

  server.on(
    "/state",
    HTTP_POST,
    handleState
  );

  server.onNotFound(
    handleNotFound
  );

  server.begin();

  Serial.println(
    "HTTP server started."
  );
}


// ------------------------------------------------------------
// Main loop
// ------------------------------------------------------------
void loop() {

  server.handleClient();
}