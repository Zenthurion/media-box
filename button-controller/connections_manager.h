#ifndef CONNECTIONS_MANAGER_H
#define CONNECTIONS_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>

enum class ConnectionStatus {
    CONNECTED,
    WIFI_DISCONNECTED,
    MQTT_NOT_CONNECTED,
    WIFI_CONNECTING,
    MQTT_CONNECTING
};

class ConnectionsManager {
private:
    const char* ssid;
    const char* password;
    const char* mqtt_server;
    const int mqtt_port;
    
    WiFiClient espClient;
    PubSubClient mqttClient;
    
    unsigned long lastWifiAttempt;
    unsigned long lastMqttAttempt;

    static constexpr unsigned long wifiRetryIntervalMs = 5000;
    static constexpr unsigned long mqttRetryIntervalMs = 5000;

public:
    ConnectionsManager(const char* ssid, const char* password, 
                const char* mqtt_server, const int mqtt_port);
    void begin();
    bool loop();
    bool publish(const char* topic, const char* message);
    ConnectionStatus getStatus();
    
private:
    void connectWiFi();
    bool connectMQTT();
};

#endif 
