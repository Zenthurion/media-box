#include "connections_manager.h"

ConnectionsManager::ConnectionsManager(const char* ssid, const char* password, 
                        const char* mqtt_server, const int mqtt_port) 
    : ssid(ssid)
    , password(password)
    , mqtt_server(mqtt_server)
    , mqtt_port(mqtt_port)
    , mqttClient(espClient) {
}

void ConnectionsManager::begin() {
    connectWiFi();
    mqttClient.setServer(mqtt_server, mqtt_port);
}

bool ConnectionsManager::loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi disconnected, attempting to reconnect...");
        connectWiFi();
        return false;
    }
    
    if (!mqttClient.connected()) {
        Serial.println("MQTT disconnected, attempting to reconnect...");
        connectMQTT();
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
        Serial.println("MQTT disconnected, attempting to reconnect...");
        if (!connectMQTT()) {
            return false;
        }
    }
    return mqttClient.publish(topic, message);
}

void ConnectionsManager::connectWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.disconnect(true);
    WiFi.setHostname("button-controller");
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\nWiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
}

bool ConnectionsManager::connectMQTT() {
    int attempts = 0;
    const int maxAttempts = 3;  // Limit reconnection attempts
    
    while (!mqttClient.connected() && attempts < maxAttempts) {
        String clientId = "NFCReader-";
        clientId += String(random(0xffff), HEX);

        Serial.print("Attempting MQTT connection for client ");
        Serial.print(clientId);
        Serial.print("... ");
        
        
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