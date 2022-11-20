#!/bin/sh
# # sleep-launcher.sh
# navigate to home, then script directory, then execute, then back home

# Borrowed from Scott Kildall:
# https://www.instructables.com/Raspberry-Pi-Launch-Python-script-on-startup/
# ...via Michael Klements:
# https://www.the-diy-life.com/make-a-youtube-subscriber-counter-using-an-e-ink-display-and-a-raspberry-pi-zero-w/

cd /
cd home/pi/where-iss/where-iss/
sudo python3 sleep.py
cd /
