@echo off
rem Abre OpenReel permitiendo que importe archivos desde un servidor local (127.0.0.1)
set OPENREEL_ALLOW_LOCAL_FETCH=1
start "" "%LOCALAPPDATA%\Programs\@openreeldesktop\OpenReel.exe"
