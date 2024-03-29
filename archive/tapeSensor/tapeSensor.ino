float sensVal;  //value read in by the reflectance sensor
int sensPin = A0;

float threshVal = 1.5; //nominal threshold value
float threshLow = threshVal -.5; // lower hysteretic threshold
float threshHigh = threshVal +.5; // upper hysteretic threshold

bool outputVar = LOW; // variable that imitates the LED output on the tape follower circuit

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); // set up the serial debug output
  pinMode(sensPin, INPUT); // set up the sensor pin

}

void loop() {
  // put your main code here, to run repeatedly:
  sensVal = 5.0*analogRead(sensPin)/1023.0; // read in the sensor value and remap it to the voltage range

  if (outputVar) { // if we are above the threshold (black surface)
    if (sensVal < threshLow) { // if the sensed value drops below the threshold
      outputVar = LOW; // turn off the LED
    }
  }else { // if we are below the threshold (white surface)
    if (sensVal > threshHigh) { // if the sensed value rises above the threshold
      outputVar = HIGH; // turn on the LED
    }
  }

  Serial.print("LED State:");
  Serial.print('\t');
  Serial.print(outputVar);
  Serial.print('\t');
  Serial.print("Sensor Val:");
  Serial.print('\t');
  Serial.println(sensVal);
    

}
