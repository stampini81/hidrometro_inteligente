#ifndef CONFIG_H
#define CONFIG_H

// Rede WiFi (Wokwi usa Wokwi-GUEST por padrão)
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// Sensor e calibração
#define FLOW_SENSOR_PIN 2
#define CALIBRATION_FACTOR 7.5

// LCD I2C
#define LCD_ADDRESS 0x27
#define LCD_COLS 16
#define LCD_ROWS 2

// Memória e histórico
#define EEPROM_SIZE 512
#define HISTORY_SIZE 24

// Intervalos (ms)
#define UPDATE_INTERVAL 1000
#define SAVE_INTERVAL 60000

// MQTT (broker público por padrão)
#define MQTT_BROKER "broker.hivemq.com"
#define MQTT_PORT 1883
#define MQTT_BASE_TOPIC "hidrometro/leandro"
#define MQTT_PUB_TOPIC MQTT_BASE_TOPIC "/dados"
#define MQTT_CMD_TOPIC MQTT_BASE_TOPIC "/cmd"

#endif
