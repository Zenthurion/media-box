#ifndef NFC_READER_H
#define NFC_READER_H

#include <MFRC522.h>

class NFCReader {
private:
    MFRC522 mfrc522;
    MFRC522::MIFARE_Key key;
    
    byte buffer[18];

public:
    NFCReader(uint8_t ss_pin, uint8_t rst_pin);
    void begin();
    String readNDEFMessage();
    
private:
    String processNDEFData(byte* allData, int dataIndex);
};

#endif 