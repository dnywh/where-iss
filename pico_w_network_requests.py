# A more complex local network web server from your Raspberry Pi Pico W
# Provides a template for:
#   - Connecting to a local network
#   - Controlling the Pi's sensors (LED and temperature) from the webpage
#   - Making network requests and passing that JSON data

import network  # Handles connecting to Wi-Fi
import urequests  # Handles making and servicing network requests
from time import sleep
from picozero import pico_led
import machine
import secrets

# Fill in your network name (ssid) and password here as strings
# Or save them to a sibling secrets.py file and import it like I have
ssid = secrets.SSID
password = secrets.PASSWORD


# Flash the LED on and off to show things are happening
pico_led.off()  # turn off onboard LED
sleep(.5)  # Wait half a second
pico_led.toggle()  # turn on onboard LED
sleep(.5)  # Wait half a second
pico_led.toggle()  # turn off onboard LED
sleep(.5)  # Wait half a second
pico_led.toggle()  # turn on onboard LED
sleep(.5)  # Wait half a second
pico_led.off()  # turn off onboard LED


print("Trying to connect...")


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)  # Wait one second before trying again
    ip = wlan.ifconfig()[0]  # Get only IP address
    print(f'Connected on {ip}')  # Print this IP address
    regularlyCheckSomething()
    pico_led.on()  # turn on onboard LED


def regularlyCheckSomething():
    # Make a network request
    # Read information from external site
    while True:
        # Should this instead be inside connect() as `while wlan.isconnected()?`
        print("Querying date and time...")
        # Server that returns the current GMT+0 time.
        currentDateAndTime = urequests.get("http://date.jsontest.com").json()
        currentTime = currentDateAndTime['time']
        print("Querying ISS position...")
        iss = urequests.get("http://api.open-notify.org/iss-now.json").json()
        issLat = iss['iss_position']['latitude']
        issLon = iss['iss_position']['longitude']
        print(
            f"It is currently {currentTime}. The ISS coordinates are: {issLat}, {issLon}")
        # Wait before updating again...
        delay = 10  # in seconds
        print(f"Waiting {delay} seconds before next update...")
        sleep(delay)


try:
    connect()
    # The regularlyCheckSomething() function could also be called here
except KeyboardInterrupt:
    machine.reset()
