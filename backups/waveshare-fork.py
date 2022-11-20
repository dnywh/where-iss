# Forked from Waveshare's Pico ePaper-5.83py
# See Waveshare wiki for more original

# TODO
# - [ ] Have the RPi LED turn on when working on stuff
# - [ ] How can I mimick greys given that the ePaper screen doesn't support them? Dithering?

from machine import Pin, SPI
import framebuf
import utime

# Display resolution
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
        print("e-Paper busy")
        while (self.digital_read(self.busy_pin) == 0):  # 1: idle, 0: busy
            self.delay_ms(10)
        print("e-Paper busy release")

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


# Only if this is the main script (not an import...)
if __name__ == '__main__':
    # Tell Python that I want to use the Waveshare ePaper thing as my screen
    epd = EPD_5in83()
    epd.Clear(0x00)

    # Use framebuf to draw basic stuff ("graphics primitives") to the screen
    # https://mpython.readthedocs.io/en/master/library/micropython/framebuf.html
    # http://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html?highlight=fill_rect
    # Use byte array for more complex images:
    # https://www.youtube.com/watch?v=WtmAXsv7q28
    # ...that plus some info on writing fonts
    # https://blog.miguelgrinberg.com/post/micropython-and-the-internet-of-things-part-vi-working-with-a-screen

    # All the below hex colors are reversed
    # Maybe that's just how the Waveshare wants it?
    # White hex code (0xff) = what's printed (in black)?
    # Black hex code (0x00) = what's not printed (remains white)?
    # Color sets:
    # https://enchantia.com/software/graphapp/doc/tutorial/colours.htm
    # Math:
    # https://gist.github.com/zealoushacker/3970953

    # Fill the entire screen with white (actually black hex code)
    epd.fill(0x00)

    # Write some text in black
    # So I can write black either with a 1...
    epd.text("Danny's Waveshare", 5, 10, 1)
    epd.text("Pico_ePaper-5.83", 5, 40, 0xff)  # Or hex
    epd.text("Raspberry Pico", 5, 70, 0xff)
    # Write some gray text
    # Doesn't work. Floating numbers don't work either (e.g. 0.5)
    # TODO: Confirm Waveshare screens like this can only do solid black or white
    # epd.text("Testing out gray text", 200, 40, 0x80)
    # epd.text("Testing out light gray text", 200, 70, 0xC0)

    # Draw a 'manual' rectangle with an X in the middle
    epd.vline(10, 90, 60, 0xff)
    epd.vline(120, 90, 60, 0xff)
    epd.hline(10, 90, 110, 0xff)
    epd.hline(10, 150, 110, 0xff)
    epd.line(10, 90, 120, 150, 0xff)
    epd.line(120, 90, 10, 150, 0xff)

    # Draw one clear rectangle with a black stroke
    epd.rect(10, 180, 50, 80, 0xff)

    # Draw two black solid rectangles
    epd.fill_rect(70, 180, 50, 80, 1)
    epd.fill_rect(200, 100, 400, 100, 0xff)

    # Render all of the above to screen
    epd.display(epd.buffer)

    # Wait a few seconds
    epd.delay_ms(5000)

    # Draw MicroPython logo and print some text:
    print("Showing MicroPython logo...")
    epd.fill(0)  # Fill screen with white?
    # Make a 32x32px black square from top left corner
    epd.fill_rect(0, 0, 32, 32, 1)
    # Make a 28x28px white square 2px inset from top left corner
    epd.fill_rect(2, 2, 28, 28, 0)
    epd.vline(9, 8, 22, 1)  # Draw black lines for the remaining details
    epd.vline(16, 2, 22, 1)
    epd.vline(23, 8, 22, 1)
    epd.fill_rect(26, 24, 2, 4, 1)  # Make black the snake eye
    epd.text('MicroPython', 40, 0, 1)  # Render text
    epd.text('Danny', 40, 12, 1)
    epd.text('ePaper e-ink', 40, 24, 1)

    # Render all of the above to screen
    epd.display(epd.buffer)

    # Wait ten seconds
    epd.delay_ms(10000)

    # Prepare to sleep
    epd.init()
    epd.Clear(0x00)
    # Fill the entire screen with white. Maybe unecessary as the above step adoes this too? Seems to help stop artefacts on the let side FWIW
    epd.fill(0)
    # Wait four seconds then sleep
    epd.delay_ms(4000)
    print("Going to sleep...")
    epd.sleep()
