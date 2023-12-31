# <p align="center">Vintage Story ModsUpdater</p>
### <p align="center">Easily update your favorite mods</p>
<br><br>

### Description :
This program checks the mods folder and updates mods if needed. When finished, it creates a .txt file with the changelog of each mod updated.

**What the script does in detail :**
* Checks if there is a new version of the program.
* Detects the language of your system and automatically loads the language file (for now only english and french) if presents in lang directory. You can now set it manually
* Creates a config.ini file
* Browses the mods folder
* Extracts the modinfo.json from Zip-files of each mod into e "temp" folder (at the root of the program)
* Compares the version number shown in the modinfo.json and the online one and downloads the mods if the version is more recent.
* Creates à log file for mods updated
* Deleted zip file of the old mod.
* Deletes the "temp" folder

**Basic use :**
* At the first run, the program creates the config file. Then it asks if you want to go on updating or if you want to exit.
* If you go on, or if you've already run the program once, it will update all mods and show (and write) the changelog.

**Advanced use (via config.ini) :**  
With the config.ini file you can :
* Change the mod path.
* Change the language
* Select the version of the game you want to update your mods
* Exclude some mods of the update process. Usefull for mods for which you must choose a file per config, or if an updated mod doesn't work etc... Just add the name of the zip file (with the extension)

**For server :**  
I added the possibility to run VS_ModsUpdater in command line with some arguments.  

You can run the script with the following arguments:  
*For Python :*
VS_ModsUpdater.py [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]]  
*For Windows :*
VS_ModsUpdater.exe [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]]  
*For Linux :*
VS_ModsUpdater [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]]  

*options :*  
- -h, --help show this help message and exit  
- --modspath MODSPATH Enter the mods directory (in quotes). Quotes are needed only if there is some space in the path-name.
- --language LANGUAGE Set the language file (as it is named in the lang directory, without extension)
- --nopause {false,true} Disable the pause at the end of the script. You NEED to set it to true if not the script prompts and wait your intervention.
- --exclusion EXCLUSION [EXCLUSION ...] Write filenames of mods with extension (in quotes) you want to exclude (each mod separated by space). It's not really useful as you can set it later in the config.ini file.

Exemple of use :  
*Linux :* VS_ModsUpdater --language en_US --modspath "/home/VintagestoryData/mods" --nopause true  

I added  a .bat file (Windows) and a .sh file (Linux) if needed. You only have to edit them and set the the right path for your configuration.