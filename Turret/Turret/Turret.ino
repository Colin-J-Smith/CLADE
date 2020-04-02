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

//PINS
//the motor will be controlled by the motor A pins on the motor driver
#define stepPinE 3
#define stepPinR 8
#define dirPinE 4
#define dirPinR 9
#define firePin 2

//STEPPER
const int NSTEPS = 3200;
Stepper stepperE = Stepper(NSTEPS, stepPinE, dirPinE);
Stepper stepperR = Stepper(NSTEPS, stepPinR, dirPinR);


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
  stepperE.setSpeed(20); // 20 rpm
  stepperR.setSpeed(20); // 20 rpm
}

// SET UP THE COMMAND PARSING
const size_t buffLen = 3;     // length of the expected message chunks (number of characters between two commas) (16-bit int has 5 digits + sign)
char buffer[buffLen + 1];     // add one for terminating null character
const size_t cmdBuffLen = 3; // length of the expected command string
char cmdBuffer[cmdBuffLen + 1];

uint8_t bufferIndex = 0;

const size_t arrayOfIntsLen = 2; // number of ints to receive
int arrayOfInts[arrayOfIntsLen];
uint8_t arrayOfIntsIndex = 0;

bool receiving = false;       // set to true when start marker is received, set to false when end marker is received
bool commandReceived = false; // set to true when command separator is received (or if command buffer is full)


// BEGIN
void loop() {
  if (Serial.available() > 0) { // If there's at least one byte to read
    char serialByte = Serial.read(); // Read it

    if (serialByte == START_MARKER) { // Start marker received: reset indices and flags
      receiving = true;
      commandReceived = false;
      bufferIndex = 0;
      arrayOfIntsIndex = 0;
      return;
    }
    if (receiving) { // If the start marker has been received
      if (!commandReceived) { // If the command hasn't been received yet
        if (serialByte == COMMAND_SEP || serialByte == END_MARKER) { // If the command separator is received
          cmdBuffer[bufferIndex] = '\0'; // Terminate the string in the buffer

          if (serialByte == END_MARKER) { // If the end marker is received
            receiving = false; // Stop receivinng
          } else {
            bufferIndex = 0; // Reset the index of the buffer to overwrite it with the numbers we're about to receive
            commandReceived = true;
          }
        } else if (bufferIndex < cmdBuffLen) { // If the received byte is not the command separator or the end marker and the command buffer is not full
          cmdBuffer[bufferIndex++] = serialByte; // Write the new data into the buffer
        } else { // If the command buffer is full
          //Serial.println("Error: command buffer full, command is truncated");
        }
      }
      else if (serialByte == VALUE_SEP || serialByte == END_MARKER) { // If the value separator or the end marker is received
        if (bufferIndex == 0) { // If the buffer is still empty
          //Serial.println("\t(Empty input)");
        } else { // If there's data in the buffer and the value separator or end marker is received
          buffer[bufferIndex] = '\0'; // Terminate the string
          parseInt(buffer);           // Parse the input
          bufferIndex = 0;            // Reset the index of the buffer to overwrite it with the next number
        }
        if (serialByte == END_MARKER) { // If the end marker is received
          receiving = false; // Stop receivinng
        }
      } else if (bufferIndex < buffLen) { // If the received byte is not a special character and the buffer is not full yet
        buffer[bufferIndex++] = serialByte; // Write the new data into the buffer
      } else { // If the buffer is full
        //Serial.println("Error: buffer is full, data is truncated");
      }
    }// end if (receiving)
  }// end if (Serial.available() > 0)
  
  if (commandReceived) {// Send commands to the motors
    if (strcmp(cmdBuffer, "ROT")) {
      rotate(arrayOfInts);
    } else if (strcmp(cmdBuffer, "ELE")) {
      elevate(arrayOfInts);
    } else {
      //Serial.println("Error: command not recognized");
    }
  }
} // end of loop

void parseInt(char *input) {
  //Serial.print("\tInput:\t");
  //Serial.println(input);
  if (arrayOfIntsIndex >= arrayOfIntsLen) {
    //Serial.println("Error: array of ints is full");
    return;
  }
  int value = atoi(input);
  arrayOfInts[arrayOfIntsIndex++] = value;
}


/********************************************************************************/
void elevate(int deg) {
  stepperE.step(int(NSTEPS * deg / 360));
}

void rotate(int deg) {
  stepperR.step(int(NSTEPS * deg / 360));
}
