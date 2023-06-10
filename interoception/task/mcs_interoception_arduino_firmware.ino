/*
  Interoception task
  Sasha Sommerfeldt & John Koger
  2019

  Firmware code to be loaded onto an Arduino (developed using an Eelegoo Uno R3) to implement a method of constant stimuli (MCS) cardiac interoception task modeled off of

  Brener, J., Ring, C., & Liu, X. (1994). Effects of data limitations on heartbeat detection in the method of constant stimuli. Psychophysiology, 31(3), 309-312.

  Participants are asked to judge the simultaneity of their heartbeats and/or exteroceptive comparison stimuli (visual LED light flash, audio tone). Each trial consists of 5 beats, such that participants may orient to internal and external stimuli and assess the simultaneity of interoceptive and exteroceptive stimuli. Audio tones are presented at differing intervals after the R‐wave: 0 ms, 100 ms, 200 ms, 300 ms, 400 ms, or 500 ms (which are specified in Python). Participants are classfied as accurate interoceptors if they consistently report that the same delay is simultaneous with their heart beats, allowing for individual differences in the delay at which they perceive their heart.


  This code is to be run in conjunction with code in Python (PsychoPy), which supplies information on the delay condition for each trial, as well as displaying the experimenter/participant interface, which will, for example, ask participants whether lights and tones were simultaneous with their heart beats and read participant responses.

  See wiring diagram for hardware implementation. Arduino is connected through an OUT ISO to a Biopac ECG amplifier switched to R-Wave mode.


*/

// Length of current message buffer
int bufferMessageLength = 0 ;

// Set the serial input buffer -- the maximum number of characters that can be read from one serial message (from Python)
#define BUFFERSIZE 256
char serialBuffer[BUFFERSIZE] ;


// read the input on analog pin 0:
// long ecgSignal = analogRead(A0); // for ECG-less testing
long ecgSignal = 100 ;

// Number of samples to use to calculate the average signal
long ecgAVGlength = -9999 ;
float ecgAVG = 0 ;
float ecgSUM = 0 ;

// Delay for the trial
long msDelay = -9999 ;
// How long you want the light to stay on/flash for
long msStimulus = -9999 ;
// What to multiply the ecgAVG by to set the RWaveThreshold
float thresholdMultiplier = -9999 ;
// Number of heart beats per trial (typically 5)
int beatsPerTrial = -9999;
// Just initialize a variable for the R-wave microvolt threshold where you determine it's a beat = 1.5x their average signal (need to pilot this on hearts other than my own!)
float RWaveThreshold = -9999 ;
// Whether it is a practice trial
char practiceYN = 'Y' ;

#define ACTIVE_BUZZER 4 // buzzes after msDelay from heart beat
#define GREEN_LED 7 // Light for practice trials to go in sync or not the tones
#define WHITE_LED 8 // With blue indicates in calibration phase
#define BLUE_LED 12 // With white indicates calibration phase. When flashes once, indicates finished trial of 5 beats
#define RED_LED 13 //signals Arudino is in main loop / is on

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 57600 bits per second:
  Serial.begin(9600);
  // Set A0 as input (potentiometer)
  pinMode(A0, INPUT);
  // Set 13 as output (Red LED)
  pinMode(RED_LED, OUTPUT);
  // Set 12 as output (Blue LED)
  pinMode(BLUE_LED, OUTPUT);
  // Set 8 as output (White LED)
  pinMode(WHITE_LED, OUTPUT);
  // Set 7 as output (Green LED)
  pinMode(GREEN_LED, OUTPUT);
  // Set 4 as output (Tone)
  pinMode(ACTIVE_BUZZER, OUTPUT);


  // Ensure these are set to what we want after reset
  bufferMessageLength = 0 ;
  ecgSignal = 100 ;
  ecgAVGlength = -9999 ;
  ecgAVG = 0 ;
  ecgSUM = 0 ;
  msDelay = -9999 ;
  msStimulus = -9999 ;
  thresholdMultiplier = -9999 ;
  beatsPerTrial = -9999;
  RWaveThreshold = -9999 ;
  practiceYN = 'Y' ;

  Serial.print("#ArduinoReady") ;
  Serial.println(" ##") ;
}
// Reset function
void(* resetFunc) (void) = 0; //declare reset function @ address 0


///////////////////////////////
/////// Wait for Python ///////
///////////////////////////////

// Read a line off of Serial
void getMessage() {
    // Reset the buffer message length so that it's the current message length
    bufferMessageLength = 0 ;
    serialBuffer[0] = '\0' ;
    if (Serial.available() > 0) {
      char c = Serial.read();  // gets one byte from serial buffer
      // Keep looping until hit a new line character
      while (c != '\n') {
        serialBuffer[bufferMessageLength] = c ;
        bufferMessageLength += 1 ;
        // readString += c; // concatenate c onto readString
        delay(10); // delay for 10 ms, serial communication is going on in background as this routine is going, so need to give that background routine time to read again
        c = Serial.read();  // gets one byte from serial buffer
      } // End of line of message
      serialBuffer[bufferMessageLength] = '\0' ; // The very last character in the buffer is the end of the string (byte 0)
    } // End if of serial available

}

// Runs fast, takes up almost no space, compared to .toInt() :(
// s[i] is the current character we're looking at
int makeIntoInt(char *s) {
   int r = 0 ;
   // Serial.println("One int, coming up!") ;
   // Look for any characters that are actually printable digits (>= 0 ASCII character).
   for (int i = 0; s[i] >= '0'; i++ ) {
    r = r*10 ; // moving over a digit
    r = r+(s[i]-'0') ; // subtract ASCII 0 from s[i]
    // Serial.print("r = ") ;
    // Serial.println(r);
   }
   return r ;
}

float makeIntoFloat(char *s) {
   float r = 0 ;
   int decimalFlag = 0 ;
   float tenthsMultiplier = 0.1 ;
   // Serial.println("One float, coming up!") ;
   // Look for any characters that are actually printable digits (>= 0 ASCII character).
   for (int i = 0; (s[i] >= '0') || (s[i] == '.') ; i++ ) {
    // If see a decimal, divide the current thing by
    if (s[i] == '.') {
      decimalFlag = 1 ;
    }
    else {
      if (decimalFlag == 1) {
        r = r + ( (s[i]-'0') * tenthsMultiplier ) ; // subtract ASCII 0 from s[i]
        tenthsMultiplier*=.1 ;
      }
      else {
        r = r*10 ; // moving over a digit
        r = r+(s[i]-'0') ; // subtract ASCII 0 from s[i]
      }
      // Serial.print("r = ") ;
      // Serial.println(r) ;
    }
   }
   return r ;
}

///////////////////////////////
///////// Calibration /////////
///////////////////////////////

// Take ecgAVGlength number of samples of the ECG signal to calculate an average signal (ecgAVG)
// This will be used with a multiplier to set the threshold for the R-Wave/ detection of a heart beat
void calibrate() {
  // turn the blue LED on
  digitalWrite(BLUE_LED, HIGH);
  // turn the white LED on
  digitalWrite(WHITE_LED, HIGH);
  ecgAVG = analogRead(A0);
  // ecgAVG = 100 ;
  for (int nPreSamples = 1; nPreSamples <= ecgAVGlength; nPreSamples++) {
    ecgSignal = analogRead(A0);
    //ecgSignal = 100 + nPreSamples ; //for ECG-less testing
    //Serial.print("ecgSignal=");
    //Serial.println(ecgSignal);
    ecgSUM += ecgSignal ;
    //Serial.print("ecgSUM=");
    //Serial.println(ecgSUM);
    delay(50);
  }
  ecgAVG = ecgSUM / ecgAVGlength ;
 // for (int counter = 1; counter < 10; counter++) {
  //  Serial.println("@@") ;
  //  delay(10);
  //}
  Serial.print("ecgAVG=");
  Serial.println(ecgAVG);
  Serial.print("#CDone") ;
  Serial.println(" ##") ;

  // turn the blue LED off
  digitalWrite(BLUE_LED, LOW);
  // turn the white LED off
  digitalWrite(WHITE_LED, LOW);
} ;
///////////////////////////////




///////////////////////////////
/////////// Trials ///////////
///////////////////////////////

// Trial function to run 1 trial of 5 (or whatever beatsPerTrial is set to) beats
void runTrial() {

  Serial.print("msDelay=");
  Serial.println(msDelay);
  Serial.print("beatsPerTrial=");
  Serial.println(beatsPerTrial);
  Serial.print("msStimulus=");
  Serial.println(msStimulus);
  Serial.print("ecgAVG=");
  Serial.println(ecgAVG);
  Serial.print("thresholdMultiplier=");
  Serial.println(thresholdMultiplier);

  // For number of heart beats specified by beatsPerTrial +1, we'll skip the first one each time so not super fast
  for (int ntrials = 1; ntrials <= beatsPerTrial+1; ntrials++) {
     ecgSignal = analogRead(A0);
     //Serial.print("ecgSignal=");
     //Serial.println(ecgSignal);
     RWaveThreshold = ecgAVG * thresholdMultiplier ;
     //Serial.print("RWaveThreshold=");
     //Serial.println(RWaveThreshold);


    // Wait for a heart beat coming off the ECG. While the voltage is below the threshold, do nothing
    while(ecgSignal < RWaveThreshold) {
       ecgSignal = analogRead(A0);
       //Serial.print("ecgSignal=");
       //Serial.println(ecgSignal);
       ecgAVG = (ecgAVG*ecgAVGlength + ecgSignal) / (ecgAVGlength + 1); // continually recalc the ecgAVG
       RWaveThreshold = ecgAVG * thresholdMultiplier ;
       //Serial.println("1st loop, waiting for R-wave to start");
       delay(5);
    };

    // Skip the first heart beat
    if (ntrials != 1) {
      Serial.println("passed threshold");
      if(practiceYN == 'Y') {
          // turn the green LED on
          digitalWrite(GREEN_LED, HIGH);
          // pause for the time stimulus should be on
          delay(msStimulus); // Wait for sensorvalue millisecond(s)
          // turn the green LED off
          digitalWrite(GREEN_LED, LOW);
      }

        // Once it goes above the threshold
        delay(msDelay);
        // make a sound
        digitalWrite(ACTIVE_BUZZER, HIGH);
        // pause for the time stimulus should be on
        delay(msStimulus); // Wait for sensorvalue millisecond(s)
        // turn the sound off
        digitalWrite(ACTIVE_BUZZER, LOW);
    }

     // Wait until it drops back down so not setting off multiple per heart beat because of the long R wave
     while(ecgSignal > RWaveThreshold) {
        ecgSignal = analogRead(A0);
        ecgAVG = (ecgAVG*ecgAVGlength + ecgSignal) / (ecgAVGlength + 1);
        RWaveThreshold = ecgAVG * thresholdMultiplier;
        delay(5);
     };

  }; // 5 trials done

  Serial.print("#TDone");
  Serial.println(" ##");
  // Reset delay from heart beat to impossible value
  msDelay = -9999 ;

}; // end of runTrial function


///////////////////////////////
////// Reset the buffer ////////
///////////////////////////////
void resetBuffer() {
    //serialBuffer[0] = '\0' ;
    //bufferMessageLength = 0 ;
}

///////////////////////////////
/////// Parse Message ////////
///////////////////////////////

int parseMessage() {
    delay(100) ; //to give python code time to do something
    getMessage() ;

    // Check if there is a command, and if it is a valid command (everything comming from python should start with >)
    if ( serialBuffer[0] == '\0' ) {
      return 0 ;
    }
    if ( (bufferMessageLength >0) && (serialBuffer[0] != '>') ) {
      Serial.print("Unrecognized command: ") ;
      Serial.print(serialBuffer) ;
      Serial.println(" ##") ;
      resetBuffer() ;
      return 0 ;
    }

    // How long the light/tone should stay on for
    if ( (serialBuffer[1] == 'S') && (serialBuffer[2] == 'T') ) {
      msStimulus = makeIntoInt( &(serialBuffer[4]) ) ;
      Serial.print("msStimulus = ") ;
      Serial.print(msStimulus) ;
      Serial.println(" ##") ;
      resetBuffer() ;
    }

    // Threshold Muliplier: What to multiply the ecgAVG by to set the RWaveThreshold
    if ( (serialBuffer[1] == 'T') && (serialBuffer[2] == 'M') ) {
      thresholdMultiplier = makeIntoFloat( &(serialBuffer[4]) ) ;
      Serial.print("thresholdMultiplier = ") ;
      Serial.print(thresholdMultiplier) ;
      Serial.println(" ##") ;
      resetBuffer() ;
    }

    // Beats per Trial
    if ( (serialBuffer[1] == 'B') && (serialBuffer[2] == 'P') ) {
      delay(100);
      beatsPerTrial = makeIntoInt( &(serialBuffer[4]) ) ;
      Serial.print("beatsPerTrial = ") ;
      Serial.print(beatsPerTrial) ;
      Serial.println(" ##") ;
      resetBuffer() ;
    }

    // Number of samples to use to compute ECG average for calibration
    if ( (serialBuffer[1] == 'A') && (serialBuffer[2] == 'L') ) {
      digitalWrite(GREEN_LED, HIGH);
      delay(500);
      digitalWrite(GREEN_LED, LOW);
      ecgAVGlength = makeIntoInt( &(serialBuffer[4]) ) ;
      Serial.print("ecgAVGlength = ") ;
      Serial.print(ecgAVGlength) ;
      Serial.println(" ##") ;
      //digitalWrite(RED_LED, HIGH);
      //delay(500);
      //digitalWrite(RED_LED, LOW);
      resetBuffer() ;
    }

    // Delay between tone and heart beat (or light)
    if ( (serialBuffer[1] == 'D') && (serialBuffer[2] == 'L') ) {
      msDelay = makeIntoInt( &(serialBuffer[4]) ) ;
      Serial.print("msDelay = ") ;
      Serial.print(msDelay) ;
      Serial.println(" ##") ;
      resetBuffer() ;
    }



    if ( (serialBuffer[1] == 'C') && (serialBuffer[2] == 'M') ) {
      // Serial.println("Received a command") ;
      char nextCommand = serialBuffer[4] ;

      Serial.print("Received command = ") ;
      Serial.println(nextCommand) ;

      switch(nextCommand) {

        case 'R': {
          Serial.println("Arduino Reset") ;
          Serial.println("Resetting..");
          resetFunc();  //call reset
          Serial.print("Reset failed");
          Serial.println(" ##") ;
          resetBuffer() ;
          break;
        }

        case 'I' : {
          Serial.println("Arduino Initialize") ;
          // These are all set to an impossible value at the top, then initialize needs to make sure theyre all set from python.
          // Python needs to send all of these values first, then say Initialize, and this case statement just checks to make sure all of those are set.
          if ( msStimulus == -9999 || thresholdMultiplier == -9999 || beatsPerTrial == -9999) {
            Serial.print("ERROR: ST, TM, or BP not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          else {
            Serial.print("msStimulus = ");
            Serial.println(msStimulus) ;
            Serial.print("thresholdMultiplier = ");
            Serial.println(thresholdMultiplier) ;
            Serial.print("beatsPerTrial = ");
            Serial.print(beatsPerTrial) ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          break;
        }

        case 'C': {
          Serial.println("Arduino Calibrate") ;
          if ( ecgAVGlength == -9999 ) {
            Serial.print("ERROR: AL not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          else {
            Serial.print("ecgAVGlength = ");
            Serial.println(ecgAVGlength) ;
            Serial.print("Beginning calibration..") ;
            Serial.println(" ##") ;
            // resetBuffer() ;
            calibrate() ;
            Serial.println("Calibration call is done.") ;
          }
          break;
        }

        case 'P': {
          practiceYN = 'Y' ;
          Serial.println("Arduino Run Practice Trial") ;
          if ( msDelay == -9999) {
            Serial.print("ERROR: msDelay not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          if ( ecgAVG == 0 ) {
            Serial.print("ERROR: ecgAVG not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          else {
            Serial.print("ecgAVG = ");
            Serial.println(ecgAVG) ;
            Serial.print("msDelay = ");
            Serial.print(msDelay) ;
            Serial.println(" ##") ;
            resetBuffer() ;
            runTrial() ;
         }
         break ;
        }

        case 'T': {
          practiceYN = 'N' ;
          Serial.println("Arduino Run Trial") ;
          if ( msDelay == -9999) {
            Serial.print("ERROR: msDelay not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          if ( ecgAVG == 0 ) {
            Serial.print("ERROR: ecgAVG not set.") ;
            Serial.println(" ##") ;
            resetBuffer() ;
          }
          else {
            Serial.print("ecgAVG = ");
            Serial.println(ecgAVG) ;
            Serial.print("msDelay = ");
            Serial.print(msDelay) ;
            Serial.println(" ##") ;
            resetBuffer() ;
            runTrial() ;
         }
         break ;
        }

        default: {
          Serial.print("Error: Acceptable commands are R, I, C, P, or T") ;
          Serial.println(" ##") ;
          resetBuffer() ;
          break;
        }
      }
  }
}

///////////////////////////////






// the loop routine runs over and over again forever:
void loop() {
  // Loop forever getting message from serial (python)
  while(1) {
    parseMessage() ;
  }
};
