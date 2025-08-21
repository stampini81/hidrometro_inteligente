#include "config.h"
#include <WiFi.h>
#include <WebServer.h>
#include <LiquidCrystal_I2C.h>
#include <RTClib.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>

// Protótipo da função de interrupção para evitar erros de compilação
void IRAM_ATTR flowPulseCounter();

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLS, LCD_ROWS);
RTC_DS3231 rtc;
WebServer server(80);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

const int LED_STATUS_PIN = 13;
volatile int flowPulseCount = 0;
float totalLiters = 0.0;
float currentFlowRate = 0.0;
unsigned long oldTime = 0;
float calibrationFactor = CALIBRATION_FACTOR;
bool systemActive = true;
// Simulação
bool simEnabled = false;
float simFlowTarget = 0.0; // L/min desejado na simulação
double simPulseFrac = 0.0; // acumulador de frações de pulso

struct ConsumptionData {
  DateTime timestamp;
  float consumption;
  float flowRate;
};

ConsumptionData history[HISTORY_SIZE];
int historyIndex = 0;

const char index_html[] PROGMEM = R"rawliteral(
<!doctype html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>Hidrometro Inteligente</title>
  <style>
    body{font-family:Arial,Helvetica,sans-serif;background:#f4f6f9;margin:0;padding:20px}
    .card{background:white;border-radius:8px;padding:20px;box-shadow:0 6px 18px rgba(0,0,0,.08);max-width:900px;margin:20px auto}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    @media(max-width:720px){.grid{grid-template-columns:1fr}}
    .value{font-size:28px;color:#1976d2}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Hidrômetro Inteligente</h1>
    <p>Acesse <a href=\"/api/current\">/api/current</a> para ver os dados em JSON.</p>
    <div class=\"grid\">
      <div>
        <strong>Total Consumido (L)</strong>
        <div id=\"total\" class=\"value\">0.0</div>
      </div>
      <div>
        <strong>Vazão Atual (L/min)</strong>
        <div id=\"flow\" class=\"value\">0.0</div>
      </div>
    </div>
  </div>
  <script>
    function refreshData(){
      fetch('/api/current').then(res => res.json()).then(data => {
        document.getElementById('total').textContent = data.totalLiters.toFixed(1);
        document.getElementById('flow').textContent = data.currentFlow_L_min.toFixed(1);
      }).catch(e => console.error(e));
    }
    setInterval(refreshData, 2000);
    window.onload = refreshData;
  </script>
</body>
</html>
)rawliteral";

unsigned long getUnixTime() {
  return rtc.now().unixtime();
}

void setup() {
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);
  pinMode(LED_STATUS_PIN, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseCounter, FALLING);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Hidrometro Smart");
  lcd.setCursor(0, 1);
  lcd.print("Inicializando...");
  delay(1000);
  if (!rtc.begin()) {
    Serial.println("RTC nao encontrado!");
    lcd.setCursor(0, 1);
    lcd.print("Erro RTC!       ");
    while (1);
  }
  setupWiFi();
  setupWebServer();
  setupMQTT();
  loadSavedData();
  Serial.println("Sistema inicializado!");
  lcd.clear();
  oldTime = millis();
  updateDisplay();
}

void loop() {
  server.handleClient();
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  if ((millis() - oldTime) >= UPDATE_INTERVAL) {
    detachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN));
    // Gera pulsos simulados para atingir um fluxo alvo, se habilitado
    if (simEnabled && simFlowTarget > 0.0f) {
      // frequency (pulsos/s) = fluxo(L/min) * calibrationFactor
      double pulsesThisTick = (double)simFlowTarget * (double)calibrationFactor * ((double)UPDATE_INTERVAL / 1000.0);
      pulsesThisTick += simPulseFrac; // adiciona fração acumulada
      long addInt = (long)pulsesThisTick; // parte inteira de pulsos
      simPulseFrac = pulsesThisTick - (double)addInt; // guarda fração restante
      if (addInt > 0) {
        // adiciona aos pulsos medidos no período
        flowPulseCount += (int)addInt;
      }
    }
    float frequency = (float)flowPulseCount / (UPDATE_INTERVAL / 1000.0);
    currentFlowRate = frequency / calibrationFactor;
    totalLiters += currentFlowRate * (UPDATE_INTERVAL / 60000.0);
    flowPulseCount = 0;
    oldTime = millis();
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseCounter, FALLING);
    DateTime now = DateTime(getUnixTime());
    if (now.minute() == 0 && now.second() < 2) {
      saveHourlyData();
    }
    updateDisplay();
  publishCurrentDataMQTT();
    static unsigned long lastSaveTime = 0;
    if (millis() - lastSaveTime >= SAVE_INTERVAL) {
      saveDataToEEPROM();
      lastSaveTime = millis();
    }
  }
  digitalWrite(LED_STATUS_PIN, (millis() / 500) % 2);
}

void IRAM_ATTR flowPulseCounter() {
  flowPulseCount++;
}

void setupWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lcd.setCursor(0, 1);
  lcd.print("Conectando WiFi ");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    lcd.setCursor(0, 1);
    lcd.print("IP:             ");
    delay(1000);
    lcd.setCursor(0,1);
    lcd.print(WiFi.localIP());
  } else {
    Serial.println("\nFalha ao conectar no WiFi");
    lcd.setCursor(0, 1);
    lcd.print("WiFi Falhou      ");
  }
  delay(2000);
}

void setupWebServer() {
  server.on("/", handleRoot);
  server.on("/api/current", handleCurrentData);
  server.on("/api/history", handleHistoryData);
  server.on("/api/config", HTTP_POST, handleConfig);
  server.on("/api/reset", HTTP_POST, handleReset);
  // Ativa/desativa simulação direto via HTTP: /api/sim?flow=8  ou  /api/sim?off=1
  server.on("/api/sim", [](){
    if (server.hasArg("off")) {
      simEnabled = false; simFlowTarget = 0.0; simPulseFrac = 0.0;
      server.send(200, "application/json", "{\"ok\":true,\"sim\":false}");
      return;
    }
    float v = server.hasArg("flow") ? server.arg("flow").toFloat() : 0.0;
    if (v > 0) { simEnabled = true; simFlowTarget = v; }
    String resp = String("{\"ok\":true,\"sim\":") + (simEnabled?"true":"false") + ",\"flow\":" + String(simFlowTarget,1) + "}";
    server.send(200, "application/json", resp);
  });
  server.begin();
  Serial.println("Servidor web iniciado!");
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  if (String(topic) == MQTT_CMD_TOPIC) {
    // comandos suportados: {"action":"reset"} ou {"action":"setCalibration","value":7.5}
    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, msg);
    if (!err) {
      String action = doc["action"] | "";
      if (action == "reset") {
        totalLiters = 0.0;
        historyIndex = 0;
        for (int i=0;i<HISTORY_SIZE;i++) history[i] = ConsumptionData();
        saveDataToEEPROM();
      } else if (action == "setCalibration") {
        float v = doc["value"] | 0.0;
        if (v > 0) { calibrationFactor = v; saveConfigToEEPROM(); }
      } else if (action == "simulate" || action == "simSetFlow") {
        float v = doc["value"] | 0.0;
        if (v > 0) {
          simEnabled = true;
          simFlowTarget = v; // L/min
        }
      } else if (action == "simOff" || action == "simulateOff") {
        simEnabled = false;
        simFlowTarget = 0.0;
      }
    }
  }
}

void setupMQTT() {
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
}

void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  while (!mqttClient.connected()) {
    String clientId = String("hidrometro-") + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      mqttClient.subscribe(MQTT_CMD_TOPIC);
    } else {
      delay(1000);
      break; // sai e tenta novamente no próximo loop
    }
  }
}

void publishCurrentDataMQTT() {
  StaticJsonDocument<256> doc;
  doc["ts"] = getUnixTime();
  doc["totalLiters"] = totalLiters;
  doc["flowLmin"] = currentFlowRate;
  char buf[256];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  mqttClient.publish(MQTT_PUB_TOPIC, buf, n);
}

void updateDisplay() {
  lcd.setCursor(0, 0);
  lcd.print("Total: ");
  lcd.print(totalLiters, 1);
  lcd.print(" L ");
  lcd.setCursor(0, 1);
  lcd.print("Vazao: ");
  lcd.print(currentFlowRate, 1);
  lcd.print(" L/min");
}

void handleRoot() {
  String html = String(index_html);
  server.send(200, "text/html", html);
}

void handleCurrentData() {
  DynamicJsonDocument doc(1024);
  doc["timestamp"] = getUnixTime();
  doc["totalLiters"] = totalLiters;
  doc["currentFlow_L_min"] = currentFlowRate;
  doc["systemActive"] = systemActive;
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handleHistoryData() {
  DynamicJsonDocument doc(4096);
  JsonArray data = doc.createNestedArray("history");
  for (int i = 0; i < HISTORY_SIZE; i++) {
    if (history[i].timestamp.isValid()) {
      JsonObject entry = data.createNestedObject();
      entry["timestamp"] = history[i].timestamp.unixtime();
      entry["consumption"] = history[i].consumption;
      entry["flowRate_L_min"] = history[i].flowRate;
    }
  }
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handleConfig() {
  if (server.hasArg("calibration")) {
    calibrationFactor = server.arg("calibration").toFloat();
    saveConfigToEEPROM();
    server.send(200, "text/plain", "Configuracao salva!");
  } else {
    server.send(400, "text/plain", "Argumento 'calibration' ausente.");
  }
}

void handleReset() {
  totalLiters = 0.0;
  for (int i = 0; i < HISTORY_SIZE; i++) {
    history[i] = ConsumptionData();
  }
  historyIndex = 0;
  saveDataToEEPROM();
  server.send(200, "text/plain", "Sistema resetado!");
}

void saveHourlyData() {
  DateTime now = DateTime(getUnixTime());
  history[historyIndex] = {now, totalLiters, currentFlowRate};
  historyIndex = (historyIndex + 1) % HISTORY_SIZE;
}

void saveDataToEEPROM() {
  EEPROM.put(0, totalLiters);
  EEPROM.put(sizeof(totalLiters), calibrationFactor);
  EEPROM.commit();
  Serial.println("Dados salvos na EEPROM.");
}

void loadSavedData() {
  EEPROM.get(0, totalLiters);
  if (isnan(totalLiters)) totalLiters = 0.0;
  EEPROM.get(sizeof(totalLiters), calibrationFactor);
  if (isnan(calibrationFactor) || calibrationFactor == 0) {
    calibrationFactor = CALIBRATION_FACTOR;
  }
}

void saveConfigToEEPROM() {
  saveDataToEEPROM();
}
