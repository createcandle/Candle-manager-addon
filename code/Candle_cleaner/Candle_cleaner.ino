/*

 * Candle Manager Example

 * 

 * This is an example for Candle Manager.

 * 

 * This script clears the memory (eeprom) of the Arduino that you upload this code to. It then simply blinks its LED.

 * 

 * Wiping the memory can in rare occasions be necessary if a device has previously been used with encryption. This wipes the old encryption settings. They can sometimes interfere when you create a new device, like a ghost from the past.

 * 

 * SETTINGS */ 

int blinkSeconds = 2;  // Blink duration. How many seconds should a LED blink take?

 /* END OF SETTINGS

 * 

 * 

 */



#include <EEPROM.h>



// There is an option to auto-install missing libraries.

// #include <Your library name here.h> // The library name in between < and > (of in between "") will be used.



// #include <Your library name here.h> // "name to search for". In this case the "name to searh for" will be used to search for (and install) the required library. This is useful because library names are often different from their .h file names, and must be given exactly.





// the setup function runs once when you press reset or power the board

void setup()

{

  Serial.begin(115200); // for serial debugging over USB.

  Serial.println("Hello");

  pinMode(LED_BUILTIN, OUTPUT);

  Serial.println("Starting memory wipe.");

  for (int i = 0 ; i < EEPROM.length() ; i++) {

    EEPROM.write(i, 0);

  }

  Serial.println("My memory (eeprom) has been wiped.");



  if(blinkSeconds <= 0){    // This should not be set to 0 (or less).

    blinkSeconds = 1;

  }

}





// the loop function runs over and over again forever

void loop() {

  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)

  delay( (blinkSeconds / 2)*1000 );                       // wait before we continue

  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW

  delay( (blinkSeconds / 2)*1000 );                       // wait before we continue

  Serial.println("I just blinked my LED");

}

