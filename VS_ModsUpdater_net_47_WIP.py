# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story v.1.0.4:
- Pour NET4 ET NET7
- Liste les mods installés et vérifie s'il existe une version plus récente et la télécharge
- Affiche le résumé
- Crée un fichier updates.log
- maj des mods pour une version donnée du jeu
- TO DO LIST :
    - Verification de la présence d'une maj du script sur moddb
"""
__author__ = "Laerinok"
__date__ = "2023-08-01"


import configparser
import datetime
import glob
import json
import locale
import os
import re
import shutil
import urllib.request
import urllib.error
import zipfile
import requests
import wget
from bs4 import BeautifulSoup
from rich import print


class VSUpdate:
    def __int__(self):
        pass


# ##### Version du script pour affichae titre et verif version en ligne.
num_version = '1.0.4'
# #####

# On cherche les versions installées de Vintage Story (Net4 et/ou NET7)
path_VS_net4 = os.path.join(os.getenv('appdata'), 'VintagestoryData')
path_VS_net7 = os.path.join(os.getenv('appdata'), 'VintagestoryDataNet7')
if os.path.isdir(path_VS_net4):
    print(f'Vintage Story NET4 est installé')
    # On lance l'instance pour net4
else:
    print(f'Vintage Story NET4 n\'est pas installé')
if os.path.isdir(path_VS_net7):
    print(f'Vintage Story NET7 est installé')
    # On lance l'instance pour net7
else:
    print(f'Vintage Story NET7 n\'est pas installé')


net4_vsdata_path = VSUpdate()
