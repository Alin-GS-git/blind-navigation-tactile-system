/*
  Phase 2 - ESP32 Web Server (communication test)

  Connects to Wi-Fi, starts an HTTP server, and listens for:
    /left
    /center
    /right
    /none

  When a request comes in, it prints the corresponding direction to
  the Serial Monitor. No servo control here - that's Phase 3. This
  sketch's only job is to prove the Python -> ESP32 link works.

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

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

WebServer server(80);

void handleLeft() {
  Serial.println("LEFT");
  server.send(200, "text/plain", "OK: LEFT");
}

void handleCenter() {
  Serial.println("CENTER");
  server.send(200, "text/plain", "OK: CENTER");
}

void handleRight() {
  Serial.println("RIGHT");
  server.send(200, "text/plain", "OK: RIGHT");
}

void handleNone() {
  Serial.println("NONE");
  server.send(200, "text/plain", "OK: NONE");
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

  server.on("/left", handleLeft);
  server.on("/center", handleCenter);
  server.on("/right", handleRight);
  server.on("/none", handleNone);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}
