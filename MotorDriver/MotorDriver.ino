/*
    This sketch reads data from the Serial input stream of the format "<COMMAND|Value1,Value2,Value3,...,ValueN>"
    and parses it into the COMMAND and an array of N values.
    Whitespace is ignored.
*/

//COMMAND MARKER DEFINITIONS
#define START_MARKER '<'
#define END_MARKER '>'
#define COMMAND_SEP '|'
#define VALUE_SEP ','

//COMMANDS
const long cmd_timeout = 1000; // miliseconds
long cmd_issued = 0; // time command was recieved

//PIN VARIABLES
//the motor will be controlled by the motor A pins on the motor driver
#define AIN1 2 //control pin 1 on the motor driver for the left motor
#define AIN2 4 //control pin 2 on the motor driver for the left motor
#define PWMA 5 //speed control pin on the motor driver for the left motor

#define CIN1 6 //control pin 1 on the motor driver for the right motor
#define CIN2 7 //control pin 2 on the motor driver for the right motor
#define PWMC 3 //speed control pin on the motor driver for the right motor

#define BIN1 13 //control pin 1 on the motor driver for the front motor
#define BIN2 12 //control pin 2 on the motor driver for the front motor
#define PWMB 11 //speed control pin on the motor driver for the front motor

#define DIN1 8 //control pin 1 on the motor driver for the back motor
#define DIN2 9 //control pin 2 on the motor driver for the back motor
#define PWMD 10 //speed control pin on the motor driver for the back motor

// MOTOR SPEED
#define SPD 120 // duty cycle for the pwm signal 0-255

/********************************************************************************/

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
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(CIN1, OUTPUT);
  pinMode(CIN2, OUTPUT);
  pinMode(DIN1, OUTPUT);
  pinMode(DIN2, OUTPUT);

  pinMode(PWMA, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(PWMC, OUTPUT);
  pinMode(PWMD, OUTPUT);
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

  if (commandReceived) {// Execute the command
    // check the timeout
    if ((millis() - cmd_issued) > cmd_timeout) {
      stopMove();
      return;
    }

    // run the command
    if (strcmp(cmdBuffer, "STP") == 0) {
      stopMove();
    } else if (strcmp(cmdBuffer, "FWD") == 0) {
      goFwd();
    } else if (strcmp(cmdBuffer, "BCK") == 0) {
      goBack();
    } else if (strcmp(cmdBuffer, "LFT") == 0) {
      goLeft();
    } else if (strcmp(cmdBuffer, "RGT") == 0) {
      goRight();
    } else if (strcmp(cmdBuffer, "LLL") == 0) {
      rotLeft();
    } else if (strcmp(cmdBuffer, "RRR") == 0) {
      rotRight();
    }

  }// end if (commandReceived)
}// end of loop

/********************************************************************************/

void stopMove() {
  //left wheel
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  //right wheel
  digitalWrite(CIN1, LOW);
  digitalWrite(CIN2, LOW);
  //front wheel
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  //back wheel
  digitalWrite(DIN1, LOW);
  digitalWrite(DIN2, LOW);

  analogWrite(PWMA, 0);
  analogWrite(PWMB, 0);
  analogWrite(PWMC, 0);
  analogWrite(PWMD, 0);

  //  Serial.println("Stop");
}

void goFwd() {
  //left wheel
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  //right wheel
  digitalWrite(CIN1, HIGH);
  digitalWrite(CIN2, LOW);
  //front wheel
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  //back wheel
  digitalWrite(DIN1, LOW);
  digitalWrite(DIN2, LOW);

  analogWrite(PWMA, SPD);
  analogWrite(PWMC, SPD);

  //  Serial.println("Back");
}

void goBack() {
  //left wheel
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  //right wheel
  digitalWrite(CIN1, LOW);
  digitalWrite(CIN2, HIGH);
  //front wheel
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  //back wheel
  digitalWrite(DIN1, LOW);
  digitalWrite(DIN2, LOW);

  analogWrite(PWMA, SPD);
  analogWrite(PWMC, SPD);

  //  Serial.println("Forward");
}

void goRight() {
  //front wheel
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  //back wheel
  digitalWrite(DIN1, HIGH);
  digitalWrite(DIN2, LOW);
  //left wheel
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  //right wheel
  digitalWrite(CIN1, LOW);
  digitalWrite(CIN2, LOW);

  analogWrite(PWMB, SPD);
  analogWrite(PWMD, SPD);

  //  Serial.println("Right");
}

void goLeft() {
  //front wheel
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);
  //back wheel
  digitalWrite(DIN1, LOW);
  digitalWrite(DIN2, HIGH);
  //left wheel
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  //right wheel
  digitalWrite(CIN1, LOW);
  digitalWrite(CIN2, LOW);
  
  analogWrite(PWMB, SPD);
  analogWrite(PWMD, SPD);

  //  Serial.println("Left");
}

void rotLeft() {
  //left wheel
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  //right wheel
  digitalWrite(CIN1, HIGH);
  digitalWrite(CIN2, LOW);
  //front wheel
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);
  //back wheel
  digitalWrite(DIN1, HIGH);
  digitalWrite(DIN2, LOW);

  analogWrite(PWMA, SPD);
  analogWrite(PWMC, SPD);
  analogWrite(PWMB, SPD);
  analogWrite(PWMD, SPD);

  //  Serial.println("Rot Left");
}

void rotRight() {
  //left wheel
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  //right wheel
  digitalWrite(CIN1, LOW);
  digitalWrite(CIN2, HIGH);
  //front wheel
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  //back wheel
  digitalWrite(DIN1, LOW);
  digitalWrite(DIN2, HIGH);

  analogWrite(PWMA, SPD);
  analogWrite(PWMC, SPD);
  analogWrite(PWMB, SPD);
  analogWrite(PWMD, SPD);

  //  Serial.println("Rot Right");
}

void turnLeft() {
}

void turnRight() {
}
