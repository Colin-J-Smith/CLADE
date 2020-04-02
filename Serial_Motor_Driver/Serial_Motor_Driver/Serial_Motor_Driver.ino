/*
    This sketch reads data from the Serial input stream of the format "<COMMAND|Value1,Value2,Value3,...,ValueN>"
    and parses it into the COMMAND and an array of N values.
    Whitespace is ignored.
*/

#define START_MARKER '<'
#define END_MARKER '>'
#define COMMAND_SEP '|'
#define VALUE_SEP ','

//PIN VARIABLES
//the motor will be controlled by the motor A pins on the motor driver
const int AIN1 = 13;           //control pin 1 on the motor driver for the right motor
const int AIN2 = 12;            //control pin 2 on the motor driver for the right motor
const int BIN1 = 8;           //control pin 1 on the motor driver for the left motor
const int BIN2 = 9;            //control pin 2 on the motor driver for the left motor
const int PWMA = 11;            //speed control pin on the motor driver for the right motor
const int PWMB = 10;            //speed control pin on the motor driver for the left motor

//VARIABLES
int motorSpeedA = 0;       //starting speed for the motor
int motorSpeedB = 0;       //starting speed for the motor


void setup()
{
    Serial.begin(115200);

      //set the motor control pins as outputs
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
}

const size_t buffLen = 3;     // length of the expected message chunks (number of characters between two commas) (16-bit int has 5 digits + sign)
char buffer[buffLen + 1];     // add one for terminating null character
const size_t cmdBuffLen = 4; // length of the expected command string
char cmdBuffer[cmdBuffLen + 1];

uint8_t bufferIndex = 0;

const size_t arrayOfIntsLen = 2; // number of ints to receive
int arrayOfInts[arrayOfIntsLen];
uint8_t arrayOfIntsIndex = 0;

bool receiving = false;       // set to true when start marker is received, set to false when end marker is received
bool commandReceived = false; // set to true when command separator is received (or if command buffer is full)

void loop()
{
    if (Serial.available() > 0)
    {                                    // If there's at least one byte to read
        char serialByte = Serial.read(); // Read it

//        if (isWhiteSpace(serialByte))
//            return; // Ignore whitespace

        if (serialByte == START_MARKER)
        { // Start marker received: reset indices and flags
            receiving = true;
            commandReceived = false;
            bufferIndex = 0;
            arrayOfIntsIndex = 0;
            return;
        }
        if (receiving)
        { // If the start marker has been received
            if (!commandReceived)
            { // If the command hasn't been received yet
                if (serialByte == COMMAND_SEP || serialByte == END_MARKER)
                {                                  // If the command separator is received
                    cmdBuffer[bufferIndex] = '\0'; // Terminate the string in the buffer
                    if (strcmp(cmdBuffer, "RAW") == 0)
                    { // Check if the received string is "RAW"
                        Serial.println("RAW:");
                    }
                    else
                    {
                        Serial.print("Unknown command (");
                        Serial.print(cmdBuffer);
                        Serial.println("):");
                    }
                    if (serialByte == END_MARKER)
                    { // If the end marker is received
                        Serial.println("Message finished: (No data)");
                        Serial.println();
                        receiving = false; // Stop receivinng
                    }
                    else
                    {
                        bufferIndex = 0; // Reset the index of the buffer to overwrite it with the numbers we're about to receive
                        commandReceived = true;
                    }
                }
                else if (bufferIndex < cmdBuffLen)
                {                                          // If the received byte is not the command separator or the end marker and the command buffer is not full
                    cmdBuffer[bufferIndex++] = serialByte; // Write the new data into the buffer
                }
                else
                { // If the command buffer is full
                    Serial.println("Error: command buffer full, command is truncated");
                }
            }
            else if (serialByte == VALUE_SEP || serialByte == END_MARKER)
            { // If the value separator or the end marker is received
                if (bufferIndex == 0)
                { // If the buffer is still empty
                    Serial.println("\t(Empty input)");
                }
                else
                {                               // If there's data in the buffer and the value separator or end marker is received
                    buffer[bufferIndex] = '\0'; // Terminate the string
                    parseInt(buffer);           // Parse the input
                    bufferIndex = 0;            // Reset the index of the buffer to overwrite it with the next number
                }
                if (serialByte == END_MARKER)
                { // If the end marker is received
                    Serial.println("Message finished:");
                    printArrayOfInts(); // Print the values
                    Serial.println();
                    
                    spinMotor(arrayOfInts[]); // spin the motor
 
                    receiving = false; // Stop receivinng
                }
            }
            else if (bufferIndex < buffLen)
            {                                       // If the received byte is not a special character and the buffer is not full yet
                buffer[bufferIndex++] = serialByte; // Write the new data into the buffer
            }
            else
            { // If the buffer is full
                Serial.println("Error: buffer is full, data is truncated");
            }
            return; // Optional (check for next byte before executing the loop, may prevent the RX buffer from overflowing)
        }           // end if (receiving)
    }               // end if (Serial.available() > 0)
} // end of loop

bool isWhiteSpace(char character)
{
    if (character == ' ')
        return true;
    if (character == '\r')
        return true;
    if (character == '\n')
        return true;
    return false;
}

void parseInt(char *input)
{
    Serial.print("\tInput:\t");
    Serial.println(input);
    if (arrayOfIntsIndex >= arrayOfIntsLen)
    {
        Serial.println("Error: array of ints is full");
        return;
    }
    int value = atoi(input);
    arrayOfInts[arrayOfIntsIndex++] = value;
}

void printArrayOfInts()
{
    for (uint8_t i = 0; i < arrayOfIntsIndex; i++)
    {
        Serial.print(arrayOfInts[i]);
        Serial.print(' ');
    }
    Serial.println();
}


/********************************************************************************/
void spinMotor(int motorSpeedA, int motorSpeedB)      //function for driving the right motor
{
  // CONTROL MOTOR A
  if (motorSpeedA > 0)                                //if the motor should drive forward (positive speed)
  {
    digitalWrite(AIN1, HIGH);                         //set pin 1 to high
    digitalWrite(AIN2, LOW);                          //set pin 2 to low
  }
  else if (motorSpeedA < 0)                           //if the motor should drive backward (negative speed)
  {
    digitalWrite(AIN1, LOW);                          //set pin 1 to low
    digitalWrite(AIN2, HIGH);                         //set pin 2 to high
  }
  else                                                //if the motor should stop
  {
    digitalWrite(AIN1, LOW);                          //set pin 1 to low
    digitalWrite(AIN2, LOW);                          //set pin 2 to low
  }
  analogWrite(PWMA, abs(motorSpeedA));                //now that the motor direction is set, drive it at the entered speed

  // CONTROL MOTOR B
  if (motorSpeedB > 0)                                //if the motor should drive forward (positive speed)
  {
    digitalWrite(BIN1, HIGH);                         //set pin 1 to high
    digitalWrite(BIN2, LOW);                          //set pin 2 to low
  }
  else if (motorSpeedB < 0)                           //if the motor should drive backward (negative speed)
  {
    digitalWrite(BIN1, LOW);                          //set pin 1 to low
    digitalWrite(BIN2, HIGH);                         //set pin 2 to high
  }
  else                                                //if the motor should stop
  {
    digitalWrite(BIN1, LOW);                          //set pin 1 to low
    digitalWrite(BIN2, LOW);                          //set pin 2 to low
  }
  analogWrite(PWMB, abs(motorSpeedB));                //now that the motor direction is set, drive it at the entered speed
}
