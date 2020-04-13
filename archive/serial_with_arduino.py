import serial

def get_mtr_cmd(motor_num):
    print("Inputs for motor %d:" % motor_num)
    
    # get direction
    valid_input = False
    while (not valid_input):
        direction = input("    What direction (CW or CCW)? ").lower()
        if direction == "cw":
            sign = '-'
            valid_input = True
        elif direction == "ccw":
            sign = ''
            valid_input = True
        else:
            print("    Direction must be CW or CCW")
        
    # get speed
    valid_input = False
    while (not valid_input):
        speed = input("    What speed (0 to 100)? ")
        try:
            speed = int(speed)
            if speed >= 0 and speed <= 100:
                valid_input = True
            else:
                raise Exception()
        except:
            print("    Speed must be 0.0 to 100.0")

    cmd = "{}{}".format(sign,speed).rjust(4, ' ')
    return cmd

#end get_motor_cmd()

def main():
    outbound = serial.Serial(port="/dev/ttyUSB0", baudrate=115200)
    print("Found port to Arduino")

    while(True):
        packet = "<"

        # specify wheels
        packet += "wheels"
        packet += "|"

        # get command for motor 1
        packet += get_mtr_cmd(1)
        packet += ","

        # get command for motor 2
        packet += get_mtr_cmd(2)
        packet += ">"
        
        # send command
        outbound.write(packet.encode('utf-8'))
        print("Sending command: " + packet)
        print("")
        
        # get feedback
        if outbound.in_waiting:
            outbound.readline()

    #end while(True)

#end main()


if __name__ == '__main__':
    main()
