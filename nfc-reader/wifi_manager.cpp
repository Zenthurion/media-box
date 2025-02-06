#include "wifi_manager.h"

WiFiManager::WiFiManager(const char* ssid, const char* password, 
                        const char* mqtt_server, const int mqtt_port) 
    : ssid(ssid)
    , password(password)
    , mqtt_server(mqtt_server)
    , mqtt_port(mqtt_port)
    , mqttClient(espClient) {
}

void WiFiManager::begin() {
    connectWiFi();
    mqttClient.setServer(mqtt_server, mqtt_port);
}

bool WiFiManager::loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi disconnected, attempting to reconnect...");
        connectWiFi();
        return false;
    }
    
    if (!mqttClient.connected()) {
        Serial.println("MQTT disconnected, attempting to reconnect...");
        reconnectMQTT();
        return false;
    }
    
    mqttClient.loop();
    return true;
}

bool WiFiManager::publish(const char* topic, const char* message) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi disconnected, cannot publish");
        return false;
    }
    
    if (!mqttClient.connected()) {
        Serial.println("MQTT disconnected, attempting to reconnect...");
        if (!reconnectMQTT()) {
            return false;
        }
    }
    return mqttClient.publish(topic, message);
}

void WiFiManager::connectWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\nWiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
}

bool WiFiManager::reconnectMQTT() {
    int attempts = 0;
    const int maxAttempts = 3;  // Limit reconnection attempts
    
    while (!mqttClient.connected() && attempts < maxAttempts) {
        Serial.print("Attempting MQTT connection...");
        
        String clientId = "NFCReader-";
        clientId += String(random(0xffff), HEX);
        
        if (mqttClient.connect(clientId.c_str())) {
            Serial.println("connected");
            return true;
        } else {
            attempts++;
            Serial.print("failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" trying again in 2 seconds");
            delay(2000);
        }
    }
    return false;
} 