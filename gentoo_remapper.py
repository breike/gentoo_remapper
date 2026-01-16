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
import sys

def write_config(config_path):
    global alt_pressed
    global current_layer
    global layering_key
    global ctrl_pressed

    with open(config_path, "w") as f:
        json.dump({
            "alt_pressed": alt_pressed,
            "current_layer": current_layer,
            "layering_key": layering_key,
            "ctrl_pressed": ctrl_pressed
        }, f)

def read_config(config_path):
    global alt_pressed
    global current_layer
    global layering_key
    global ctrl_pressed

    with open(config_path, "rb") as f:
        config = json.load(f)

        alt_pressed = config['alt_pressed']
        current_layer = config['current_layer']
        layering_key = config['layering_key']
        ctrl_pressed = config['ctrl_pressed']

json_config_path = "/tmp/gentoo_remapper.json"

# making layered layout...
current_layer = 1

# key for switching to layers on pressing
#layering_key = evdev.ecodes.KEY_SPACE
layering_key = 522

# also add ctrl mode for sequential hotkeys
ctrl_pressed = False

# also left alt mode...
alt_pressed = False

# Define an example dictionary describing the remaps.
REMAP_TABLE = {
    # Let's swap A and B...
    #
    #evdev.ecodes.KEY_TAB: {
    #    1: evdev.ecodes.KEY_ESC,
    #    2: evdev.ecodes.KEY_LEFTALT
    #},
}
# The names can be found with evtest or in evdev docs.


# The keyboard name we will intercept the events for. Obtainable with evtest.
#MATCH = ['CyLei Dactyl_74_L', 'CyLei Dactyl_74_R']
MATCH = sys.argv[1]
# Find all input devices.
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
# Limit the list to those containing MATCH and pick the first one.
kbd = [d for d in devices if MATCH == d.name][0]
atexit.register(kbd.ungrab)  # Don't forget to ungrab the keyboard on exit!
kbd.grab()  # Grab, i.e. prevent the keyboard from emitting original events.

soloing_caps = False  # A flag needed for CapsLock example later.

# Create a new keyboard mimicking the original one.
write_config(json_config_path)
with evdev.UInput.from_device(kbd, name='kbdremap') as ui:
    for ev in kbd.read_loop():  # Read events from original keyboard.
        read_config(json_config_path)

        if ev.type == evdev.ecodes.EV_KEY:  # Process key events.
            if ev.code == evdev.ecodes.KEY_PAUSE and ev.value == 1:
                # Exit on pressing PAUSE.
                # Useful if that is your only keyboard. =)
                # Also if you bind that script to PAUSE, it'll be a toggle.
                break
            
            # selecting 2 layer if layering key pressed
            elif ev.code == layering_key and ev.value == 1:
                current_layer = 2
            # or selecting 1 on releasing
            elif ev.code == layering_key and ev.value == 0:
                current_layer = 1
            elif ev.code in REMAP_TABLE:
                if ctrl_pressed and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, ev.value)
                    if ev.value == 0:
                        ctrl_pressed = False
                if alt_pressed and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, ev.value)
                    if ev.value == 0:
                        alt_pressed = False
                # Lookup the key we want to press/release instead...
                remapped_code = REMAP_TABLE[current_layer][ev.code]
                # And do it.
                if remapped_code == evdev.ecodes.KEY_LEFTCTRL:
                    ctrl_pressed = True
                elif remapped_code == evdev.ecodes.KEY_LEFTALT:
                    alt_pressed = True
                else:
                    ui.write(evdev.ecodes.EV_KEY, remapped_code, ev.value)
            elif ev.code == evdev.ecodes.KEY_LEFTCTRL:
                ctrl_pressed = True
                ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 1)
            elif ev.code == evdev.ecodes.KEY_LEFTALT:
                alt_pressed = True
                ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, 1)
            else:
                if ctrl_pressed and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, ev.value)
                    if ev.value == 0:
                        ctrl_pressed = False
                if alt_pressed and ev.code != evdev.ecodes.KEY_LEFTSHIFT and ev.code != evdev.ecodes.KEY_RIGHTSHIFT:
                    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, ev.value)
                    if ev.value == 0:
                        alt_pressed = False
                # Passthrough other key events unmodified.
                ui.write(evdev.ecodes.EV_KEY, ev.code, ev.value)
            # If we just pressed (or held) CapsLock, remember it.
            # Other keys will reset this flag.
            soloing_caps = (ev.code == evdev.ecodes.KEY_CAPSLOCK and ev.value)
            write_config(json_config_path)
        else:
            # Passthrough other events unmodified (e.g. SYNs).
            ui.write(ev.type, ev.code, ev.value)
