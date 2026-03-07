#include "nfc_reader.h"
#include "connections_manager.h"
#include "secrets.h"

// Pin definitions
#define SS_PIN 27 // SPI Slave Select pin (output-capable)
#define RED_PIN 4
#define GREEN_PIN 5
#define BLUE_PIN 22
#define BUTTON_PIN 13 // Manual button test message trigger

// Create objects
NFCReader nfcReader(SS_PIN);
ConnectionsManager connectionsManager(WIFI_SSID, WIFI_PASSWORD, MQTT_SERVER, MQTT_PORT);

const char *mqtt_topic = "media/url";

void setup()
{
    Serial.begin(115200);

    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    // Turn off all LED colors initially
    digitalWrite(RED_PIN, LOW);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);

    nfcReader.begin();
    Serial.println("NFC Reader Ready!");

    connectionsManager.begin();
    Serial.printf("MQTT target: %s:%d\n", MQTT_SERVER, MQTT_PORT);
    Serial.printf("Publishing NFC URLs to topic: %s\n", mqtt_topic);
    // Serial.println("Button test started");
}

void setLEDColor(bool red, bool green, bool blue)
{
    digitalWrite(RED_PIN, red);
    digitalWrite(GREEN_PIN, green);
    digitalWrite(BLUE_PIN, blue);
}

void indicateSuccess(int duration = 1000)
{
    setLEDColor(false, true, false); // Green
    delay(duration);
    setLEDColor(false, false, false); // Off
}

void indicateError(int duration = 1000)
{
    setLEDColor(true, false, false); // Red
    delay(duration);
    setLEDColor(false, false, false); // Off
}

void indicateReading(int duration = 200)
{
    setLEDColor(false, false, true); // Blue
    delay(duration);
    setLEDColor(false, false, false); // Off
}

bool isButtonPressed()
{
    static bool lastState = HIGH;
    static unsigned long lastDebounceTime = 0;
    const unsigned long debounceDelay = 50;

    bool currentState = digitalRead(BUTTON_PIN);

    if (currentState == LOW && lastState == HIGH)
    {
        lastState = currentState;
        Serial.println("Button press detected!");
        return true;
    }

    lastState = currentState;
    return false;
}

void loop()
{
    // Check WiFi status
    if (!connectionsManager.loop())
    {
        static unsigned long lastConnectionLog = 0;
        unsigned long now = millis();
        if (now - lastConnectionLog > 5000)
        {
            Serial.println("Waiting for WiFi/MQTT connection...");
            lastConnectionLog = now;
        }
        indicateError(200); // Short red flash to show connection issues
        delay(1000);
        return;
    }

    // Handle button press
    if (isButtonPressed())
    {
        const char *predefinedMessage = "https://music.youtube.com/watch?v=CTvjhbfrgEY";
        Serial.printf("Publishing test URL to %s: %s\n", mqtt_topic, predefinedMessage);

        bool publishResult = connectionsManager.publish(mqtt_topic, predefinedMessage);

        if (publishResult)
        {
            Serial.printf("Publish OK to %s\n", mqtt_topic);
            indicateSuccess();
        }
        else
        {
            Serial.printf("Publish FAILED to %s\n", mqtt_topic);
            indicateError();
        }
        Serial.println("------------------");
        delay(200);
    }

    // Handle NFC reading
    String ndefData = nfcReader.readNDEFMessage();
    if (ndefData.length() > 0)
    {
        indicateReading(); // Blue flash when tag is read

        Serial.print("NDEF Data: ");
        Serial.println(ndefData);
        Serial.printf("Publishing NFC URL to %s (len=%d)\n", mqtt_topic, ndefData.length());

        if (connectionsManager.publish(mqtt_topic, ndefData.c_str()))
        {
            Serial.printf("Publish OK to %s\n", mqtt_topic);
            indicateSuccess(); // Green light for successful send
        }
        else
        {
            Serial.printf("Publish FAILED to %s\n", mqtt_topic);
            indicateError(); // Red light for error
        }
    }

    delay(100);
}
