#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>

class WiFiManager {
private:
    const char* ssid;
    const char* password;
    const char* mqtt_server;
    const int mqtt_port;
    
    WiFiClient espClient;
    PubSubClient mqttClient;

public:
    WiFiManager(const char* ssid, const char* password, 
                const char* mqtt_server, const int mqtt_port);
    void begin();
    bool loop();
    bool publish(const char* topic, const char* message);
    
private:
    void connectWiFi();
    bool reconnectMQTT();
};

#endif 