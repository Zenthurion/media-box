#include "connections_manager.h"

ConnectionsManager::ConnectionsManager(const char* ssid, const char* password, 
                        const char* mqtt_server, const int mqtt_port) 
    : ssid(ssid)
    , password(password)
    , mqtt_server(mqtt_server)
    , mqtt_port(mqtt_port)
    , mqttClient(espClient)
    , lastWifiAttempt(0)
    , lastMqttAttempt(0) {
}

void ConnectionsManager::begin() {
    WiFi.setHostname("button-controller");
    WiFi.mode(WIFI_STA);
    WiFi.persistent(false);
    WiFi.setAutoReconnect(true);
    lastWifiAttempt = millis() - wifiRetryIntervalMs; // force an immediate attempt
    connectWiFi();
    mqttClient.setServer(mqtt_server, mqtt_port);
    lastMqttAttempt = millis() - mqttRetryIntervalMs; // allow immediate MQTT attempt once WiFi is up
}

bool ConnectionsManager::loop() {
    unsigned long now = millis();

    // Handle WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        if (now - lastWifiAttempt >= wifiRetryIntervalMs) {
            Serial.println("WiFi disconnected, attempting to reconnect...");
            connectWiFi();
        }
        return false;
    }
    
    // Handle MQTT connection
    if (!mqttClient.connected()) {
        if (now - lastMqttAttempt >= mqttRetryIntervalMs) { // Only attempt every retry window
            Serial.println("MQTT disconnected, attempting to reconnect...");
            lastMqttAttempt = now;
            connectMQTT();
        }
        return false;
    }
    
    mqttClient.loop();
    return true;
}

bool ConnectionsManager::publish(const char* topic, const char* message) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi disconnected, cannot publish");
        return false;
    }
    
    if (!mqttClient.connected()) {
        Serial.println("MQTT disconnected, cannot publish");
        return false; // Let loop() handle reconnection
    }
    
    return mqttClient.publish(topic, message);
}

String getClientId() {
  uint64_t chipId = ESP.getEfuseMac(); // 64-bit MAC address
  char idBuffer[32];
  snprintf(idBuffer, sizeof(idBuffer), "Buttons-%04X", (uint16_t)(chipId >> 32 ^ chipId));
  return String(idBuffer);
}


ConnectionStatus ConnectionsManager::getStatus() {
    if (WiFi.status() != WL_CONNECTED) {
        unsigned long now = millis();
        if (now - lastWifiAttempt < wifiRetryIntervalMs) {
            return ConnectionStatus::WIFI_CONNECTING;
        }
        return ConnectionStatus::WIFI_DISCONNECTED;
    }
    
    if (!mqttClient.connected()) {
        unsigned long now = millis();
        if (now - lastMqttAttempt < mqttRetryIntervalMs) {
            return ConnectionStatus::MQTT_CONNECTING;
        }
        return ConnectionStatus::MQTT_NOT_CONNECTED;
    }
    
    return ConnectionStatus::CONNECTED;
}

void ConnectionsManager::connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) {
        return; // Already connected
    }
    
    lastWifiAttempt = millis();
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
}

bool ConnectionsManager::connectMQTT() {
    if (mqttClient.connected()) {
        return true; // Already connected
    }
    
    static String clientId = getClientId();
    
    Serial.print("Attempting MQTT connection for client ");
    Serial.print(clientId);
    Serial.print("... ");
    
    if (mqttClient.connect(clientId.c_str())) {
        Serial.println("connected");
        return true;
    } else {
        Serial.print("failed, rc=");
        Serial.println(mqttClient.state());
        return false;
    }
} 
