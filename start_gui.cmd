@echo off
REM Morse Trainer GUI Windows Startup Script
set MTLAME=lame.exe
set MTSPEAK=espeak.exe
python morse_gui.py %*
