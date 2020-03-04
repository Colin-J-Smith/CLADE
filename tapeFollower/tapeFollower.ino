/* Logic
 *  if left sensor sees black, stop left motor
 *  
 */
//---------------------------------------------------------------------------
bool debug = true;

//----------------------------------------------------------------------------
float sensVal_L; //value read in by the reflectance sensor L
float sensVal_R; //value read in by the reflectance sensor R
int sensPin_L = A0;
int sensPin_R = A1;

float threshVal = 3.5; //nominal threshold value
float threshLow = threshVal -1; // lower hysteretic threshold
float threshHigh = threshVal +1; // upper hysteretic threshold

bool outputVal_L = false;
bool outputVal_R = false;
bool outputVar = LOW; // variable that imitates the LED output on the tape follower circuit

//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); // set up the serial debug output
  
  pinMode(sensPin_L, INPUT); // set up the sensor pin
  pinMode(sensPin_R, INPUT); // set up the sensor pin
  
  //set the motor control pins as outputs
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(PWMB, OUTPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  sensVal_L = 5.0*analogRead(sensPin_L)/1023.0; // read in the sensor value and remap it to the voltage range
  sensVal_R = 5.0*analogRead(sensPin_R)/1023.0; // read in the sensor value and remap it to the voltage range

  // check both sensors
  // if one of them detects yellow
  // stop the corresponding wheel
  // if both detect black, turn the wheels at the same rate

  // 4 Logic cases
  //TODO: change to switch statement
  if (sensVal_L < threshLow){//seeing black on L
    motorSpeedA = 255; //drive the left motor
  }
  if (sensVal_L > threshHigh){ //seeing yellow on L
    motorSpeedA = 0; //stop the left motor
  }
  if (sensVal_R < threshLow){//seeing black on R
    motorSpeedB = 255; //drive the right motor
  }
  if (sensVal_R > threshHigh){//seeing yellow on R
    motorSpeedB = 0; //stop the right motor
  }

  spinMotor(motorSpeedA, motorSpeedB);

  if (debug) {
    Serial.print('LED State:');
    Serial.print('\t');
    Serial.print(outputVar);
    Serial.print('\t');
    Serial.print('Sensor Val:');
    Serial.print('\t');
    Serial.println(sensVal);
  }
    

}


//---------------------------------------------------------------------------
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
