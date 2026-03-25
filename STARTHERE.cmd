@echo off
setlocal
SET CMD_DP=%~dp0

rem ============== FFPlay ============================
set  MTFFPLAY=%CMD_DP%ffmpeg\ffplay.exe

rem ============== Lame Encoder ======================
set    MTLAME=%CMD_DP%lame\lame.exe

rem ============== eSpeak-NG =========================
set   MTESPEAK=%CMD_DP%espeak NG\espeak-ng.exe
set       PATH=%CMD_DP%espeak NG;%PATH%
set  MTREGFILE=%CMD_DP%regfile.reg
echo Windows Registry Editor Version 5.00     > "%MTREGFILE%"
echo [HKEY_LOCAL_MACHINE\SOFTWARE\eSpeak NG] >> "%MTREGFILE%"
echo "Path"="%CMD_DP:\=\\%eSpeak NG"         >> "%MTREGFILE%"
regedit /s "%MTREGFILE%"
if exist "%MTREGFILE%" DEL "%MTREGFILE%"

"%CMD_DP%python3\python.exe" "%CMD_DP%morse_gui.py"
endlocal