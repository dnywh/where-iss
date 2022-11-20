# A basic example of showing how many days of the year have passed
# Forked from Waveshare's Pico ePaper-5.83py


from machine import Pin, SPI
import framebuf
import utime
import math  # Required to draw circles

# Display resolution
EPD_WIDTH = 648
EPD_HEIGHT = 480

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

# Waveshare stuff


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

# Circle function by Tony Goodhew
# https://www.instructables.com/Computer-Graphics-101-With-Pi-Pico-and-Colour-Disp/


def circle(x, y, r, c):
    epd.hline(x-r, y, r*2, c)
    for i in range(1, r):
        a = int(math.sqrt(r*r-i*i))  # Pythagoras!
        epd.hline(x-a, y+i, a*2, c)  # Lower half
        epd.hline(x-a, y-i, a*2, c)  # Upper half


# Only if this is the main script (not an import...)
if __name__ == '__main__':
    # Tell Python that I want to use the Waveshare ePaper thing as my screen
    epd = EPD_5in83()
    epd.Clear(0x00)

    # Fill the entire screen with white (actually black hex code)
    epd.fill(0x00)

    # Calculate where in the year we are
    year_day = utime.localtime()[7]
    # year_progress = (year_day - 1) / 365 # Returns something like 0.8684931507 for Nov 13
    # The '365' could be dynamic (say year_length) given the number changes slightly depending on leap years

    # Set cols and rows (grid size)
    # 19*19 = 361. The real grid should stop at 365 or, even better, year_length
    cols = 19
    rows = 19
    # Set scale for drawing as 19*19 pixels is tiny
    scale = 18

    # Center grid
    x_offset = int((EPD_WIDTH - (cols * scale)) / 2)
    y_offset = int((EPD_HEIGHT - (rows * scale)) / 2)

    # Draw rectangle with black stroke, slightly bigger than the below contents
    epd.rect(x_offset - 1, y_offset - 1,
             (cols * scale) + 2, (rows * scale) + 2, 1)

    # Prepare variables
    grid_index = 0
    # fill = 1
    x_val = 0
    y_val = 0

    # Traverse through rows top to bottom
    for kk in range(rows):
        # Traverse through cols left to right
        for jj in range(cols):
            # Compare day in grid against current day in year
            if grid_index <= year_day:  # If the day in grid has already passed or is today...
                # Paint a black square at that grid coordinate
                # epd.fill_rect((x_val + x_offset),
                #               (y_val + y_offset), scale, scale, 1)

                # Paint a smaller black square in the center of the grid coordinate
                # epd.fill_rect(int((x_val + x_offset) + (scale / 4)),
                #               int((y_val + y_offset) + (scale / 4)),
                #               int(scale / 2),
                #               int(scale / 2),
                #               1)
                # Paint a dot in the center of the grid coordinate
                # circle (cx,cy,r,c)
                circle(int((x_val + x_offset) + (scale / 2)),
                       int((y_val + y_offset) + (scale / 2)),
                       int(scale / 4),
                       1)

            # else:  # If the day in the grid is in the future
                # Paint a white square with black (inner) outline at that grid coordinate
                # epd.rect((x_val + x_offset),
                #          (y_val + y_offset), scale, scale, 1)
            # Move to the next column in the row
            x_val += scale
            # Store what grid_index we're up to
            grid_index += 1
        # Go to next row down
        y_val += scale
        # Go to first column on left
        x_val = 0

    # Render all of the above to screen
    epd.display(epd.buffer)

    # Keep on screen for a while
    epd.delay_ms(30000)  # 30 seconds

    # ...then prepare to sleep
    epd.init()
    epd.Clear(0x00)
    # Fill the entire screen with white. Maybe unecessary as the above step adoes this too? Seems to help stop artefacts on the let side FWIW
    epd.fill(0)
    # Wait four seconds then sleep
    epd.delay_ms(4000)
    print("Going to sleep...")
    epd.sleep()
