# A more complex local network web server from your Raspberry Pi Pico W
# Provides a template for:
#   1. Connecting to a local network
#   2. Serving a webpage
#   3. Controlling the Pi's sensors (LED and temperature) from the webpage
#   4. Network requests: reading information from another site

# Based on:
# Getting started with your Raspberry Pi Pico W
# https://projects.raspberrypi.org/en/projects/get-started-pico-w/
# See also:
# https://core-electronics.com.au/guides/raspberry-pi-pico-w-connect-to-the-internet/

import network  # Handles connecting to Wi-Fi
import urequests  # Handles making and servicing network requests
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led
import machine

# Fill in your network name (ssid) and password here:
# TODO: Can I use .env variables?
ssid = 'Coastal Coworking - 2.4GHz'
password = '21Heathfield4573!'

# Begin by turning the onboard LED on
pico_led.on()


print("Trying to connect")


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)  # Wait one second before trying again
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip


def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection


def webpage(temperature, state):
    # Template HTML
    html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta http-equiv="X-UA-Compatible" content="IE=edge" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Danny's Pi</title>
            </head>
            <body>
                <form action="./lighton">
                <input type="submit" value="Light on" />
                </form>
                <form action="./lightoff">
                <input type="submit" value="Light off" />
                </form>
                <p>LED is {state}</p>
                <p>Temperature is {temperature}</p>
            </body>
            </html>
            """
    return str(html)


def serve(connection):
    print("Starting a web server")
    # Start a web server
    state = 'OFF'
    # Turn off LED once connected and web server spun up
    pico_led.off()
    temperature = 0

    # Listen for connections, serve client
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        if request == '/lighton?':
            pico_led.on()
            state = 'ON'
            print("LED turned on")
        elif request == '/lightoff?':
            pico_led.off()
            state = 'OFF'
            print("LED turned off")
        temperature = pico_temp_sensor.temp
        html = webpage(temperature, state)
        client.send(html)
        client.close()


def makeTestNetworkRequest():
    # Make a network request
    # Read information from external site
    # Example 2. urequests can also handle basic json support! Let's get the current time from a server
    print("\n\n2. Querying the current GMT+0 time:")
    # Server that returns the current GMT+0 time.
    r = urequests.get("http://date.jsontest.com")
    print(r.json())


try:
    ip = connect()
    connection = open_socket(ip)
    makeTestNetworkRequest()
    serve(connection)
except KeyboardInterrupt:
    machine.reset()
