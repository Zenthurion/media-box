#include "connections_manager.h"
#include "secrets.h"

#define BUTTON_PLAY 33
#define BUTTON_STOP 22
#define BUTTON_SHUTDOWN 19
#define BUTTON_START 21

#define RED_PIN 25
#define GREEN_PIN 26
#define BLUE_PIN 27

#define MOSFET_GATE_PIN 5 // P-FET gate: LOW = ON (pulls low to power Pi)
#define PI_ALIVE_PIN 18   // From Pi GPIO7

const char *mqttTopics[] = {
    "media/command",   // media play/pause/stop/etc.
    "media/command",
    "system/command",  // system controls (Start/Shutdown)
    "system/command"};

const char *mqttPayloads[] = {
    "Play",
    "Stop",
    "Shutdown",
    "Start"};

const uint8_t buttonPins[] = {
    BUTTON_PLAY,
    BUTTON_STOP,
    BUTTON_SHUTDOWN,
    BUTTON_START};

#define NUM_BUTTONS 4

ConnectionsManager connectionsManager(WIFI_SSID, WIFI_PASSWORD, MQTT_SERVER, MQTT_PORT);

// Better debounce tracking
bool lastButtonStates[NUM_BUTTONS] = {HIGH, HIGH, HIGH, HIGH};
bool buttonPressed[NUM_BUTTONS] = {false, false, false, false};
unsigned long lastDebounceTimes[NUM_BUTTONS] = {0, 0, 0, 0};
bool stableStates[NUM_BUTTONS] = {HIGH, HIGH, HIGH, HIGH};
const unsigned long debounceDelay = 50;

const char *buttonNames[] = {
    "PLAY",
    "STOP",
    "SHUTDOWN",
    "START"};

// Shutdown monitoring
bool shutdownRequested = false;
unsigned long shutdownRequestTime = 0;
unsigned long aliveLowSince = 0;
const unsigned long shutdownTimeoutMs = 60000; // how long to wait before giving up
const unsigned long aliveLowStableMs = 2000;   // require low for this long before power cut

void setup()
{
  Serial.begin(115200);
  Serial.println("Button Controller Starting...");

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  // Power control: default OFF (gate pulled high), watch Pi alive signal
  pinMode(MOSFET_GATE_PIN, OUTPUT);
  digitalWrite(MOSFET_GATE_PIN, HIGH); // off until Start button
  pinMode(PI_ALIVE_PIN, INPUT_PULLDOWN);

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

          // Handle start/shutdown locally
          if (i == 3) // START
          {
            Serial.println("Start button: enabling Pi power.");
            digitalWrite(MOSFET_GATE_PIN, LOW); // turn power on
            shutdownRequested = false;
            aliveLowSince = 0;
          }
          else if (i == 2) // SHUTDOWN
          {
            Serial.println("Shutdown button: requesting Pi shutdown and waiting to cut power.");
            shutdownRequested = true;
            shutdownRequestTime = millis();
            aliveLowSince = 0;
          }

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

void handleShutdownMonitor()
{
  if (!shutdownRequested)
  {
    return;
  }

  unsigned long now = millis();
  int alive = digitalRead(PI_ALIVE_PIN);

  if (alive == LOW)
  {
    if (aliveLowSince == 0)
    {
      aliveLowSince = now;
    }
    else if ((now - aliveLowSince) >= aliveLowStableMs)
    {
      Serial.println("Pi reported down; cutting power.");
      digitalWrite(MOSFET_GATE_PIN, HIGH); // turn Pi power off
      shutdownRequested = false;
      aliveLowSince = 0;
      indicateSuccess(300);
    }
  }
  else
  {
    aliveLowSince = 0; // still alive, reset low timer
  }

  if (now - shutdownRequestTime > shutdownTimeoutMs)
  {
    Serial.println("Shutdown timeout: Pi still alive. Leaving power ON.");
    shutdownRequested = false; // stop waiting; do not cut power
    aliveLowSince = 0;
    indicateError(300);
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
  handleShutdownMonitor();
  delay(50);
}
