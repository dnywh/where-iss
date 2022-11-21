import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


import logging
from waveshare_epd import epd7in5_V2 # Waveshare display stuff
# import time # Delays in seconds, not used, right? TODO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # Image stuff
# import traceback # TODO: Did removing this do anything? From Waveshare demo

import requests # Needed to check the ISS location
import secrets  # Needed for Mapbox access token
import math  # Needed for converting lat and long
import urllib.request # Needed for saving the Mapbox image
from datetime import datetime # For appending a timestamp on file images

# Imports for checking if ISS is over land or water
# https://github.com/toddkarin/global-land-mask
# from global_land_mask import globe
# import numpy as np

mapboxAccessToken = secrets.MAPBOX_ACCESS_TOKEN

logging.basicConfig(level=logging.DEBUG)

# Get API results

issData = requests.get("http://api.open-notify.org/iss-now.json").json()
issLat = float(issData['iss_position']['latitude'])
issLon = float(issData['iss_position']['longitude'])
# print(globe.is_land(issLat, issLon))
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
mapTileUrl = f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileNameZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}"

# EDP 7.5" = 800x480
mapImageWidth = 400
mapImageHeight = mapImageWidth
# Square
mapTileSize = (mapImageWidth, mapImageHeight)

try:
    timeStampNice = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Kicking off at {timeStampNice}: Latitude: {issLat}, Longitude: {issLon}")
    logging.info(f"Requesting map tile JPG from URL: {mapTileUrl}")
    # Save a copy of the map tile
    urllib.request.urlretrieve(f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileNameZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}", "map-tile.jpg")

    # Begin rendering
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
    # font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    # font32 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 32)

    # Create canvas on the horizontal plane
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images
    canvas = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    # Get a drawing context
    draw = ImageDraw.Draw(canvas)

    # Construct images
    mapImageColor = Image.open('map-tile.jpg')
    mapImageGrayscale = mapImageColor.convert('L')
    enhancer = ImageEnhance.Contrast(mapImageGrayscale)
    mapImageGrayscaleBetterContrast = enhancer.enhance(1.8) # 1 = default
    mapImageGrayscaleResized = mapImageGrayscaleBetterContrast.resize(mapTileSize)
    mapImageDithered = mapImageGrayscaleResized.convert('1')
    # Assign which of the above I want to have as the end result
    mapImageEndResult = mapImageGrayscaleResized.resize(mapTileSize)

    # Save out image
    timeStampSlug = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    fullImageUrl = f'{picdir}/map-tile-color-resized-{timeStampSlug}.jpg'
    mapImageEndResult.save(fullImageUrl) # Save the image to the appropriate folder
    logging.info(f"Image saved to: {fullImageUrl}")


    # Place map image in center
    mapImageX = int((epd.width - mapImageWidth) / 2)
    mapImageY = int((epd.height - mapImageHeight) / 2)
    canvas.paste(mapImageEndResult, (mapImageX, mapImageY))

    draw.multiline_text((40, 40), f"Latitude: {issLat}\nLongitude: {issLon}", font=font12, fill=0)
    

    # Render all of the above to the e-Paper
    epd.display(epd.getbuffer(canvas))


    # # Create canvas on the vertical plane (sideways)
    # # Using this to debug
    # canvasVertical = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    # draw = ImageDraw.Draw(canvasVertical)
    

    # # Render all of the above to the e-Paper
    # epd.display(epd.getbuffer(canvasVertical))




    # Clear screen (commented out so it can stay on)
    # logging.info("Putting display to sleep")
    # time.sleep(12) # Delay
    # epd.init()
    # epd.Clear()
    # epd.sleep()

    # Put e-Paper on pause, keeping what's on screen
    epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
