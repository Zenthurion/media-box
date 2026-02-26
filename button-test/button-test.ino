#define BUTTON_PIN 4  // Change to your test GPIO
#define LED_PIN 2  // Built-in LED (usually GPIO2 on most ESP32 boards)

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("Button test started. Press the button to see changes...");
}

void loop() {
  static bool lastState = HIGH;
  bool currentState = digitalRead(BUTTON_PIN);

  if (currentState != lastState) {
    if (currentState == LOW) {
      Serial.println("Button PRESSED");
      digitalWrite(LED_PIN, HIGH);
    } else {
      Serial.println("Button RELEASED");
      digitalWrite(LED_PIN, LOW);
    }
    lastState = currentState;
  }

  delay(10);  // Light debounce
}
