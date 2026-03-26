#!/bin/bash
# Morse Trainer CLI Linux Startup Script
export MTLAME="/usr/bin/lame"
python3 text_to_morse_mp3.py "$@"
