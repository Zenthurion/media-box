#ifndef CONNECTIONS_MANAGER_H
#define CONNECTIONS_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>

class ConnectionsManager {
private:
    const char* ssid;
    const char* password;
    const char* mqtt_server;
    const int mqtt_port;
    
    WiFiClient espClient;
    PubSubClient mqttClient;

public:
    ConnectionsManager(const char* ssid, const char* password, 
                const char* mqtt_server, const int mqtt_port);
    void begin();
    bool loop();
    bool publish(const char* topic, const char* message);
    
private:
    void connectWiFi();
    bool connectMQTT();
};

#endif 