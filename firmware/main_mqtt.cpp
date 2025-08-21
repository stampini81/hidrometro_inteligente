#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void setupWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void setupMQTT() {
  mqttClient.setServer("broker.hivemq.com", 1883);
}

void publishData(float totalLiters, float flowRate) {
  String payload = String("{\"totalLiters\":") + totalLiters + ",\"flowRate\":" + flowRate + "}";
  mqttClient.publish("hidrometro/leandro/dados", payload.c_str());
}

void setup() {
  Serial.begin(115200);
  setupWiFi();
  setupMQTT();
}

void loop() {
  if (!mqttClient.connected()) {
    mqttClient.connect("hidrometroClient");
  }
  mqttClient.loop();
  // Simulação de dados
  float totalLiters = 123.4;
  float flowRate = 5.6;
  publishData(totalLiters, flowRate);
  delay(5000);
}
