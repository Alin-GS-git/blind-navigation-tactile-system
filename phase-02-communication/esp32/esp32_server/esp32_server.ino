/*
  Phase 2 - ESP32 Web Server (communication test)

  Connects to Wi-Fi, starts an HTTP server, and listens for:
    /state

  When a request comes in, it prints the corresponding occupancy
  state to the Serial Monitor. No servo control here - that's Phase 3. This
  sketch's only job is to prove the Python -> ESP32 link works.

  Setup:
    1. Install the "WiFi", "WebServer", and "ArduinoJson" libraries (bundled with the
       ESP32 board package in Arduino IDE - Boards Manager > esp32).
    2. Fill in WIFI_SSID and WIFI_PASSWORD below.
    3. Upload to the ESP32, then open Serial Monitor at 115200 baud.
    4. Note the IP address it prints - use that as esp32_ip in
       communication.py / main.py on the Python side.
*/
/*
  Phase 2 - ESP32 Web Server (No ArduinoJson)

  Endpoint:
      /state?left=1&center=0&right=1

  Prints the received occupancy state to the Serial Monitor.
*/

#include <WiFi.h>
#include <WebServer.h>

const char* WIFI_SSID = "Bozzelli_2.4";
const char* WIFI_PASSWORD = "t@81pa(u51L0";

WebServer server(80);

bool leftOccupied = false;
bool centerOccupied = false;
bool rightOccupied = false;

void printOccupancyState() {
  Serial.println();
  Serial.println("===== Occupancy State =====");
  Serial.print("LEFT   : ");
  Serial.println(leftOccupied ? "YES" : "NO");

  Serial.print("CENTER : ");
  Serial.println(centerOccupied ? "YES" : "NO");

  Serial.print("RIGHT  : ");
  Serial.println(rightOccupied ? "YES" : "NO");
  Serial.println("===========================");
}

void handleState() {

  if (server.hasArg("left"))
    leftOccupied = server.arg("left") == "1";

  if (server.hasArg("center"))
    centerOccupied = server.arg("center") == "1";

  if (server.hasArg("right"))
    rightOccupied = server.arg("right") == "1";

  printOccupancyState();

  server.send(200, "text/plain", "OK");
}

void handleNotFound() {
  server.send(404, "text/plain", "Unknown endpoint");
}

void setup() {

  Serial.begin(115200);
  delay(500);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());

  server.on("/state", HTTP_GET, handleState);
  server.onNotFound(handleNotFound);

  server.begin();

  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}