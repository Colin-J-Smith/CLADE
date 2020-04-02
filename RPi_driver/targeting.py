import sys
import os
from datetime import datetime

target_msg_size = 50
def target(target_write):
    command = "Targeting process started"
    time = datetime.now().strftime('%S.%f')
    command += " " + str(time)
    msg = command.ljust(target_msg_size)
    
    try:
        target_write.write(msg)
    except:
        sys.exit(0)

    if target_write == sys.stdout:
        print("")

    import time
    i = 1
    while i <= 1000:
        command = "tar{} {}".format(str(i).zfill(4), datetime.now().strftime('%S.%f'))
        msg = command.ljust(target_msg_size)
        try:
            target_write.write(msg)
        except:
            sys.exit(0)
        if target_write == sys.stdout:
            print("")
        i = i+1

if __name__=="__main__":
    nav(sys.stdout)
