# Imports
import sys
import os
import logging  # Write to console
import math  # For converting lat and long
from datetime import datetime  # For appending a timestamp on file images
from PIL import Image, ImageEnhance, ImageOps  # Image and graphics
import requests  # To check the ISS location and retrieving Mapbox image

# Prepare directories so they can be reached from anywhere
appDir = os.path.dirname(os.path.realpath(__file__))
assetsDir = os.path.join(appDir, "assets")
# Get required items from other root-level directories
parentDir = os.path.dirname(appDir)
libDir = os.path.join(parentDir, "lib")
if os.path.exists(libDir):
    sys.path.append(libDir)

# Change the below import to match your display's driver
from waveshare_epd import epd5in83_V2 as display

# Adjust your optical offsets from one place
# import layout
# See Pi Frame for usage:
# https://github.com/dnywh/pi-frame

import env  # For Mapbox access token

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Settings
mapboxAccessToken = env.MAPBOX_ACCESS_TOKEN
headers = {"User-Agent": "Where ISS", "From": "endless.paces-03@icloud.com"}

# Shared optical sizing and offsets with Pi Frame
# containerSize = layout.size
# offsetX = layout.offsetX
# offsetY = layout.offsetY
# Manual optical sizing and offsets
containerSize = 360
offsetX = 0
offsetY = 16

mapTileSize = (containerSize, containerSize)

# pixelRangeMinimum = 128  # Anything lower than 128 is probably ocean. Images with even a smidge of land tend to be around 200+
# Useful as ISS spends a lot of time over oceans of solid color
minForegroundPercentage = 18  # Anything lower than 18% is probably uninteresting
# Set zoom range
# 2: whole continents, 4: recognisable contours, 8: ridges, 10: clouds and rivers, 18 trees
maxZoomLevel = 10
minZoomLevel = 4
invertZoomLevel = 6  # At what zoom level to invert the colors
backgroundColor = "black"  # A starting background color to invert if necessary
contrast = 3  # 1 = no changes, 1.5 = modest, 2 = noticeable, 3 = extreme
exportImages = True  # Save both the input and output image in an exports folder
debug = False  # Uses known fixed coordinates instead of the ISS coordinates

# Functions
# Converts from latitude and longitude to the Slippy Map tilenames Mapbox wants
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)  # Store x and y in tuple


# The main map printing function
def attemptMapPrint(mapTileZoom):
    if debug == True:
        # Use fixed coordinates
        lat = 37.8683
        lon = -98.417
    else:
        # Use the ISS coordinates which could be over ocean
        lat = issLat
        lon = issLon

    mapTileNameX = deg2num(lat, lon, mapTileZoom)[0]
    mapTileNameY = deg2num(lat, lon, mapTileZoom)[1]
    # Retrieve a Mapbox tile image
    mapTileUrl = f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}"
    logging.info(f"Tile URL: {mapTileUrl}")

    # Download a temporary copy of the map tile from the Mapbox API to render to screen
    r = requests.get(mapTileUrl, headers=headers)
    # Store it locally
    mapImagePath = os.path.join(appDir, "map-tile.jpg")
    with open(mapImagePath, "wb") as f:
        f.write(r.content)

    # Prepare versions of image
    mapImageColor = Image.open(mapImagePath)
    mapImageGrayscale = mapImageColor.convert("L")
    # Including a dithered version to mimic e-Paper screen for subsequent histogram math
    mapImageDithered = mapImageColor.convert("1")
    # Include versions with increased contrast for testing
    mapImageGrayscaleSharp = ImageEnhance.Contrast(mapImageGrayscale).enhance(contrast)
    mapImageDitheredSharp = mapImageGrayscaleSharp.convert("1")
    # Throw away original map tile image since new versions have been made
    os.remove(mapImagePath)

    # Get information about image to see if it is interesting enough to print to e-Paper...
    extrema = mapImageGrayscaleSharp.getextrema()
    pixelRange = extrema[1] - extrema[0]
    histogram = mapImageDitheredSharp.histogram()
    backgroundPercentage = int(round(histogram[0] / (512 * 512), 2) * 100)
    foregroundPercentage = int(round(histogram[255] / (512 * 512), 2) * 100)
    logging.info(
        f"Foreground: {foregroundPercentage}%, Background: {backgroundPercentage}%. Pixel Range: {pixelRange}"
    )

    # Invert colors if ocean is visible so that ocean is white and land black
    if currentZoomLevel <= invertZoomLevel:
        mapImageInverted = ImageOps.invert(mapImageGrayscaleSharp)
        mapImageResult = mapImageInverted
        backgroundColor = "white"
    else:
        mapImageResult = mapImageGrayscaleSharp
        backgroundColor = "black"

    # Quality control
    # Check if histogram range is less than minimum
    if foregroundPercentage <= minForegroundPercentage:
        # Does not pass quality control
        # Return and try again
        logging.info(
            f"I think this might be an uninteresting image. Zooming out and trying again..."
        )
        return
    else:
        # Passed quality control
        logging.info(f"Looks good! Let's print.")
        # Continue

    # Log information
    output = f"Printed at:\t{timeStampNice}\nCoordinates:\t{lat}, {lon}\nMap zoom:\t{mapTileZoom}\nTile name:\t{mapTileNameX}, {mapTileNameY}\nContrast:\t{contrast}\nForeground:\t{foregroundPercentage}%\nBackground:\t{backgroundPercentage}%\nPixel range:\t{pixelRange}"
    # ...to console
    logging.info(f"\n{output}")

    # Save out
    if exportImages == True:
        # Prepare directory for saving image(s)
        exportsDir = os.path.join(appDir, "exports")
        timeStampSlugToMin = datetime.today().strftime("%Y-%m-%d-%H-%M")
        imageDir = os.path.join(exportsDir, timeStampSlugToMin)
        if not os.path.exists(exportsDir):
            os.makedirs(exportsDir)
        if not os.path.exists(imageDir):
            os.mkdir(imageDir)
        # Save image in its directory
        mapImageDitheredSharp.save(
            os.path.join(imageDir, f"{timeStampSlugToMin}-dithered.jpg")
        )
        # mapImageDitheredSharp.save(f"{imageDir}/{timeStampSlugToMin}-dithered.jpg")
        # Also save other variants for comparison
        mapImageColor.save(os.path.join(imageDir, f"{timeStampSlugToMin}-color.jpg"))
        # mapImageColor.save(f"{imageDir}/{timeStampSlugToMin}-color.jpg")
        # mapImageGrayscale.save(f"{imageDir}/{timeStampSlugToMin}-grayscale.jpg")
        # mapImageDitheredSharp.save(f"{imageDir}/{timeStampSlugToMin}-dithered-sharp.jpg")
        # mapImageGrayscaleSharp.save(f"{imageDir}/{timeStampSlugToMin}-grayscale-sharp.jpg")
        # Also save text output
        with open(os.path.join(imageDir, f"{timeStampSlugToMin}.txt"), "w") as f:
            f.write(output)

    # Resize final image
    mapImagePrinted = mapImageResult.resize(mapTileSize)

    # Start rendering
    epd = display.EPD()
    epd.init()
    epd.Clear()

    canvas = Image.new("1", (epd.width, epd.height), backgroundColor)

    # Calculate top-left starting position
    startX = int(offsetX + (epd.width - containerSize) / 2)
    startY = int(offsetY + (epd.height - containerSize) / 2)

    canvas.paste(mapImagePrinted, (startX, startY))

    # Render all of the above to the display
    epd.display(epd.getbuffer(canvas))

    # Put display on pause, keeping what's on screen
    epd.sleep()
    logging.info(f"Finishing printing. Enjoy.")

    # Exit application
    exit()


# Kick things off
try:
    timeStampNice = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Kicking off at {timeStampNice}")
    if debug == True:
        logging.info(
            "Debug mode is on. Using fixed coordinates instead of the ISS coordinates."
        )
    else:
        # Get ISS latitude and longitude results
        issData = requests.get(
            "http://api.open-notify.org/iss-now.json", headers=headers
        ).json()
        issLat = float(issData["iss_position"]["latitude"])
        issLon = float(issData["iss_position"]["longitude"])
        logging.info(f"ISS coordinates: {issLat}, {issLon}")

    # Start at max zoom level before zooming out
    currentZoomLevel = maxZoomLevel
    # Decrement through map zoom levels until one is worth printing
    while True:
        logging.info(f"Map zoom: {currentZoomLevel}")
        # Unless the map zoom level has made all attempts within the range...
        # Map zoom level within range. Try to print
        attemptMapPrint(currentZoomLevel)
        # Didn't work? go down a zoom level for next time
        currentZoomLevel -= 1
        # Exit if map printed or couldn't produce desired contrast even at map zoom level 3
        if currentZoomLevel < minZoomLevel:
            logging.info(
                "I still couldn't get a good map image at these coordinates despite being fully zoomed out. Keeping what's already on screen."
            )
            break

except IOError as e:
    logging.info(e)

# Exit plan
except KeyboardInterrupt:
    logging.info("Exited.")
    display.epdconfig.module_exit()
    exit()
