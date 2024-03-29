								Welcome to the Vintage Story ModsUpdater wiki
									Easily update your favorite mods


* Description :
This a third-party program. It means it is NOT a mod. You do not have to put it in the mods folder. 
All you have do to is :
    - extract the archive
    - run the program
    - wait while checking/updating
    - play once finished This program checks the "mods" folder and updates the mods if necessary. Once finished, if there has been an - update, it creates an updates_YYYYMMDD_HHMMSS.txt file in the "logs" folder. Before quitting the program, you can choose to - generate a pdf file listing ALL your mods in the 'Mods' folder.


* Installation / Update:
Installation:
- Save the VS_ModsUpdater.v.X.X.X.zip file to the location of your choice and extract the archive. The archive should contain these files: (see photo).

Update:
- To update, simply replace the old files with the new ones contained in the new version of the zip file. - In most cases, all you need to do is replace the VS_ModsUpdater.exe file.

* What the script does in detail
    - Checks for the presence of a new version of ModsUpdater.
    - Detection of the system language to load the correct language file (if present in the 'lang' folder).
    - Create configuration file.
    - Create temporary 'temp' folder.
    - List mods present in 'Mods' folder.
    - Compare the version of installed mods with the latest online version and download the latest version if necessary.
    - Creation of a log file ('logs' folder) to keep track of updated files.
    - Creation of a log file in the event of a crash.
    - Creation of a pdf file (optional).
    - Delete old mods file
    - Delete temporary 'temp' folder

* Basic usage
    - Launch VS_ModsUpdater.exe
    - On first run, the program creates a config.ini file and asks you whether you wish to continue or interrupt the program.
    - If you continue, the program will continue with the default settings: location of the 'Mods' folder by default and the language of your operating system (if detected and present in the 'lang' folder) or English.

* Advanced Operation (via config.ini)
The config.ini file lets you :
    - Change the path to the mods folder
    - Select a specific language
    - Specify the maximum game version for which you wish to update mods
    - Exclude mods from the update process

Config.ini file :
[DEFAULT]
# modsupdater v1.3.4
=> This for my information only

[ModPath]
path = C:\Users\UserName\AppData\Roaming\VintagestoryData\Mods
=> Here you can change the path of your mods folder

[Language]
# To change the default language, uncomment the line below and set the desired language ('lang' folder).
# language = fr_FR
=> By uncommenting this you can choose your language among those present in the lang folder.

[Game_Version_max]
# Select the maximum game version for which mods can update themselves (ex: 100.0.0, 1.19, 1.19.4). default: 100.0.0 (to have all versions)
version = 1.19.4
=> You can set here the maximal version you want to update your mods. Useful if you don't want update mods to the latest version of the game (mainly when RC are put online)

[Mod_Exclusion]
# To exclude a mod from the update, add the name (with extension) of the mod's zip file after = (ONE per line)
mod1 = modname.zip
mod2 = 
mod3 = 
mod4 = 
mod5 = 
mod6 = 
mod7 = 
mod8 = 
mod9 = 
mod10 =

=> The mod_exclusion section allows you to exlude an update for a mod. Usefull if a mod is the cause of a crash or if you don't want it updates.

* Additional information
    - You can use arguments to launch the program. cf the readme.txt file or add the -h argument when launching via the console or the shortcut (VS_ModsUpdater.exe -h)
    - If you want additional features, such as profile management, take a look at the Early Mod Toolkit (NET4 / NET7) or Vintage Launcher mods.

* Supported languages
    - english
    - french
    - russian by Vsatan
    - brazilian by Yskar
    - spanish by Sir-Ryu
    - german (DeepL)
    - italian (DeepL)
    - ukrainian (DeepL)

===============================================================
For server :
I added the possibility to run VS_ModsUpdater in command line with some arguments.

You can run the script with the following arguments:
	- For Python : VS_ModsUpdater.py [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]] [--forceupdate {false,true}] [--makepdf {false,true}]
	- For Windows : VS_ModsUpdater.exe [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]] [--forceupdate {false,true}] [--makepdf {false,true}]
	- For Linux : VS_ModsUpdater [-h] [--modspath MODSPATH] [--language LANGUAGE] [--nopause {false,true}] [--exclusion EXCLUSION [EXCLUSION ...]] [--forceupdate {false,true}] [--makepdf {false,true}]

options :
	-h, --help show this help message and exit
	--modspath MODSPATH Enter the mods directory (in quotes). Quotes are needed only if there is some space in the path-name.
	--language LANGUAGE Set the language file (as it is named in the lang directory, without extension) (default=en_US)
	--nopause {false,true} (default: false) Disable the pause at the end of the script. You NEED to set it to true if not the script prompts and wait your intervention. (default=false)
	--exclusion EXCLUSION [EXCLUSION ...] Write filenames of mods with extension (in quotes) you want to exclude (each mod separated by space). It's not really useful as you can set it later in the config.ini file.
	--forceupdate {false,true} (default: false) Force ModsUpdater to download the latest versions for ALL the mods, even if they are up to date. (default=false)
	--makepdf {false,true} (default: false) Create,at the end of the Update, a PDF file of all mods in the mods folder (default=false).

Exemple of use :
Linux : VS_ModsUpdater --language fr_FR --modspath "/home/VintagestoryData/mods" --nopause true
WINDOWS: Add the desired arguments in the target field of a shortcut e.g "Path\to\ModsUpdater\VS_ModsUpdater.exe" --language fr_FR --modspath "D:\Game\VS_DATA\mods" --nopause true --forceupdate true

I added a .bat file (Windows) and a .sh file (Linux) if needed. You only have to edit them and set the the right path for your configuration and yours desired arguments.