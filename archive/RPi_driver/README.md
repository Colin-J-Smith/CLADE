# Driver for the police academy robot.

## States
The driver has four states: initializing, looking, turning, and shooting.

### Initializing
During initializing, the driver creates child process for the navigation and targeting modules and pipes to communicate with them, and starts serial communication with the Arduino. The state then becomes looking.

### Looking
During looking, the driver will receive and process messages from both modules. If the targeting module finds a target, the state becomes shooting. Otherwise, if the navigation module commands a turn, the state becomes turning.

### Turning
During turning, all targeting messages are ignored as the driver process turning commands in close to real time. When the navigation module commands to continue straight, the state becomes looking.

### Targeting
During targeting, all navigation messages are ignored as the driver processes shooting commands in close to real time. When the targeting module indicates the target is hit, the state becomes looking.

## Logic

### Timestamp
When a message is received from either module, the sent timestamp is compared with the received time. If the time delay is more than 0.5 seconds, it can be assumed that all messages in the input buffer are old. The entire input buffer from that module is then cleared.
