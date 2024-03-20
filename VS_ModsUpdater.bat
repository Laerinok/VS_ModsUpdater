@echo off
CHCP 65001
cls


rem *************************************************************************************************
rem You can modify these variables to match your config.
rem VS_ModsUpdater directory path:
set VS_ModsUpdaterPath=E:\Jeux\Vintage Story\Modding\VS_ModsUpdater\_my releases\Windows\VS_ModsUpdater.v.1.3.0
rem Mods directory path:
set modspath=C:\Users\Jerome\AppData\Roaming\VintagestoryData\Mods
rem Language of the script. same name than the file in the 'lang'directory of VS_ModsUpdater
set language=fr_FR
rem enable or disable the force_update (true/false)
set force_update=true
rem ************************************************************************************************

start /B /wait /D "%VS_ModsUpdaterPath%" VS_ModsUpdater.exe --modspath "%modspath%" --language "%language%" --nopause true --force_update %force_update%
