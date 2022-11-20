import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


import logging
from waveshare_epd import epd7in5_V2 # Waveshare display stuff
import time # Delays in seconds
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # Image stuff
import traceback

import requests # Needed to check the ISS location
import secrets  # Needed for Mapbox access token
import math  # Needed for converting lat and long
# from gazpacho import Soup # Needed for finding the Mapbox image on the URL
import urllib.request # Needed for saving the Mapbox image

mapboxAccessToken = secrets.MAPBOX_ACCESS_TOKEN

logging.basicConfig(level=logging.DEBUG)

# Get API results

issData = requests.get("http://api.open-notify.org/iss-now.json").json()
issLat = float(issData['iss_position']['latitude'])
issLon = float(issData['iss_position']['longitude'])

# Convert results to a string

# lat = 'Latitude:   ' + f"{issLat}"
# lon = 'Longitude:   ' + f"{issLon}"

# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon./lat._to_tile_numbers_2


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


# Convert latitude and longitude (along with desired zoom) to map tile
mapTileNameZoom = 10
mapTileNameX = deg2num(issLat, issLon, mapTileNameZoom)[0]
mapTileNameY = deg2num(issLat, issLon, mapTileNameZoom)[1]

# EDP 7.5" = 800x480
mapImageWidth = 400
mapImageHeight = mapImageWidth
# Square
mapTileSize = (mapImageWidth, mapImageHeight)

# Update the display

try:
    print(f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileNameZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}")
    # Save a copy of the map tile
    urllib.request.urlretrieve(f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileNameZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}", "map-tile.jpg")
    # url = "https://via.placeholder.com/150"
    logging.info(f"Latitude: {issLat}, Longitude: {issLon}")
    # Begin rendering
    logging.info("Updating display")
    epd = epd7in5_V2.EPD()

    logging.info("initialising and clearing display")
    epd.init()
    epd.Clear()

    font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
    # font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    # font32 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 32)

    logging.info("Drawing new image on the horizontal plane...")

    # Create canvas
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images
    image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(image)

    # Construct images
    mapImageColor = Image.open('map-tile.jpg')
    mapImageGrayscale = mapImageColor.convert('L')
    enhancer = ImageEnhance.Contrast(mapImageGrayscale)
    mapImageGrayscaleBetterContrast = enhancer.enhance(1.5)
    mapImageGrayscaleResized = mapImageGrayscaleBetterContrast.resize(mapTileSize)
    mapImageDithered = mapImageGrayscaleResized.convert('1')

    # mapImageGrayscaleResized.save('map-tile-grayscale.jpg')
    # mapImageDithered.save('map-tile-dithered.jpg')

    # Draw stuff
    draw.text((10, 0), f"Latitude: {issLat}, Longitude: {issLon}", font=font12, fill=0)
    # draw.text((10, 100), lat, font=font12, fill=0)
    # draw.text((10, 200), lon, font=font12, fill=0)

    # bmp = Image.open(os.path.join(picdir, 'youtubeIcon.bmp'))
    # image.paste(bmp, (265, 80))
    # image.paste(mapImageGrayscaleResized, (0, 40))

    # Place map image in center
    mapImageX = int((epd.width - mapImageWidth) / 2)
    mapImageY = int((epd.height - mapImageHeight) / 2)
    image.paste(mapImageDithered, (mapImageX, mapImageY))

    # Render everything on screen
    epd.display(epd.getbuffer(image))

    # Clear screen (commented out so it can stay on)
    # logging.info("Putting display to sleep")
    
    # time.sleep(12) # Delay
    # epd.init()
    # epd.Clear()
    # epd.sleep()

    logging.info("Putting display on pause but keeping what's on screen")
    epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
