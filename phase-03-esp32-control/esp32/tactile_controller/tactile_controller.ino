#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* WIFI_SSID="";
const char* WIFI_PASSWORD="";

const int LEFT_PIN=25,CENTER_PIN=26,RIGHT_PIN=27;
const int UP_ANGLE=90,DOWN_ANGLE=0;
Servo leftServo,centerServo,rightServo;
WebServer server(80);
bool leftOcc=false,centerOcc=false,rightOcc=false;

void updateServos(){
 leftServo.write(leftOcc?UP_ANGLE:DOWN_ANGLE);
 centerServo.write(centerOcc?UP_ANGLE:DOWN_ANGLE);
 rightServo.write(rightOcc?UP_ANGLE:DOWN_ANGLE);
}
void handleState(){
 if(server.hasArg("left")) leftOcc=server.arg("left")=="1";
 if(server.hasArg("center")) centerOcc=server.arg("center")=="1";
 if(server.hasArg("right")) rightOcc=server.arg("right")=="1";
 updateServos();
 server.send(200,"text/plain","OK");
}
void handleRoot(){
 String h="<!doctype html><html><meta http-equiv='refresh' content='1'><body><h2>Blind Navigation</h2>";
 h+="<p>LEFT: ";h+=(leftOcc?"ACTIVE":"OFF");h+="</p><p>CENTER: ";h+=(centerOcc?"ACTIVE":"OFF");h+="</p><p>RIGHT: ";h+=(rightOcc?"ACTIVE":"OFF");h+="</p></body></html>";
 server.send(200,"text/html",h);
}
void setup(){
 Serial.begin(115200);
 leftServo.attach(LEFT_PIN);centerServo.attach(CENTER_PIN);rightServo.attach(RIGHT_PIN);
 updateServos();
 WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
 while(WiFi.status()!=WL_CONNECTED){delay(500);}
 Serial.println(WiFi.localIP());
 server.on("/",handleRoot);
 server.on("/state",HTTP_GET,handleState);
 server.begin();
}
void loop(){server.handleClient();}
