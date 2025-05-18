#pragma once
#include <Arduino.h>
#include <Adafruit_PN532.h>

enum TagType {
  TAG_UNKNOWN,
  TAG_MIFARE_CLASSIC,
  TAG_ULTRALIGHT,
  TAG_ISO_DEP
};

class NFCReader {
public:
  NFCReader(uint8_t cs_pin);
  void begin();
  String readNDEFMessage();
  void debugDump(uint8_t* data, uint32_t length);

private:
  Adafruit_PN532 pn532;
  String processNDEFData(uint8_t* data, uint32_t length);
  String getUriPrefix(uint8_t code);
  bool readMifareClassicNDEF(String& result, uint8_t* uid, uint8_t uidLength);
  bool readUltralightNDEF(String& result, uint8_t* uid, uint8_t uidLength);
  TagType identifyTagType(uint8_t* uid, uint8_t uidLength);
};
