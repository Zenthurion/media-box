#include <SPI.h>
#include "nfc_reader.h"

#define ENABLE_DEBUG_DUMP false

NFCReader::NFCReader(uint8_t cs_pin)
  : pn532(cs_pin) {}

void NFCReader::begin() {
  pn532.begin();
  uint32_t versiondata = pn532.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("Didn't find PN532 board");
    while (1)
      ;
  }
  Serial.print("Found PN532: ");
  Serial.println((versiondata >> 24) & 0xFF, HEX);
  pn532.SAMConfig();
  Serial.println("Waiting for an NFC card...");
}
String NFCReader::readNDEFMessage() {
  uint8_t uid[7];
  uint8_t uidLength;
  String result;
  
  // First detect tag only once
  if (!pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
    return ""; // No tag found, return immediately
  }
  
  // Debug: Print UID to help troubleshoot
  Serial.print("Card detected with UID: ");
  for (uint8_t i = 0; i < uidLength; i++) {
    Serial.print(uid[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
  
  // Determine card type solely by UID length
  bool isLikelyUltralight = (uidLength == 4);
  bool isLikelyClassic = (uidLength == 7);
  
  // Try Ultralight first for 4-byte UIDs
  if (isLikelyUltralight) {
    Serial.println("Trying Ultralight read first for 4-byte UID");
    if (readUltralightNDEF(result, uid, uidLength)) {
      Serial.println("Ultralight read successful");
      return result;
    }
    
    // Reset the reader state before trying a different protocol
    delay(50);
    pn532.SAMConfig();
    delay(50);
    
    // Re-detect the card
    if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
      if (readMifareClassicNDEF(result, uid, uidLength)) {
        Serial.println("MIFARE Classic read successful as fallback");
        return result;
      }
    }
  }
  
  // Try MIFARE Classic first for 7-byte UIDs
  if (isLikelyClassic) {
    Serial.println("Trying MIFARE Classic read first for 7-byte UID");
    if (readMifareClassicNDEF(result, uid, uidLength)) {
      Serial.println("MIFARE Classic read successful");
      return result;
    }
    
    // Reset the reader state before trying a different protocol
    delay(50);
    pn532.SAMConfig();
    delay(50);
    
    // Re-detect the card
    if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
      if (readUltralightNDEF(result, uid, uidLength)) {
        Serial.println("Ultralight read successful as fallback");
        return result;
      }
    }
  }
  
  // Unknown card type or read failed
  Serial.println("All read attempts failed");
  return "";
}

TagType NFCReader::identifyTagType(uint8_t* uid, uint8_t uidLength) {
  // Simple identification based on UID length - this is the most reliable indicator
  // and we're avoiding any operations that might interfere with later reading
  
  // 7-byte UIDs are always MIFARE Classic
  if (uidLength == 7) {
    Serial.println("7-byte UID detected - MIFARE Classic");
    return TAG_MIFARE_CLASSIC;
  } 
  
  // 4-byte UIDs are typically Ultralight in your case
  if (uidLength == 4) {
    Serial.println("4-byte UID detected - Ultralight");
    return TAG_ULTRALIGHT;
  }
  
  // Unknown card type
  Serial.println("Unknown card type - UID length not 4 or 7 bytes");
  return TAG_UNKNOWN;
}

bool NFCReader::readMifareClassicNDEF(String& result, uint8_t* uid, uint8_t uidLength) {
  uint8_t key[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
  uint8_t buffer[16];
  uint8_t allData[128];  // Increased from 96 to 128 bytes
  int dataIndex = 0;
  bool terminatorFound = false;
  unsigned long startTime = millis();
  
  // Set a timeout of 250ms for the entire read operation
  const unsigned long READ_TIMEOUT = 250;

  for (int sector = 1; sector <= 3 && !terminatorFound; sector++) {
    // Authenticate once per sector instead of per block
    if (!pn532.mifareclassic_AuthenticateBlock(uid, uidLength, sector * 4, 1, key)) {
      continue; // Skip this sector and try the next one
    }
    
    for (int blockInSector = 0; blockInSector < 3; blockInSector++) {
      // Check timeout
      if (millis() - startTime > READ_TIMEOUT) {
        return false;
      }
      
      int block = sector * 4 + blockInSector;
      if (!pn532.mifareclassic_ReadDataBlock(block, buffer)) continue;
      
      // Check if we have enough space in allData
      if (dataIndex + 16 > sizeof(allData)) {
        break; // Prevent buffer overflow
      }
      
      memcpy(&allData[dataIndex], buffer, 16);
      dataIndex += 16;

      if (memchr(buffer, 0xFE, 16)) {
        terminatorFound = true;
        break;
      }
    }
  }

  result = processNDEFData(allData, dataIndex);
  return !result.isEmpty();
}

bool NFCReader::readUltralightNDEF(String& result, uint8_t* uid, uint8_t uidLength) {
  uint8_t data[128];  // Increased from 64 to 128 bytes
  int index = 0;
  bool terminatorFound = false;
  unsigned long startTime = millis();
  
  // Set a timeout of 250ms for the entire read operation
  const unsigned long READ_TIMEOUT = 250;

  for (uint8_t page = 4; page < 20 && !terminatorFound; page++) {
    // Check timeout
    if (millis() - startTime > READ_TIMEOUT) {
      return false;
    }
    
    // Make sure we have enough space for the next page
    if (index + 4 > sizeof(data)) {
      break; // Prevent buffer overflow
    }
    
    if (!pn532.ntag2xx_ReadPage(page, &data[index])) {
      // If a page read fails, continue with what we have so far
      break;
    }
    
    if (memchr(&data[index], 0xFE, 4)) {
      terminatorFound = true;
    }
    index += 4;
  }

  // Process data even if we didn't read everything
  if (index > 0) {
    result = processNDEFData(data, index);
    return !result.isEmpty();
  }
  
  return false;
}

void NFCReader::debugDump(uint8_t* data, uint32_t length) {
  if (!ENABLE_DEBUG_DUMP) return;

  Serial.println(F("---- RAW NDEF DUMP ----"));
  for (uint32_t i = 0; i < length; i += 16) {
    char ascii[17] = { 0 };
    char line[80] = { 0 };
    snprintf(line, sizeof(line), "%04X: ", i);
    for (uint8_t j = 0; j < 16; j++) {
      if (i + j < length) {
        uint8_t b = data[i + j];
        snprintf(line + strlen(line), sizeof(line) - strlen(line), "%02X ", b);
        ascii[j] = (b >= 32 && b <= 126) ? b : '.';
      } else {
        strcat(line, "   ");
        ascii[j] = ' ';
      }
    }
    snprintf(line + strlen(line), sizeof(line) - strlen(line), " | %s", ascii);
    Serial.println(line);
  }
  Serial.println(F("------------------------"));
}

String NFCReader::processNDEFData(uint8_t* data, uint32_t length) {
  int tlvStart = -1;
  for (int i = 0; i < length - 1; i++) {
    if (data[i] == 0x03) {
      tlvStart = i;
      break;
    }
  }
  if (tlvStart == -1 || tlvStart + 1 >= length) return "";

  int offset = tlvStart + 1;
  uint32_t ndefLength;
  
  if (data[offset] == 0xFF) {
    // Long record format
    if (offset + 2 >= length) return ""; // Not enough data
    ndefLength = ((uint16_t)data[offset + 1] << 8 | data[offset + 2]);
    offset += 3;
  } else {
    // Short record format
    ndefLength = data[offset++];
  }

  if (offset + ndefLength > length) return "";

  // Safety check to avoid out-of-bounds access
  if (offset >= length) return "";
  
  uint8_t tnf = data[offset++];
  bool isShortRecord = tnf & 0x10;

  // Check if we have enough data for typeLength
  if (offset >= length) return "";
  uint8_t typeLength = data[offset++];
  
  uint32_t payloadLength;
  if (isShortRecord) {
    // Short record
    if (offset >= length) return "";
    payloadLength = data[offset++];
  } else {
    // Long record
    if (offset + 3 >= length) return ""; // Not enough data for 4-byte length
    payloadLength = ((uint32_t)data[offset] << 24) | 
                    ((uint32_t)data[offset + 1] << 16) | 
                    ((uint32_t)data[offset + 2] << 8) | 
                    (uint32_t)data[offset + 3];
    offset += 4;
  }

  uint8_t idLength = 0;
  if (tnf & 0x08) {
    if (offset >= length) return "";
    idLength = data[offset++];
  }

  // Check if there's enough data for the type field
  if (offset + typeLength > length) return "";
  uint8_t* typeField = &data[offset];
  offset += typeLength + idLength;

  if (typeLength != 1 || typeField[0] != 'U') return "";

  String result = "";
  if (offset >= length) return result;

  uint8_t uriPrefix = data[offset++];
  result += getUriPrefix(uriPrefix);

  // Make sure payloadLength is reasonable
  if (payloadLength > 1000 || offset + payloadLength - 1 > length) {
    payloadLength = length - offset; // Limit to available data
  }

  for (uint32_t i = 0; i < payloadLength - 1 && (offset + i) < length; i++) {
    char c = data[offset + i];
    if (isPrintable(c)) {
      result += c;
    }
  }

  return result;
}

String NFCReader::getUriPrefix(uint8_t code) {
  switch (code) {
    case 0x00: return "";
    case 0x01: return "http://www.";
    case 0x02: return "https://www.";
    case 0x03: return "http://";
    case 0x04: return "https://";
    default: return "";
  }
}
