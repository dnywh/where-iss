
from PIL import Image, ImageDraw, ImageFont
import secrets
import traceback
import time
from waveshare_epd import epd7in5_V2
import logging
import sys
import os
import requests
picdir = os.path.join(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


# Test
password = secrets.PASSWORD

logging.basicConfig(level=logging.DEBUG)

# Get API results

data = requests.get("http://api.open-notify.org/iss-now.json").json()
issLat = data['iss_position']['latitude']
issLon = data['iss_position']['longitude']

# Convert results to a string

lat = 'Latitude:   ' + f"{issLat}"
lon = 'Longitude:   ' + f"{issLon}"

# Update the display

try:
    print("trying out print")
    logging.info(f"Shhh! Secret is: '{password}'")
    logging.info("Updating display")
    epd = epd7in5_V2.EPD()

    logging.info("initialising and clearing display")
    epd.init()
    epd.Clear()

    font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    font32 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 32)

    logging.info("Drawing new image on the horizontal plane")
    # Construct images
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images
    image = Image.new('1', (epd.width, epd.height),
                      255)  # 255: clear the frame
    # mapImage = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)
    # drawMapImage = ImageDraw.Draw(mapImage)

    # Draw stuff
    draw.text((10, 0), 'hello Danny!', font=font24, fill=0)
    draw.text((10, 100), lat, font=font24, fill=0)
    draw.text((10, 200), lon, font=font24, fill=0)

    bmp = Image.open(os.path.join(picdir, 'youtubeIcon.bmp'))
    image.paste(bmp, (265, 80))

    # Render everything on screen
    epd.display(epd.getbuffer(image))

    # Sleep
    time.sleep(12)

    logging.info("Clear...")
    epd.init()
    epd.Clear()

    logging.info("Goto Sleep...")
    epd.sleep()

    logging.info("Putting display to sleep")
    epd.sleep()
    epd.Dev_exit()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
