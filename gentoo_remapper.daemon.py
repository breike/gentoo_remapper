#!/bin/env python3

from flask import Flask, jsonify, request

app = Flask(__name__)

config = {
    # making layered layout...
    'current_layer': 1,

    # key for switching to layers on pressing
    #layering_key = evdev.ecodes.KEY_SPACE
    'layering_key': 522,

    # also add ctrl mode for sequential hotkeys
    'ctrl_pressed': False,

    # also left alt mode...
    'alt_pressed': False,

    # Define an example dictionary describing the remaps.
    'REMAP_TABLE': {
        # Let's swap A and B...
        #
        #evdev.ecodes.KEY_TAB: {
        #    1: evdev.ecodes.KEY_ESC,
        #    2: evdev.ecodes.KEY_LEFTALT
        #},
  },
    'soloing_caps': False
}
# The names can be found with evtest or in evdev docs.

@app.route("/config", methods=['GET'])
def get_config():
    return (jsonify(config))

@app.route("/config", methods=['PATCH'])
def edit_config():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    global config

    config = request.get_json()

    return jsonify(config), 200

if __name__ == "__main__":
    app.run(debug=True, port=1337)
