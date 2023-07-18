# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story :
- Liste les mods installés et vérifie s'il existe une version plus récente et la télécharge
"""
__author__ = "Jay"
__date__ = "2023-07-16"


import configparser
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
from rich import print

# Définition des chemins
PATH_CONFIG = os.path.join(os.getenv('APPDATA'), 'VintagestoryData', 'ModConfig', 'ModsUpdate')
PATH_MODS_VANILLA = os.path.join(os.getenv('APPDATA'), 'VintagestoryData', 'Mods')
PATH_MODS_VSLAUNCHER = os.path.join(os.getenv('APPDATA'), 'VintageStoryModVault')
CONFIG_FILE = os.path.join(PATH_CONFIG, 'config.ini')
PATH_TEMP = "temp"
PATH_LANG = "lang"
URL_API = 'https://mods.vintagestory.at/api/mod/'
URL_MODS = 'https://mods.vintagestory.at/'

# Creation des dossiers et fichiers
if not os.path.isdir(PATH_TEMP):
    os.mkdir('temp')
if not os.path.isdir(PATH_CONFIG):
    os.mkdir(PATH_CONFIG)

# On charge le fichier config.ini
config_read = configparser.ConfigParser(allow_no_value=True)
config_read.read(CONFIG_FILE, encoding='utf-8-sig')

# On récupère la langue du système
lang = locale.getlocale()
lang = str(lang[0])
file_lang = f"{lang.split('_')[0]}.json"
file_lang_path = os.path.join(PATH_LANG, file_lang)
if not os.path.isfile(file_lang_path):
    file_lang_path = os.path.join(PATH_LANG, 'en.json')  # on charge en.json si aucun fichier de langue n'est présent

# On charge le fichier de langue
with open(file_lang_path, "r", encoding='utf-8-sig') as lang_json:
    desc = json.load(lang_json)
    setconfig = desc['setconfig']
    title = desc['title']
    err_list = desc['err_list']
    compver1 = desc['compver1']
    compver2 = desc['compver2']
    compver3 = desc['compver3']
    compver3a = desc['compver3a']
    compver4 = desc['compver4']
    summary1 = desc['summary1']
    summary2 = desc['summary2']
    summary3 = desc['summary3']
    summary4 = desc['summary4']
    summary5 = desc['summary5']
    summary6 = desc['summary6']
    summary7 = desc['summary7']
    Error_modid = desc['Error_modid']
    Error = desc['Error']

# Définition des listes
mod_filename = []
mods_exclu = []
mods_updated = []

# Définition des variables
nb_maj = 0


def set_config_ini():
    # Création du config.ini si inexistant
    with open(CONFIG_FILE, "w", encoding="utf-8") as cfgfile:
        # Ajout du contenu
        config = configparser.ConfigParser(allow_no_value=True)
        config.add_section('ModPath')
        config.set('ModPath', 'path', PATH_MODS_VANILLA)
        config.set('ModPath', ';path', PATH_MODS_VSLAUNCHER)
        config.add_section('Mod_Exclusion')
        config.set('Mod_Exclusion', setconfig)
        for i in range(1, 11):
            config.set('Mod_Exclusion', 'mod' + str(i), '')
        config.write(cfgfile)


def json_correction(txt_json):
    name_json = ''
    version_json = ''
    modid_json = ''
    regex_name_json = r'(\"name\": \")([\w*\s*]*)'
    result_name_json = re.search(regex_name_json, txt_json, flags=re.IGNORECASE)
    regex_version_json = r'(\"version\": \")([\d*.]*)'
    result_version_json = re.search(regex_version_json, txt_json, flags=re.IGNORECASE)
    regex_modid_json = r'(\"modid\": \")([\w*\s*]*)'
    result_modid_json = re.search(regex_modid_json, txt_json, flags=re.IGNORECASE)
    if result_name_json:
        name_json = result_name_json.group(2)
    if result_version_json:
        version_json = result_version_json.group(2)
    if result_modid_json:
        modid_json = result_modid_json.group(2)
    return name_json, version_json, modid_json


def extract_modinfo(file):
    # On extrait le fichier modinfo.json de l'archive et on recupere le modid, name et version
    zipfilepath = os.path.join(PATH_MODS, file)
    if zipfile.is_zipfile(zipfilepath):  # Vérifie si fichier est un Zip valide
        archive = zipfile.ZipFile(zipfilepath, 'r')
        archive.extract('modinfo.json', PATH_TEMP)
        zipfile.ZipFile.close(archive)
    json_file_path = os.path.join(PATH_TEMP, "modinfo.json")
    with open(json_file_path, "r", encoding='utf-8-sig') as fichier_json:  # place le contenu du fichier dans une variable pour le tester ensuite avec regex
        content_file = fichier_json.read()
    with open(json_file_path, "r", encoding='utf-8-sig') as fichier_json:
        try:
            des = json.load(fichier_json)
            regex_name = r'name'
            result_name = re.search(regex_name, content_file, flags=re.IGNORECASE)
            regex_modid = r'modid'
            result_modid = re.search(regex_modid, content_file, flags=re.IGNORECASE)
            regex_version = r'version'
            result_version = re.search(regex_version, content_file, flags=re.IGNORECASE)
            mod_name = des[result_name.group()]
            mod_modid = des[result_modid.group()]
            mod_version = des[result_version.group()]
        except Exception:
            json_correct = json_correction(content_file)
            mod_name = json_correct[0]
            mod_version = json_correct[1]
            mod_modid = json_correct[2]
    return mod_name, mod_modid, mod_version, zipfilepath


def liste_complete_mods():
    # On crée la liste contenant les noms des fichiers zip
    regex_filename = ''
    for elem in glob.glob(PATH_MODS + "\*.zip"):
        if PATH_MODS == PATH_MODS_VANILLA:
            regex_filename = r'.*\\Mods\\(.*)'
        elif PATH_MODS == PATH_MODS_VSLAUNCHER:
            regex_filename = r'.*\\(.*)'
        result_filename = re.search(regex_filename, elem, flags=re.IGNORECASE)
        mod_filename.append(result_filename.group(1))
    if len(mod_filename) == 0:
        print(f"{err_list}")
        os.system("pause")
        exit()
    return mod_filename


def compversion(v1, v2):
    # This will split both the versions by '.'
    arr1 = v1.split(".")
    arr2 = v2.split(".")
    n = len(arr1)
    m = len(arr2)
    try:
        # converts to integer from string
        arr1 = [int(i) for i in arr1]
        arr2 = [int(i) for i in arr2]
    except ValueError:
        regex_ver = '([\d*.]*)(\W[\S]*)'
        result_v1 = re.search(regex_ver, v1)
        result_v2 = re.search(regex_ver, v2)
        v1 = result_v1[0]
        v2 = result_v2[0]

        arr1 = v1.split(".")
        arr2 = v2.split(".")
        n = len(arr1)
        m = len(arr2)

    # compares which list is bigger and fills
    # smaller list with zero (for unequal delimiters)
    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    # returns -1 if version 1 is bigger and 1 if version 2 is bigger and 0 if equal
    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            return -1
        elif arr2[i] > arr1[i]:
            return 1
    return 0


# On crée le fichier config.ini si inexistant
if not os.path.isfile(CONFIG_FILE):
    set_config_ini()
config_path = config_read.get('ModPath', 'path')
PATH_MODS = config_path

# *** Texte d'accueil ***
print(f'\n\n\t\t\t[bold cyan]{title}[/bold cyan]')
print('\t\t\thttps://mods.vintagestory.at/list/mod\n\n')

# On crée la liste des mods à exclure de la maj
for j in range(1, 11):
    try:
        modfile = config_read.get('Mod_Exclusion', 'mod' + str(j))
        if modfile != '':
            mods_exclu.append(modfile)
    except configparser.NoSectionError:
        pass

# Création de la liste des mods à mettre à jour
# On retire les mods de la liste d'exclusion
liste_mod_maj = liste_complete_mods()
for modexclu in mods_exclu:
    if modexclu in liste_mod_maj:
        liste_mod_maj.remove(modexclu)

# Comparaison et maj des mods
for mod_maj in liste_mod_maj:
    modname_value = extract_modinfo(mod_maj)[0]
    version_value = extract_modinfo(mod_maj)[2]
    modid_value = extract_modinfo(mod_maj)[1]
    zipfilename_value = extract_modinfo(mod_maj)[3]
    mod_url_api = os.path.join(URL_API, modid_value)
    # On teste la validité du lien url
    req = urllib.request.Request(mod_url_api)
    try:
        urllib.request.urlopen(req)  # On teste l'existence du lien
        req_page = requests.get(mod_url_api)
        resp_dict = req_page.json()
        mod_last_version = (resp_dict['mod']['releases'][0]['modversion'])
        mod_file_onlinepath = (resp_dict['mod']['releases'][0]['mainfile'])
        # compare les versions
        result_compversion = compversion(version_value, mod_last_version)
        print(f'[green]{modname_value}[/green]: {compver1}{version_value} - {compver2}{mod_last_version}')
        if result_compversion == 1:
            dl_link = os.path.join(URL_MODS, mod_file_onlinepath)
            resp = requests.get(dl_link, stream=True)
            file_size = int(resp.headers.get("Content-length"))
            file_size_mo = round(file_size / (1024 ** 2), 2)
            print(f'\t{compver3}{file_size_mo} {compver3a}')
            print(f'\t[green]{modname_value} v.{mod_last_version}[/green] {compver4}')
            mods_updated.append(modname_value)
            os.remove(zipfilename_value)
            wget.download(dl_link, PATH_MODS)
            print('\n')
            nb_maj += 1
    except urllib.error.URLError as e:
        # Affiche de l'erreur si le lien n'est pas valide
        print(e.reason)
    except KeyError as err:
        # print(err.args)  # pour debuggage
        print(f'[red]{Error} !!! - {modname_value} - {Error_modid}[/red]')

# Résumé de la maj
if nb_maj > 1:
    print(f'  [yellow]{summary1}[/yellow] \n')
    print(f'{summary2}')
    for modup in mods_updated:
        print(f'- [green]{modup}[/green]')
elif nb_maj == 1:
    print(f'  [yellow]{summary3}[/yellow] \n')
    print(f'{summary4}')
    for modup in mods_updated:
        print(f'- [green]{modup}[/green]')
else:
    print(f'  [yellow]{summary5}[/yellow]\n')

if len(mods_exclu) == 1:
    modinfo_values = extract_modinfo(mods_exclu[0])
    print(f'{summary6}[yellow]{modinfo_values[0]} v.{modinfo_values[2]}[/yellow]')
if len(mods_exclu) > 1:
    print(f'{summary7}')
    for k in range(0, len(mods_exclu)):
        # On appelle la fonction pour extraire modinfo.json
        modinfo_values = extract_modinfo(mods_exclu[k])
        print(f'- [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')

# On efface le dossier temp
try:
    shutil.rmtree(PATH_TEMP)
except OSError as e:
    print(f"Error:{ e.strerror}")
os.system("pause")
