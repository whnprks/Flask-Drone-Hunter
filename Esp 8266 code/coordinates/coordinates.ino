#include <SPI.h>
#include <Ethernet.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x44};
IPAddress ip(192, 168, 0, 2);

EthernetServer server(5000);

StaticJsonDocument<256> jsonDoc; // Using StaticJsonDocument
String jsonResponse; // Declare jsonResponse

LiquidCrystal_I2C lcd(0x27, 20, 4); // Adjust I2C address as needed

void setup() {
  // LCD
  lcd.clear();
  lcd.init();                      // initialize the lcd
  lcd.backlight();
  // Print a message to the LCD.
  lcd.setCursor(3, 0);
  lcd.print("Drone Detection");
  lcd.setCursor(0, 2);
  lcd.print("Coordinates :");

  Ethernet.init(D3);

  Serial.begin(9600);
  while (!Serial) {
    ;
  }
  Serial.println("Ethernet WebServer Example");

  Ethernet.begin(mac, ip);
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("Ethernet shield was not found. Sorry, can't run without hardware. :(");
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // Start the server
  server.begin();
  Serial.print("server is at ");
  Serial.println(Ethernet.localIP());
}

void loop() {
  EthernetClient client = server.available();

  if (client) {
    Serial.println("New connection.");

    // Read HTTP request until '\r'
    String request = client.readStringUntil('\r');
    if (request.indexOf("POST /api HTTP/1.1") != -1) {
      // Read JSON data from the request body
      String jsonRaw = "";
      bool jsonStarted = false;

      while (client.available()) {
        char c = client.read();

        if (c == '{') {
          jsonStarted = true;
        }

        if (jsonStarted) {
          jsonRaw += c;
        }
      }

      jsonDoc.clear(); // Clear the JSON document before filling it again

      DeserializationError error = deserializeJson(jsonDoc, jsonRaw);

      if (!error) {
        int XCoord = jsonDoc["XCoord"].as<int>();
        int YCoord = jsonDoc["YCoord"].as<int>();

        Serial.println("Received data from client: ");
        Serial.print("X : ");
        Serial.println(XCoord);
        Serial.print("Y : ");
        Serial.println(YCoord);

        if (XCoord == 0 && YCoord == 0) {
          // Handle the case when XCoord and YCoord are both 0
          lcd.setCursor(3, 3);
          lcd.print("                ");
        } else {
          String formattedCoord = "X:" + String(XCoord) + " - Y:" + String(YCoord);
          // Menghapus data sebelumnya dan menampilkan koordinat
          lcd.setCursor(3, 3);
          lcd.print("                ");
          lcd.setCursor(3, 3);
          lcd.print(formattedCoord);
        }

        // Create HTTP OK response with content type application/json
        client.print("HTTP/1.1 200 OK\r\n");
        client.print("Content-Type: application/json\r\n");
        client.print("Connection: close\r\n\r\n");
        client.print(jsonResponse);
      } else {
        // Invalid JSON data
        client.print("HTTP/1.1 400 Bad Request\r\n");
        client.print("Content-Type: application/json\r\n");
        client.print("Connection: close\r\n\r\n");
        client.print("{\"status\": \"fail\", \"message\": \"Invalid JSON data\"}");
      }
      delay(1);
      client.stop();
      Serial.println("client disconnected");
      Serial.println("===============================");
    }
  } else if (!client.connected()) {
    // Clear previous data and display "Test"
    lcd.setCursor(3, 3);
    lcd.print("                ");

  }
  delay(500);
}
