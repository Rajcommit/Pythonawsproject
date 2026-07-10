##Purpose: load/save state/sate.json, and do it automatically so a crash mid-write is not curroting any file we are working on . Covring partial faliures.abs

import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "..","state","state.json")

def load_state():
    with open(STATE_PATH, "r") as f:
        return json.load(f)

def save_state(state):
    tmp_path = STATE_PATH + ".tmp"  ## Creates a temporary file path like /home/raj/project/state/state.json.tmp
    with open(tmp_path, "w") as f:
         json.dump(state , f , indent=2)
    os.replace(tmp_path, STATE_PATH) ## is atomic on most system, it eith suceeds or does not wok at all
