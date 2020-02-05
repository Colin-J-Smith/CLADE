#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 18:12:57 2020

@author: colin
"""
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# INIT MODE
# Set up 7 of the pins to control the LEDS
# Set the cycle period

# PAUSE MODE
# Turn off all LEDS
# Reset the cycle timer
# Wait for a button press to start the cycle timer
# Set the incremement to the first LED

# PLAY MODE
# Listen for a button press (with debounce)
## If button pressed, check which LED is active
### If green LED is active, keep the green LED on for 3 seconds and switch to PAUSE
### If another LED is pressed, continue PLAY mode


class Cyclone(object):
   
    def __init__(self, period=0.5):
        self.last_time = time.perf_counter()
        self.led_pins = range(19,26)
        self.leds = {}
       
        self.button_pin = 10
        self.last_button_state = False
       
        self.winning_led = 22 # uses a 0 indexed list
        self.current_led = min(self.led_pins)
       
        self.period = 1 # number of seconds each led is lit up
       
        # Set up the GPIO LED pins
        for channel in self.led_pins:
            GPIO.setup(channel, GPIO.OUT)
            self.leds[str(channel)] = GPIO.PWM(channel, 50) # PWM at 50Hz
            self.leds[str(channel)].start(50)
       
        # Set up the button input pin
        GPIO.setup(self.button_pin, GPIO.IN)
       
        # Enter pause mode
        self.pause()
   
    def pause(self):
        # turn off all leds
        for key, val in self.leds.items():
            val.stop()
       
        # wait for the button to be pressed before restarting
        while GPIO.input(self.button_pin):
            time.sleep(0.1)
        self.play()
       
   
    def play(self):
        # start a single period
        while self.last_time - time.perf_counter() < self.period:
            # Light the next LED
            self.leds[str(self.current_led)].start(50) # 50% duty cycle
           
            # check the button state
            button_state = GPIO.input(self.button_pin)
           
            # If the button has been pressed only during this iteration
            if (self.last_button_state != button_state) and (button_state):
                # check if the active led pin is a winner
                if self.current_led == self.winning_led:
                    time.sleep(3) # wait for 3 seconds
                    self.pause() # pause the game
                    return
                   
            # save the button state for this check
            self.last_button_state = button_state


        # turn off the led
        self.leds[str(self.current_led)].stop()

        # increment the LED pin
        if self.current_led == max(self.led_pins):
            self.current_led = min(self.led_pins)
        else:
            self.current_led += 1
         
        # When a single period finishes
        # record the iteration time
        self.last_time = time.perf_counter()
        # repeat the loop
        self.play() 


if __name__== "__main__":
  Cyclone()