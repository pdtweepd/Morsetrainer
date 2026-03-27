#!/bin/bash
# Morse Trainer CLI Linux/macOS Startup Script

# Locate lame: prefer known paths (Python falls back to PATH if unset)
for p in /usr/bin/lame /usr/local/bin/lame /opt/homebrew/bin/lame; do
    if [ -x "$p" ]; then export MTLAME="$p"; break; fi
done

# Locate espeak/espeak-ng: prefer known paths (Python falls back to PATH if unset)
for p in /usr/bin/espeak-ng /usr/bin/espeak /usr/local/bin/espeak-ng /usr/local/bin/espeak /opt/homebrew/bin/espeak; do
    if [ -x "$p" ]; then export MTSPEAK="$p"; break; fi
done

cd "$(dirname "$0")"
python3 text_to_morse_mp3.py "$@"
