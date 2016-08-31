#include <SPI.h>
#include <RF24.h>

#define SPEAKER 8
#define CE 9
#define CSN 10
#define MOSI 11
#define MISO 12
#define SCK 13
#define RADIO_CHANNEL 0x76
#define RADIO_PIPE 0xF0F0F0F0E1LL

int length;
String messageForRadio;
RF24 radio(CE, CSN);

void setup() {
  //Initialize serial and wait for port to open:
	Serial.begin(9600);
	pinMode(SPEAKER,OUTPUT);
	initRadio();
	while (!Serial) {
    // wait for serial port to connect. Needed for native USB
		beep();
	}

	digitalWrite(SPEAKER,HIGH);
	delay(50);
	digitalWrite(SPEAKER,LOW); 
}

void loop() {
   //proceed normally
	if (Serial.available() > 0) {
		String receivedMessage = Serial.readString();

		Serial.print("The received string is: ");
		Serial.println(receivedMessage);

		if (receivedMessage.equals("xxxx")) {
			digitalWrite(SPEAKER,HIGH);
			delay(50);
			digitalWrite(SPEAKER,LOW);
			delay(50);
			digitalWrite(SPEAKER,HIGH);
			delay(50);
			digitalWrite(SPEAKER,LOW);
			delay(50);
			digitalWrite(SPEAKER,HIGH);
			delay(50);
			digitalWrite(SPEAKER,LOW);
			Serial.println("OK");
		}
		     
		else {
			//check the first character which represent the length of bytes to receive
			if((int) receivedMessage[0] >= 48 && (int) receivedMessage[0] <= 57) {
				length = (int) receivedMessage[0] - 48;

				// check if length of string is complete
				if (checkString(receivedMessage,length + 1)) {
					// send this to radio for transmission
					// Do radio transmission in here! 
					messageForRadio = receivedMessage.substring(1);
					Serial.println(messageForRadio);

					char* buffer = (char*) malloc(sizeof(char) * messageForRadio.length());
					messageForRadio.toCharArray(buffer, messageForRadio.length());
					radio.write(&buffer, sizeof(buffer));
					delay(1000);
					free(buffer);
				}

			}
		       
		}  
	}
}

bool flushReceived() {
	while(Serial.available()) {
		Serial.read();
	}

	return true;
}


bool checkString(String msg, int length) {
	if (msg.length() == length) {
		return true;
	}

	else
    	return false;
}

void initRadio() {
	radio.begin();
	radio.setPALevel(RF24_PA_MAX);
	radio.setChannel(RADIO_CHANNEL);
	radio.openWritingPipe(RADIO_PIPE);

	radio.enableDynamicPayloads();
	radio.powerUp();
}

void beep() {
	digitalWrite(SPEAKER,HIGH);
	delay(20);
	digitalWrite(SPEAKER,LOW);
	delay(20);
}