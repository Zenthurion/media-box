#include "connections_manager.h"
#include "secrets.h"

#define BUTTON_PLAY 33
#define BUTTON_STOP 22

#define RED_PIN 25
#define GREEN_PIN 26
#define BLUE_PIN 27

const char *mqttTopics[] = {
    "media/command",   // media play/pause/stop/etc.
    "media/command"};

const char *mqttPayloads[] = {
    "Play",
    "Stop"};

const uint8_t buttonPins[] = {
    BUTTON_PLAY,
    BUTTON_STOP};

#define NUM_BUTTONS 2

ConnectionsManager connectionsManager(WIFI_SSID, WIFI_PASSWORD, MQTT_SERVER, MQTT_PORT);

// Better debounce tracking
bool lastButtonStates[NUM_BUTTONS] = {HIGH, HIGH};
bool buttonPressed[NUM_BUTTONS] = {false, false};
unsigned long lastDebounceTimes[NUM_BUTTONS] = {0, 0};
bool stableStates[NUM_BUTTONS] = {HIGH, HIGH};
const unsigned long debounceDelay = 50;

const char *buttonNames[] = {
    "PLAY",
    "STOP"};

void setup()
{
  Serial.begin(115200);
  Serial.println("Button Controller Starting...");

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  for (int i = 0; i < NUM_BUTTONS; i++)
  {
    pinMode(buttonPins[i], INPUT_PULLUP);

    bool initialState = digitalRead(buttonPins[i]);
    Serial.printf("Button %s (GPIO%d) initialized with INPUT_PULLUP, initial state: %s\n",
                  buttonNames[i], buttonPins[i], initialState == HIGH ? "HIGH" : "LOW");
    lastButtonStates[i] = initialState;
    stableStates[i] = initialState;
  }

  // Test LED indication
  Serial.println("Testing LEDs...");
  setLEDColor(true, true, true); // White
  delay(500);
  setLEDColor(false, false, false);

  connectionsManager.begin();

  Serial.println("Setup complete. Monitoring buttons...");
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
  setLEDColor(false, false, false);
}

void indicateError(int duration = 1000)
{
  setLEDColor(true, false, false); // Red
  delay(duration);
  setLEDColor(false, false, false);
}

void checkButtons()
{
  for (int i = 0; i < NUM_BUTTONS; i++)
  {
    bool currentState = digitalRead(buttonPins[i]);

    if (currentState != lastButtonStates[i])
    {
      lastDebounceTimes[i] = millis();
    }

    if ((millis() - lastDebounceTimes[i]) > debounceDelay)
    {
      if (currentState != stableStates[i])
      {
        bool oldStableState = stableStates[i];
        stableStates[i] = currentState;

        if (oldStableState == HIGH && stableStates[i] == LOW && !buttonPressed[i])
        {
          Serial.printf("Button %s PRESSED -> Publishing to %s\n", buttonNames[i], mqttTopics[i]);
          buttonPressed[i] = true; // Mark as processed

          bool publishOk = connectionsManager.publish(mqttTopics[i], mqttPayloads[i]);

          if (publishOk)
          {
            indicateSuccess(200);
          }
          else
          {
            indicateError(200);
          }
        }

        else if (oldStableState == LOW && stableStates[i] == HIGH)
        {
          buttonPressed[i] = false;
        }
      }
    }

    lastButtonStates[i] = currentState;
  }
}

void loop()
{
  static int lastPlay = -1;
  int raw = digitalRead(BUTTON_PLAY);
  if (raw != lastPlay)
  {
    Serial.printf("Play raw: %d\n", raw);
    lastPlay = raw;
  }
  if (!connectionsManager.loop())
  {
    ConnectionStatus status = connectionsManager.getStatus();

    switch (status)
    {
    case ConnectionStatus::WIFI_DISCONNECTED:
      Serial.println("WiFi connection lost!");
      break;
    case ConnectionStatus::WIFI_CONNECTING:
      Serial.println("WiFi connecting...");
      break;
    case ConnectionStatus::MQTT_NOT_CONNECTED:
      Serial.println("MQTT connection lost!");
      break;
    case ConnectionStatus::MQTT_CONNECTING:
      Serial.println("MQTT connecting...");
      break;
    case ConnectionStatus::CONNECTED:
      Serial.println("Connected!");
      break;
    default:
      Serial.printf("Unknown connection status: %d!", status);
      break;
    }

    indicateError(200);
    delay(1000);
    return;
  }

  checkButtons();
  delay(50);
}
