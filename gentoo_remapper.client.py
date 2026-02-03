#!/usr/bin/python3

# CC0, originally written by t184256.

# This is an example Python program for Linux that remaps a keyboard.
# The events (key presses releases and repeats), are captured with evdev,
# and then injected back with uinput.

# This approach should work in X, Wayland, anywhere!

# Also it is not limited to keyboards, may be adapted to any input devices.

# The program should be easily portable to other languages or extendable to
# run really any code in 'macros', e.g., fetching and typing current weather.

# The ones eager to do it in C can take a look at (overengineered) caps2esc:
# https://github.com/oblitum/caps2esc


# Import necessary libraries.
import atexit
import json
# You need to install evdev with a package manager or pip3.
import evdev  # (sudo pip3 install evdev)
import requests
import sys

def write_config(config):
    response = requests.patch("http://127.0.0.1:1337/config",
                    json=config)

    return response

def read_config():
    return requests.get("http://127.0.0.1:1337/config").json()

config = read_config()

# The keyboard name we will intercept the events for. Obtainable with evtest.
#MATCH = ['CyLei Dactyl_74_L', 'CyLei Dactyl_74_R']
MATCH = sys.argv[1]
# Find all input devices.
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
# Limit the list to those containing MATCH and pick the first one.
kbd = [d for d in devices if MATCH == d.name][0]
atexit.register(kbd.ungrab)  # Don't forget to ungrab the keyboard on exit!
kbd.grab()  # Grab, i.e. prevent the keyboard from emitting original events.

# Create a new keyboard mimicking the original one.
with evdev.UInput.from_device(kbd, name='kbdremap') as ui:
    for ev in kbd.read_loop():  # Read events from original keyboard.
        config = read_config()

        if ev.type == evdev.ecodes.EV_KEY:  # Process key events.
            if ev.code == evdev.ecodes.KEY_PAUSE and ev.value == 1:
                # Exit on pressing PAUSE.
                # Useful if that is your only keyboard. =)
                # Also if you bind that script to PAUSE, it'll be a toggle.
                break
            
            # selecting 2 layer if layering key pressed
            elif ev.code == config['layering_key'] and ev.value == 1:
                config['current_layer'] = 2
                write_config(config)
            # or selecting 1 on releasing
            elif ev.code == config['layering_key'] and ev.value == 0:
                config['current_layer'] = 1
                write_config(config)
            elif ev.code in config['REMAP_TABLE']:
                if config['ctrl_pressed'] and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, ev.value)
                    if ev.value == 0:
                        config['ctrl_pressed'] = False
                        write_config(config)
                if config['alt_pressed'] and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, ev.value)
                    if ev.value == 0:
                        config['alt_pressed'] = False
                        write_config(config)
                # Lookup the key we want to press/release instead...
                remapped_code = config['REMAP_TABLE'][config['current_layer']][ev.code]
                # And do it.
                if remapped_code == evdev.ecodes.KEY_LEFTCTRL:
                    config['ctrl_pressed'] = True
                    write_config(config)
                elif remapped_code == evdev.ecodes.KEY_LEFTALT:
                    config['alt_pressed'] = True
                    write_config(config)
                else:
                    ui.write(evdev.ecodes.EV_KEY, remapped_code, ev.value)
            elif ev.code == evdev.ecodes.KEY_LEFTCTRL:
                config['ctrl_pressed'] = True
                ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 1)
                write_config(config)
            elif ev.code == evdev.ecodes.KEY_LEFTALT:
                config['alt_pressed'] = True
                ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, 1)
                write_config(config)
            else:
                if config['ctrl_pressed'] and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, ev.value)
                if config['alt_pressed'] and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, ev.value)
                # Passthrough other key events unmodified.
                ui.write(evdev.ecodes.EV_KEY, ev.code, ev.value)

                if ev.value == 0:
                    if (config['alt_pressed'] or config['ctrl_pressed']) and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                        if config['alt_pressed']:
                            config['alt_pressed'] = False
                        if config['ctrl_pressed']:
                            config['ctrl_pressed'] = False
                        write_config(config)
            # If we just pressed (or held) CapsLock, remember it.
            # Other keys will reset this flag.
            config['soloing_caps'] = (ev.code == evdev.ecodes.KEY_CAPSLOCK and ev.value)
            write_config(config)
        else:
            # Passthrough other events unmodified (e.g. SYNs).
            ui.write(ev.type, ev.code, ev.value)
