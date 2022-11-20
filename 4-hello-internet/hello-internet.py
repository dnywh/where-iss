# Forked from Waveshare's Pico ePaper-5.83py
# See Waveshare wiki for more original

# https://docs.micropython.org/en/latest/library/machine.html
from machine import Pin, SPI
import framebuf
import utime
import network  # Handles connecting to Wi-Fi
import urequests  # Handles making and servicing network requests
from time import sleep
import secrets

# Fill in your network name (ssid) and password here as strings
# Or save them to a sibling secrets.py file and import it
ssid = secrets.SSID
password = secrets.PASSWORD

# Set display resolution
EPD_WIDTH = 648
EPD_HEIGHT = 480

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_5in83(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data2(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte(data)
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print("Printing press busy")
        while (self.digital_read(self.busy_pin) == 0):  # 1: idle, 0: busy
            self.delay_ms(10)
        print("Printing press released")

    def TurnOnDisplay(self):
        self.send_command(0x12)
        self.delay_ms(100)
        self.ReadBusy()

    def init(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0x01)  # POWER SETTING
        self.send_data(0x07)
        self.send_data(0x07)  # VGH=20V,VGL=-20V
        self.send_data(0x3f)  # VDH=15V
        self.send_data(0x3f)  # VDL=-15V

        self.send_command(0x04)  # POWER ON
        self.delay_ms(100)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0X00)  # PANEL SETTING
        self.send_data(0x1F)  # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)  # tres
        self.send_data(0x02)  # source 648
        self.send_data(0x88)
        self.send_data(0x01)  # gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        self.send_command(0X50)  # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x10)
        self.send_data(0x07)

        self.send_command(0X60)  # TCON SETTING
        self.send_data(0x22)
        # EPD hardware init end
        return 0

    def display(self, image):
        if (image == None):
            return
        self.send_command(0x13)  # WRITE_RAM
        self.send_data2(image)
        self.TurnOnDisplay()

    def Clear(self, color):
        self.send_command(0x13)  # WRITE_RAM
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(color)
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x02)  # DEEP_SLEEP_MODE
        self.ReadBusy()
        self.send_command(0x07)
        self.send_data(0xa5)

        self.delay_ms(2000)
        self.module_exit()


# Make Waveshare ePaper screen available
epd = EPD_5in83()

# Prepare Wi-Fi


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
    updateData()


def updateData():
    max_amount_of_refreshes = 4
    current_refresh_number = 0
    refresh_delay = 10  # in seconds

    while True:
        print("Querying ISS coordinates...")
        iss = urequests.get("http://api.open-notify.org/iss-now.json").json()
        issLat = iss['iss_position']['latitude']
        issLon = iss['iss_position']['longitude']
        print(
            f"The current ISS coordinates are: {issLat}, {issLon}")
        printPaper(issLat, issLon)
        current_refresh_number += 1
        print(
            f"Printed edition #{current_refresh_number} of #{max_amount_of_refreshes}. Waiting {refresh_delay} seconds before continuing...")

        # Wait before updating again...

        sleep(refresh_delay)

        if current_refresh_number >= max_amount_of_refreshes:
            print(
                f"That #{current_refresh_number} of #{max_amount_of_refreshes} was the last one. I'm going to sleep...")
            # Clearafter a while to prevent burn-in
            clearPaper()
            break


def printPaper(lat, lon):
    print("Printing paper...")
    # Prepare e-ink screen

    epd.Clear(0x00)
    epd.fill(0x00)

    # # Draw one clear rectangle with a black stroke
    epd.rect(0, 0, EPD_WIDTH, 100, 1)

    # # Write some text in black
    epd.text("International Space Station Coordinates:", 4, 10, 1)
    epd.text(f"Latitude: {lat}", 4, 40, 1)  # Or hex
    epd.text(f"Longitude: {lon}", 4, 70, 1)

    # Render all of the above to screen
    epd.display(epd.buffer)


def clearPaper():
    # Prepare for sleep
    print("Clearing the printing press...")
    # Vendored from Pico-ePaper-5.83.py to ensure screen doesn't burn in
    epd.init()
    epd.Clear(0x00)
    print("Going to sleep. Goodbye!")
    epd.delay_ms(2000)
    epd.sleep()


try:
    connect()
    # The regularlyCheckSomething() function could also be called here
except KeyboardInterrupt:
    machine.reset()
