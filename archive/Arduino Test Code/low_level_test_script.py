import serial
import time



# Create a functions that scripts the actions of the robot
def generate_cmds(n):
    #tur_cmds = ["STP", "UPP","DWN","LFT", "RGT", "FIR"]
    #mtr_cmds = ["STP","LFT", "RGT", "FWD", "BCK", "LLL", "RRR"]

    samples = []
    for i in range(n):
        if i < n/10:
            samples += [["STP", "FWD"]]
        elif i < 2*n/10:
            samples += [["STP", "LLL"]]
        elif i < 3*n/10:
            samples += [["STP", "FWD"]]
        elif i < 4*n/10:
            samples += [["STP", "RRR"]]
        elif i < 5*n/10:
            samples += [["STP", "STP"]]
        elif i < 6*n/10:
            samples += [["LFT", "STP"]]
        elif i < 7*n/10:
            samples += [["LFT", "STP"]]
        elif i < 8*n/10:
            samples += [["RGT", "STP"]]
        elif i < 9*n/10:
            samples += [["STP", "STP"]]
        else:
            samples += [["STP", "STP"]]
    samples+= [["FIR", "STP"]]

    return samples


#end get_cmd()

#function for assembling and sending a packet for the turret
def send_msg(cmd, device):
    packet = "<"
    packet += str(cmd)
    packet += ">"

    # send command
    device.write(packet.encode('utf-8'))
#end send_tur_msg()



def main():
    outbound_tur = serial.Serial(port="/dev/ttyACM0", baudrate=9600)
    outbound_mtr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)
    print("Found port to Arduino")

    n_samples = 100
    samples = generate_cmds(n_samples)

    for i in range (len(samples)):
        [cmd_tur, cmd_mtr] = samples[i]
        send_msg(cmd_tur, outbound_tur)
        send_msg(cmd_mtr, outbound_mtr)
        time.sleep(0.1)

    #end for:

#end main()


if __name__ == '__main__':
    main()
