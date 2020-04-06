/*
    This sketch reads data from the Serial input stream of the format "<COMMAND|Value1,Value2,Value3,...,ValueN>"
    and parses it into the COMMAND and an array of N values.
    Whitespace is ignored.
*/
#include <Stepper.h>

//COMMAND PACKET DEFINITIONS
#define START_MARKER '<'
#define END_MARKER '>'
#define COMMAND_SEP '|'
#define VALUE_SEP ','

//COMMANDS
const long cmd_timeout = 1000; // miliseconds
long cmd_issued = 0; // time command was recieved

//PINS
//the motor will be controlled by the motor A pins on the motor driver
#define stepPinE 7
#define dirPinE 8
#define stepPinR 5
#define dirPinR 6
#define firePin 3

//STEPPER
const int NSTEPS = 200;
Stepper stepperE = Stepper(NSTEPS, dirPinE, stepPinE);
Stepper stepperR = Stepper(NSTEPS, dirPinR, stepPinR);

//GUN
float fireDelay = 175;

/********************************************************************************/

// SET UP THE COMMAND PARSING
const size_t cmdBuffLen = 3; // length of the expected command string
char cmdBuffer[cmdBuffLen + 1];
uint8_t bufferIndex = 0;
bool receiving = false;       // set to true when start marker is received, set to false when end marker is received
bool commandReceived = false; // set to true when command separator is received (or if command buffer is full)

/********************************************************************************/

void setup()
{
  Serial.begin(9600);

  //set the motor control pins as outputs
  pinMode(stepPinE, OUTPUT);
  pinMode(stepPinR, OUTPUT);
  pinMode(dirPinE, OUTPUT);
  pinMode(dirPinR, OUTPUT);
  pinMode(firePin, OUTPUT);

  // set stepper RPM
  stepperE.setSpeed(60); // 20 rpm
  stepperR.setSpeed(120); // 20 rpm
}

/********************************************************************************/

void loop() {
  // Get and parse the serial command
  if (Serial.available() > 0) { // If there's at least one byte to read
    char serialByte = Serial.read(); // Read it

    if (serialByte == START_MARKER) { // Start marker received: reset indices and flags
      receiving = true;
      commandReceived = false;
      bufferIndex = 0;
      return;
    }
    if (receiving) { // If the start marker has been received
      if (!commandReceived) { // If the command hasn't been received yet
        if (serialByte == END_MARKER) { // If the command end marker is received
          cmdBuffer[bufferIndex] = '\0'; // Terminate the string in the buffer
          commandReceived = true;
          cmd_issued = millis();
          receiving = false; // Stop receivinng
        } else if (bufferIndex < cmdBuffLen) {                                         // If the received byte is not the command separator or the end marker and the command buffer is not full
          cmdBuffer[bufferIndex++] = serialByte; // Write the new data into the buffer
        } else { // If the command buffer is full
        }
      }
    }// end if (receiving)
  }// end if (Serial.available() > 0)

  if (commandReceived) {// Send commands to the motors

    // check the timeout
    if ((millis() - cmd_issued) > cmd_timeout) {
      stopMove();
      return;
    }
    if (strcmp(cmdBuffer, "FIR") == 0) {
      fire();
      commandReceived = false;
      return;
    }

    if (strcmp(cmdBuffer, "STP") == 0) {
      stopMove();
    } else if (strcmp(cmdBuffer, "UPP") == 0) {
      goUp();
    } else if (strcmp(cmdBuffer, "DWN") == 0) {
      goDown();
    } else if (strcmp(cmdBuffer, "LFT") == 0) {
      goLeft();
    } else if (strcmp(cmdBuffer, "RGT") == 0) {
      goRight();
    }
    commandReceived = false;
    return;
  }// end if (commandReceived)
} // end of loop

/********************************************************************************/
void stopMove() {
  stepperR.step(0);
  stepperE.step(0);
}


void goLeft() {
  stepperR.step(10);
}

void goRight() {
  stepperR.step(-10);
}

void goUp() {
  stepperE.step(10);
}

void goDown() {
  stepperE.step(-10);
}

void fire() {
  digitalWrite(firePin, HIGH);
  delay(fireDelay);
  digitalWrite(firePin, LOW);
}
