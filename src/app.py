# Imports
import sys
import os

assetdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets"
)
exportsdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "exports"
)
libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"
)
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging  # Write to console
from waveshare_epd import epd7in5_V2  # Waveshare display
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageEnhance,
    ImageOps,
)  # Image and graphics
import requests  # Needed to check the ISS location
import urllib.request  # Needed for saving the Mapbox image
import secrets  # Needed for Mapbox access token
import math  # Needed for converting lat and long
from datetime import datetime  # For appending a timestamp on file images
from random import randrange  # For random map zoom levels

# Settings
logging.basicConfig(level=logging.DEBUG)
# Required settings
mapboxAccessToken = secrets.MAPBOX_ACCESS_TOKEN
mapTileZoom = randrange(
    3, 10
)  # 2: whole continents, 4: recognisable contours, 8: ridges, 10: individual crops
mapImageContrast = randrange(1, 5)
mapImageWidth = 360  # My Waveshare EDP is 7.5", 800x480, and I want the map image to be a bit smaller
mapImageHeight = 360  # And I want the map image to be square since the tiles are square
mapTileSize = (mapImageWidth, mapImageHeight)
# Optional settings
imageXOffset = 0
imageYOffset = 12  # Nudge down to match placement in picture frame
# Useful as ISS spends a lot of time over oceans, which looks boring on e-Paper
pixelRangeMinimum = 128  # Anything lower than 128 is probably ocean. Images with even a smidge of land tend to be around 200+
# Enable/disable little info display at bottom of map (off by default)
mapDebug = False

# Functions
# Converts from latitude and longtitude to Slippy Map tilenames
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)  # Store x and y in tuple


try:
    # Kick things off
    timeStampNice = datetime.today().strftime("%Y-%m-%d %H:%M:%S UTC")
    logging.info(f"Kicking off at {timeStampNice}")

    # Get ISS latitude and longitude results
    issData = requests.get("http://api.open-notify.org/iss-now.json").json()
    issLat = float(issData["iss_position"]["latitude"])
    issLon = float(issData["iss_position"]["longitude"])
    # logging.info(f"ISS latitude: {issLat}, ISS longitude: {issLon}")

    # Use those ISS coordinates to find corresponding tilenames
    mapTileNameX = deg2num(issLat, issLon, mapTileZoom)[0]
    mapTileNameY = deg2num(issLat, issLon, mapTileZoom)[1]
    # Use all of that to prepare a Mapbox tile image URL
    mapTileUrl = f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}"
    # logging.info(f"Map tile image: {mapTileUrl}")

    # Download a copy of the map tile to render to screen. Store it locally
    # TODO: Save in assets folder instead? Combine with below saving of image anyway? Since the resolution is capped at 512x512 anyway
    urllib.request.urlretrieve(
        f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}",
        "map-tile.jpg",
    )

    # Make basic edits to image
    mapImageColor = Image.open("map-tile.jpg")
    mapImageGrayscale = mapImageColor.convert("L")

    # Check to see if image is interesting enough to print to e-Paper...
    extrema = mapImageGrayscale.getextrema()
    pixelRange = extrema[1] - extrema[0]
    histogram = mapImageGrayscale.histogram()

    # Quality control
    # Exit if pixel range is smaller than the minimum
    if pixelRange <= pixelRangeMinimum:
        logging.info(
            f"Pixel range of {pixelRange} probably makes for an uninteresting image. Exiting early and keeping what's already on the e-Paper screen."
        )
        exit()
    # else:
    #     logging.info(f"Pixel range of {pixelRange}. Let's print.")

    # Otherwise keep going...
    # Increase contrast on image
    enhancer = ImageEnhance.Contrast(mapImageGrayscale)
    mapImageGrayscaleBetterContrast = enhancer.enhance(
        mapImageContrast
    )  # 1 = no changes, 1.5 = modest, 2 = noticable
    # mapImageDithered = mapImageGrayscale.convert('1', dither=Image.NONE)
    invertedImage = ImageOps.invert(mapImageGrayscaleBetterContrast)
    # Resize image
    mapImageEndResult = invertedImage.resize(mapTileSize)

    # Save out image
    # TODO: Does this still happen even if it doesn't pass quality control? It shouldn't
    timeStampSlug = datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    shortImageUrl = f"map-tile-{timeStampSlug}.jpg"
    fullImageUrl = f"{exportsdir}/{shortImageUrl}"
    mapImageEndResult.save(fullImageUrl)  # Save the image to the appropriate folder
    # logging.info(f"Image saved to: {fullImageUrl}")

    # Log information to text file

    result = f"File:\t{shortImageUrl}\nPrinted at:\t{timeStampNice}\nCoordinates:\t{issLat}, {issLon}\nMap zoom:\t{mapTileZoom}\nTile name:\t{mapTileNameX}, {mapTileNameY}\nContrast:\t{mapImageContrast}\nPixel range:\t{pixelRange}\nTile image URL:\t{mapTileUrl}"

    with open(f"{exportsdir}/map-tile-{timeStampSlug}.txt", "w") as f:
        f.write(result)
    # Log same information to console
    logging.info(f"\n{result}")

    # Begin rendering
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    font12 = ImageFont.truetype(os.path.join(assetdir, "font.ttc"), 12)

    # Create image (I'm calling it canvas) on the landscape plane
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images
    canvas = Image.new("1", (epd.width, epd.height), 255)  # 255: clear the frame
    # Get a drawing context
    draw = ImageDraw.Draw(canvas)

    # Place map image in center of canvas
    mapImageX = int(imageXOffset + (epd.width - mapImageWidth) / 2)
    mapImageY = int(imageYOffset + (epd.height - mapImageHeight) / 2)
    canvas.paste(mapImageEndResult, (mapImageX, mapImageY))

    if mapDebug:
        # Draw debugging text inside a rectangle that's at the bottom of map image
        infoRectHeight = 96
        infoRectY = mapImageY + mapImageHeight - infoRectHeight
        draw.rectangle(
            (
                (mapImageX, infoRectY),
                (mapImageX + mapImageWidth, mapImageY + mapImageHeight),
            ),
            fill=0,  # Black
        )
        # Map tile zoom level
        infoTextX = 44
        infoTextY = 12
        draw.text(
            (mapImageX + infoTextX, infoRectY + infoTextY),
            f"Map Zoom: {mapTileZoom}",
            font=font12,
            fill=1,
        )
        # Coordinates
        draw.multiline_text(
            (mapImageX + infoTextX, infoRectY + infoTextY + 22),
            f"Latitude: {issLat}\nLongitude: {issLon}",
            font=font12,
            fill=1,
        )
        # Timestamp
        draw.multiline_text(
            (mapImageX + (mapImageWidth / 2), infoRectY + infoTextY),
            f"Printed at:\n{timeStampNice}",
            font=font12,
            fill=1,
        )

    # Render all of the above to the e-Paper
    epd.display(epd.getbuffer(canvas))

    # Put e-Paper on pause, keeping what's on screen
    epd.sleep()

    # See sleep.py for wiping the screen clean

except IOError as e:
    logging.info(e)

# Exit plan
except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
