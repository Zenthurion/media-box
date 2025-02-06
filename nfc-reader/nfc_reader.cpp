#include "nfc_reader.h"
#include <SPI.h>

NFCReader::NFCReader(uint8_t ss_pin, uint8_t rst_pin) : mfrc522(ss_pin, rst_pin) {
    // Initialize key
    for (byte i = 0; i < 6; i++) {
        key.keyByte[i] = 0xFF;
    }
}

void NFCReader::begin() {
    SPI.begin();
    mfrc522.PCD_Init();
}

String NFCReader::readNDEFMessage() {
    if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
        return "";
    }

    Serial.println("NFC Tag detected!");

    byte allData[96];
    int dataIndex = 0;
    byte bufferSize = sizeof(buffer); // Create a non-const byte for size

    // Read blocks 4 to 9
    for (int block = 4; block <= 9; block++) {
        MFRC522::StatusCode status = mfrc522.PCD_Authenticate(
            MFRC522::PICC_CMD_MF_AUTH_KEY_B, block, &key, &(mfrc522.uid));

        if (status != MFRC522::STATUS_OK) {
            Serial.print("Authentication failed for block ");
            Serial.println(block);
            continue;
        }

        status = mfrc522.MIFARE_Read(block, buffer, &bufferSize); // Pass non-const size
        if (status != MFRC522::STATUS_OK) {
            Serial.print("Read failed for block ");
            Serial.println(block);
            continue;
        }

        for (int i = 0; i < 16; i++) {
            allData[dataIndex++] = buffer[i];
        }
    }

    String result = processNDEFData(allData, dataIndex);

    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();

    return result;
}

String NFCReader::processNDEFData(byte* allData, int dataIndex) {
    String ndefMessage = "";
    
    if (allData[0] == 0x03) { // NDEF TLV tag
        int startPos = 6;
        for (int i = startPos; i < dataIndex; i++) {
            byte currentByte = allData[i];

            if (currentByte == 0xFE) break;
            if (i >= 48 && i < 64) continue; // Skip block 7

            if (currentByte >= 32 && currentByte <= 126) {
                ndefMessage += (char)currentByte;
            }
        }
    }
    
    return ndefMessage;
} 