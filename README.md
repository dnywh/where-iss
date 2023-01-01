# Where ISS

Track the International Space Station's (ISS) orbit by printing what they see of Earth to an e-ink display.

Designed for Raspberry Pi and Waveshare e-Paper display HAT. Likely work on any display with a decent resolution after some minor tweaks.

## Prerequisites

Where ISS works great with [Pi Frame](https://github.com/dnywh/pi-frame), which includes Waveshare drivers and scheduling templates. Just fill out an _env.py_ file with your [Mapbox access token](https://docs.mapbox.com/help/getting-started/access-tokens/) as shown in [env.example.py](https://github.com/dnywh/where-iss/blob/main/env.example.py).

### Without Pi Frame

You'll need the [Waveshare e-Paper drivers](https://github.com/waveshare/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd) (or whatever display you're using) uploaded to your Raspberry Pi in a sibling _lib_ directory. Here's an example:

```
.
└── where-iss
└── lib
    └── waveshare_epd
        ├── __init__.py
        ├── epdconfig.py
        └── epd7in5_V2.py
```

## Usage

### Running on a schedule

See [Pi Frame](https://github.com/dnywh/pi-frame)!
