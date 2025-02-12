#include "nfc_reader.h"
#include "wifi_manager.h"
#include "secrets.h"

// Pin definitions
#define SS_PIN 5
#define RST_PIN 4
#define RED_PIN 22   // RGB LED pins - adjust these
#define GREEN_PIN 15 // according to your wiring
#define BLUE_PIN 21
#define BUTTON_PIN 13 // Add button pin - adjust as needed

// Create objects
NFCReader nfcReader(SS_PIN, RST_PIN);
WiFiManager wifiManager(WIFI_SSID, WIFI_PASSWORD, MQTT_SERVER, MQTT_PORT);

const char *mqtt_topic = "nfc/url";

void setup()
{
    Serial.begin(115200);

    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP); // Add button pin mode

    // Turn off all LED colors initially
    digitalWrite(RED_PIN, LOW);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);

    nfcReader.begin();
    Serial.println("NFC Reader Ready!");

    wifiManager.begin();
    Serial.println("Button test started");
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
    if (!wifiManager.loop())
    {
        Serial.println("WiFi or MQTT connection lost!");
        indicateError(200); // Short red flash to show connection issues
        delay(1000);
        return;
    }

    // Handle button press
    if (isButtonPressed())
    {
        const char *predefinedMessage = "https://music.youtube.com/watch?v=CTvjhbfrgEY";

        bool publishResult = wifiManager.publish(mqtt_topic, predefinedMessage);

        if (publishResult)
        {
            Serial.println("Successfully sent button press to MQTT");
            indicateSuccess();
        }
        else
        {
            Serial.println("Failed to send button press to MQTT");
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

        if (wifiManager.publish(mqtt_topic, ndefData.c_str()))
        {
            Serial.println("Sent to MQTT: " + ndefData);
            indicateSuccess(); // Green light for successful send
        }
        else
        {
            indicateError(); // Red light for error
        }
    }

    delay(100);
}
