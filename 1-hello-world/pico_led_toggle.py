# Pico LED Toggle
# pico_led_toggle.py

# Adapted from Core Electronic's tutorial and video
# How to Setup a Raspberry Pi Pico and Code with Thonny
# https://core-electronics.com.au/guides/raspberry-pi-pico/how-to-setup-a-raspberry-pi-pico-and-code-with-thonny/
# Code changed to work for Raspberry Pi Pico W (LED pin assignment is different)

# Be sure to install the UF2 file before starting. TODO: Add to general README. Via Thonny or downloading the file online that looks like:
# wrp2-pico-20220117-v1.18.uf2


from machine import Pin
from time import sleep

led = Pin('LED', Pin.OUT)

n = 0

while True:
    led.toggle()
    print("13 times {} is {}".format(n, 13*n))
    n = n+1
    sleep(0.5)
