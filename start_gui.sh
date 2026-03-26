#!/bin/bash
# Morse Trainer GUI Linux Startup Script
export MTLAME="/usr/bin/lame"
export MTSPEAK="/usr/bin/espeak"
python3 morse_gui.py "$@"
