# Template for the navigation code to intergrate with the driver. The driver
# imports `nav` and `nav_msg_size` so let me know if you change either of
# those names.
#
# `nav_write` is a file object that you'll write the commands to so that they
# can be read by the driver
#
# `nav_msg_size` is the maximum length any of your commands will be
#
# You can test this file on it's own with `python3 navigation.py`. This will
# output the messages to the console instead of to the driver.

import sys
import os
from datetime import datetime

nav_msg_size = 50
def nav(nav_write):
    
    # generate a command
    command = "Navigation process started"

    # append the time
    time = datetime.now().strftime('%S.%f')
    command += " " + str(time)

    # format the command to be read by the driver by adding spaces to the end
    #    of the command until it is the length `nav_msg_size` so the correct 
    #    number of characters is read by the driver every time
    msg = command.ljust(nav_msg_size)

    # output the message
    try:
        nav_write.write(msg)
    except:
        sys.exit(0) # broken pipe (driver has closed)

    # prints a newline if outputting to the console for debugging
    if nav_write == sys.stdout:
        print("")
        
    # ---------------
    # TEMP - for testing the driver
    import time
    i = 1
    while i <= 1000:
        command = "nav{} {}".format(str(i).zfill(4), datetime.now().strftime('%S.%f'))
        msg = command.ljust(nav_msg_size)    
        try:
            nav_write.write(msg)
        except:
            sys.exit(0)
        if nav_write == sys.stdout:
            print("")
        i = i+1
    # ---------------

if __name__=="__main__":
    nav(sys.stdout)
