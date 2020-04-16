#include <RHSPIDriver.h>

//--- Tx to Rx -------------------------------------------------------------------------------

#include <SPI.h>
#include <RH_RF95.h>

/* for feather m0  */
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3

#define MAXFRAME 250

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

//---------------------------------------------------------------------------------

void setup() {

  //--- Tx to Rx -------------------------------------------------------------------------------

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }

  delay(100);

//  Serial.println("Feather LoRa TX Test!");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    while (1);
  }
//  Serial.println("LoRa radio init OK!");

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
//  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
  rf95.setSignalBandwidth(125000);
  rf95.setCodingRate4(5);
  rf95.setSpreadingFactor(12);

  //---------------------------------------------------------------------------------
}


int16_t packetnum = 0;  // packet counter, we increment per xmission
char radiopacket[1500];

void receiveFromSerial(int len, int index = 0) {
  while (Serial.available() > 0) {
    if (index < len){
      char incomingByte = (char)Serial.read();
      Serial.print(incomingByte);
      radiopacket[index] = incomingByte;
      index++;
    }
    else{
      break;
    }
  }
}

void waitForReply(){
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len_re = sizeof(buf);
  Serial.println("Waiting for reply...");
  if (rf95.waitAvailableTimeout(1000)){
  // Should be a reply message for us now
    if (rf95.recv(buf, &len_re))
    {
      Serial.print("Got reply: ");
      Serial.println((char*)buf);
    }
  }
}

void loop() {
  if (Serial.available() > 0) {
    digitalWrite(13, HIGH);
    int len = Serial.parseInt();
    receiveFromSerial(len);
    Serial.println("received data from serial: ");
    for (int j = 0; j < len; j++)
      Serial.print(radiopacket[j], HEX);
    Serial.println();
    Serial.print("Total Data: ");
    Serial.println(len);
    int i=0;
    for (i; i < (len + 1) / MAXFRAME; i++) {
      rf95.send((uint8_t *)radiopacket + (i * MAXFRAME), MAXFRAME);
      rf95.waitPacketSent();
      // waitForReply();
      digitalWrite(13, LOW);
    }
    if (len%MAXFRAME > 0){
      rf95.send((uint8_t *)radiopacket + (i * MAXFRAME), len%MAXFRAME);
      rf95.waitPacketSent();
      // waitForReply();
    }
    digitalWrite(13, LOW);
    Serial.println("Done");
    
  }
  else {
    digitalWrite(13, LOW); // turn the LED off by making the voltage LOW
  }
  Serial.flush();
}
