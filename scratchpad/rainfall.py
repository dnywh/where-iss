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
willyWeatherApiKey = secrets.WILLY_WEATHER_API_KEY

# Choose location
locationId = 6833  # Coolum Beach
locationId = 13068  # Redesdale

# Flash the LED on and off to show things are happening
pico_led.off()  # turn off onboard LED
sleep(.05)  # Wait a bit
pico_led.toggle()  # turn on onboard LED
sleep(.05)  # Wait a bit
pico_led.toggle()  # turn off onboard LED
sleep(.05)  # Wait a bit
pico_led.toggle()  # turn on onboard LED
sleep(.05)  # Wait a bit
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
    checkRainProbability(6)
    # pico_led.on()  # turn on onboard LED


def checkRainProbability(i):
    # Make a network request
    # Read information from external site
    while True:
        # Should this instead be inside connect() as `while wlan.isconnected()?`
        print("Getting the weather report...")
        # Server that returns the current GMT+0 time.
        # currentDateAndTime = urequests.get("http://date.jsontest.com").json()
        # currentTime = currentDateAndTime['time']
        # print("Querying ISS position...")
        weatherReport = urequests.get(
            f"https://api.willyweather.com.au/v2/{willyWeatherApiKey}/locations/{locationId}/weather.json?forecasts=rainfallprobability&days=1&startDate=2022-11-19").json()
        # print(weatherReport['forecasts']['rainfallprobability']['days'][0]['entries'][3])

        locationName = f"{weatherReport['location']['name']}, {weatherReport['location']['state']}"
        rainfallEntries = weatherReport['forecasts']['rainfallprobability']['days'][0]['entries']
        relevantEntry = i  # Goes up in 3 hour increments: 0 = 1/2am, 1 = 4/5am, 2 = 7/8am, 3 = 10/11am, 4 = 1/2pm, 5 = 4/5pm, 6 = 7/8pm, 7 = 10/11pm
        selectedDateAndTime = rainfallEntries[relevantEntry]['dateTime']
        rainfallProbability = rainfallEntries[relevantEntry]['probability']

        print(
            f"Rainfall probably in {locationName} for {selectedDateAndTime} is {rainfallProbability}%")

        delay = 30  # in seconds
        print(f"Waiting {delay} seconds before next weather report...")
        sleep(delay)


try:
    connect()
    # The checkRainProbability() function could also be called here
except KeyboardInterrupt:
    machine.reset()
