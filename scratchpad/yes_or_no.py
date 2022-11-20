# Forked from Waveshare's Pico_ePaper-5.83.py file

# Resources:
# - Turning PNG, JPEG etc images into byte array format: https://diyusthad.com/image2cpp
# - Making that byte array format exactly what the frame buffer wants: https://forums.pimoroni.com/t/pico-and-ssd1306-bounce-your-own-icons-tutorial/16548
# - Understanding how frame buffer formats work: https://blog.miguelgrinberg.com/post/micropython-and-the-internet-of-things-part-vi-working-with-a-screen

# Waveshare stuff
from machine import Pin, SPI
import framebuf
import utime
import random  # For debugging
from image_files import image_no, image_yes

# Display resolution
EPD_WIDTH = 648
EPD_HEIGHT = 480

# Waveshare stuff
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

        self.send_command(0X00)  # PANNEL SETTING
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


# My stuff
def show_image(img, w, h, bg):
    # TODO: what does epd.init() do? Anything helpful?
    epd.Clear(bg)
    # TODO are both this and the above necessary?
    epd.fill(bg)

    # Our desired image
    # Image formatted as byte array via image2cpp
    buffer = bytearray(img)

    # Center image
    x = int((EPD_WIDTH - w) / 2)
    y = int((EPD_HEIGHT - h) / 2)

    # Match image by setting frame buffer to MONO_HLSB
    fb = framebuf.FrameBuffer(
        buffer, w, h, framebuf.MONO_HLSB)

    # Position the image
    epd.blit(fb, x, y)

    # Display the image
    epd.display(epd.buffer)


def go_to_sleep():
    epd.init()
    epd.Clear(0x00)
    epd.delay_ms(2000)
    print("Going to sleep.")
    epd.sleep()


# Main
if __name__ == '__main__':
    epd = EPD_5in83()

    yes = 1
    current_state = yes

    if yes:
        show_image(image_yes, 324, 264, 0xff)
    else:
        show_image(image_no, 324, 166, 0x00)

    # Wait X seconds
    epd.delay_ms(5000)

    yes = random.randint(0, 1)

    if yes & current_state:
        print("Was already yes, keeping as-is")

    if not yes & current_state:
        show_image(image_no, 324, 166, 0x00)

    # Wait X seconds
    epd.delay_ms(5000)
    # Sleep
    go_to_sleep()
