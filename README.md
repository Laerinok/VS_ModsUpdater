# <p align="center">Vintage Story ModsUpdater</p>
### <p align="center">Easily update your favorite mods</p>
<br><br>

### Description :
This program checks if you have a **_net4_** or **_net7_** version (or both) of Vintage Story, then checks the mods folder and updates mods if needed. When finished, it creates a .txt file with the changelog of each mod updated.  
<br>
<br>
**What the script does in detail :**
* Checks if there is a new version of the program.
* Detects the language of your system and automatically loads the language file (for now only english and french) if presents in lang directory.
* Creates a "ModsUpdater" folder in the VintagestoryData\ModConfig (or VintagestoryDataNet7\ModConfig) and creates a config.ini file
* Browses the mods folder
* Extracts the modinfo.json from Zip-files of each mod into e "temp" folder (at the root of the program)
* Compares the version number shown in the modinfo.json and the online one and downloads the mods if the version is more recent.
* Deleted zip file of the old mod.
* Deletes the "temp" folder

**Basic use :**
* At the first run, the program creates the config file. Then it asks if you want to go on updating or if you want to exit.
* If you go on, or if you've already ran the program once, it will update all mods and show (and write) the changelog.

**Advanced use (via config.ini) :**
With the config.ini file you can :
* Change the mod path.
* Select the maximum version of the game you want to update your mods
* Exclude some mods of the update process. Usefull for mods for which you must choose a file per config, or if an updated mod doesn't work etc... Just add the name of the zip file (with the extension)
This is usefull if you have the net4 version of VS and the last version of a mod is for the net7 version of VS.
