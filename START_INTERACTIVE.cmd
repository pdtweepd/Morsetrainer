@echo off
setlocal
SET CMD_DP=%~dp0

set MTRUNTIME=%CMD_DP%runtime

rem ============== Python ============================
set  MTPYTHON=%MTRUNTIME%\python\python.exe

rem ============== FFPlay ============================
set  MTFFPLAY=%MTRUNTIME%\ffplay\ffplay.exe

rem ============== Lame Encoder ======================
set    MTLAME=%MTRUNTIME%\lame\lame.exe

rem ============== eSpeak ============================
set   MTESPEAK=%MTRUNTIME%\espeak\espeak-ng.exe
set       PATH=%MTRUNTIME%\espeak;%PATH%

set  MTREGFILE=%CMD_DP%regfile.reg
echo Windows Registry Editor Version 5.00     > "%MTREGFILE%"
echo [HKEY_LOCAL_MACHINE\SOFTWARE\eSpeak NG] >> "%MTREGFILE%"
echo "Path"="%MTRUNTIME:\=\\%\\eSpeak"       >> "%MTREGFILE%"
regedit /s "%MTREGFILE%"
if exist "%MTREGFILE%" DEL "%MTREGFILE%"

rem "%MTPYTHON%" "%CMD_DP%morse_gui.py"

"%MTPYTHON%" "%CMD_DP%text_to_morse_mp3.py"

endlocal