#!/usr/bin/python3
"""
lux-from-brightness.py - guess lux value based on a webcam image
================================================================
Copyright (C) 2023 Michael Hamilton

GNU License
===========

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/.
"""
import signal
import sys

import cv2


CAMERA_DEVICE = '/dev/video0'

# Find these out for you camera: run v4l2-ctl --device /dev/video0 --list-ctrls-menus
# specifically: v4l2-ctl --device /dev/video0 --get-ctrl auto_exposure
MANUAL_EXPOSURE_SETTING = 1
AUTO_EXPOSURE_SETTING = 3

# Customise to your desktop and webcam
# Logitech, Inc. Webcam C270 settings for my study
LUX_BRIGHTNESS = [
    ('SUNLIGHT',       100000, 140),
    ('DAYLIGHT',        10000, 120),
    ('OVERCAST',         1000, 110),
    ('SUNRISE_SUNSET',    400,  40),
    ('DARK_OVERCAST',     100,  20),
    ('LIVING_ROOM',        50,   5),
    ('NIGHT',               5,   0),
]


def main():
    """vdu_controls application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    camera = cv2.VideoCapture(CAMERA_DEVICE)
    auto_exposure = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
    exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
    print(f"INFO: existing values: auto-exposure={auto_exposure} exposure={exposure}", file=sys.stderr)
    try:
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, MANUAL_EXPOSURE_SETTING)
        camera.set(cv2.CAP_PROP_EXPOSURE, 64)
        new_auto_exposure = camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        new_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
        print(f"INFO: new values: auto-exposure={new_auto_exposure} exposure={new_exposure}", file=sys.stderr)

        result, image = camera.read()
        # cv2.imwrite("sample.png", image)  # uncomment to check the image exposure etc.
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("sample-gray.png", gray_image)

        brightness = cv2.mean(gray_image)[0]

        for name, lux, value in LUX_BRIGHTNESS:
            if brightness >= value:
                print(f"INFO lux={lux}, brightness={brightness}, name={name}", file=sys.stderr)
                print(lux)
                break
    finally:
        print(f"Restoring auto-exposure={auto_exposure} exposure={exposure}", file=sys.stderr)
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure)
        if auto_exposure != AUTO_EXPOSURE_SETTING:  # Can only set exposure if not on auto_exposure
            camera.set(cv2.CAP_PROP_EXPOSURE, exposure)
        camera.release()


if __name__ == '__main__':
    main()
