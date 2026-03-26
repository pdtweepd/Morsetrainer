@echo off
REM Morse Trainer CLI Windows Startup Script
set MTLAME=lame.exe
python text_to_morse_mp3.py %*
