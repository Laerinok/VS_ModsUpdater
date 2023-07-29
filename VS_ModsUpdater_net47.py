# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story v.1.0.3:
- Liste les mods installés et vérifie s'il existe une version plus récente et la télécharge
- Affiche le résumé
- Crée un fichier updates.log
- maj des mods pour une version donnée du jeu
- TO DO LIST :
    - Verification de la présence d'une maj du script sur moddb
"""
__author__ = "Laerinok"
__date__ = "2023-07-29"


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

# ##### Version du script pour affichae titre et verif version en ligne.
num_version = '1.0.3'
# #####

# Définition des chemins
PATH_MODS_NET4 = os.path.join(os.getenv('APPDATA'), 'VintagestoryData', 'Mods')
PATH_MODS_NET7 = os.path.join(os.getenv('APPDATA'), 'VintagestoryDataNet7', 'Mods')


class Net:
    def __init__(self):
        self.config_file = 'config.ini'
        self.path_temp = "temp"
        self.path_lang = "lang"
        self.url_api = 'https://mods.vintagestory.at/api/mod/'
        self.url_mods = 'https://mods.vintagestory.at/'

        # Creation des dossiers et fichiers
        if not os.path.isdir(self.path_temp):
            os.mkdir('temp')

    def set_config_ini(self):
        # Création du config.ini si inexistant
        with open(self.config_file, "w", encoding="utf-8") as cfgfile:
            # Ajout du contenu
            config = configparser.ConfigParser(allow_no_value=True)
            config.add_section('ModPath')
            config.set('ModPath', 'path_net4', PATH_MODS_NET4)
            config.set('ModPath', 'path_net7', PATH_MODS_NET7)
            config.add_section('Game_Version_max')
            config.set('Game_Version_max', setconfig01)
            config.set('Game_Version_max', 'version', '100')
            config.add_section('Mod_Exclusion')
            config.set('Mod_Exclusion', setconfig)
            for i in range(1, 11):
                config.set('Mod_Exclusion', 'mod' + str(i), '')
            config.write(cfgfile)

    # On récupère la langue du système
    lang = locale.getlocale()
    lang = str(lang[0])
    file_lang = f"{lang.split('_')[0]}.json"
    file_lang_path = os.path.join(self.path_lang, file_lang)
    if not os.path.isfile(file_lang_path):
        file_lang_path = os.path.join(self.path_lang, 'en.json')  # on charge en.json si aucun fichier de langue n'est présent

    # On charge le fichier de langue
    with open(file_lang_path, "r", encoding='utf-8-sig') as lang_json:
        desc = json.load(lang_json)
        setconfig = desc['setconfig']
        setconfig01 = desc['setconfig01']
        title = desc['title']
        title2 = desc['title2']
        first_launch = desc['first_launch']
        first_launch2 = desc['first_launch2']
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
        last_update = desc['last_update']

    # On charge le fichier config.ini
    config_read = configparser.ConfigParser(allow_no_value=True)
    config_read.read(self.config_file, encoding='utf-8-sig')

    # On crée le fichier config.ini si inexistant
    if not os.path.isfile(self.config_file):
        set_config_ini()
        print(f'\t\t[bold cyan]{first_launch}[/bold cyan]')
        print(f'\t\t[bold cyan]{first_launch2}[/bold cyan]')
        os.system("pause")
        exit()
    config_path = config_read.get('ModPath', 'path')
    PATH_MODS = config_path

    # Définition des listes
    mod_filename = []
    mods_exclu = []

    # Définition des dico
    mods_updated = {}

    # Définition des variables
    nb_maj = 0
    gamever_max = config_read.get('Game_Version_max', 'version')  # On récupère la version max du jeu pour la maj

    def json_correction(self, txt_json):
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

    def extract_modinfo(self, file):
        filepath = ''
        # On trie les fichiers .zip et .cs
        type_file = os.path.splitext(file)[1]
        if type_file == '.zip':
            # On extrait le fichier modinfo.json de l'archive et on recupere le modid, name et version
            filepath = os.path.join(PATH_MODS, file)
            if zipfile.is_zipfile(filepath):  # Vérifie si fichier est un Zip valide
                archive = zipfile.ZipFile(filepath, 'r')
                archive.extract('modinfo.json', self.path_temp)
                zipfile.ZipFile.close(archive)
            json_file_path = os.path.join(self.path_temp, "modinfo.json")
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
        elif type_file == '.cs':
            filepath = os.path.join(PATH_MODS, file)
            with open(filepath, "r", encoding='utf-8-sig') as fichier_cs:
                cs_file = fichier_cs.read()
                regexp_name = '(namespace )(\w*)'
                result_name = re.search(regexp_name, cs_file, flags=re.IGNORECASE)
                regexp_version = '(Version\s=\s\")([\d.]*)\"'
                result_version = re.search(regexp_version, cs_file, flags=re.IGNORECASE)
                mod_name = result_name[2]
                mod_version = result_version[2]
                mod_modid = mod_name
        return mod_name, mod_modid, mod_version, filepath


    def liste_complete_mods():
        # On crée la liste contenant les noms des fichiers zip
        regex_filename = ''
        regex_filename_cs = ''
        for elem in glob.glob(PATH_MODS + "\*.zip"):
            if PATH_MODS == PATH_MODS_NET4:
                regex_filename = r'.*\\Mods\\(.*)'
            elif PATH_MODS == PATH_MODS_NET7:
                regex_filename = r'.*\\(.*)'
            result_filename = re.search(regex_filename, elem, flags=re.IGNORECASE)
            mod_filename.append(result_filename.group(1))
        # On ajoute les fichiers .cs
        for elem_cs in glob.glob(PATH_MODS + "\*.cs"):
            if PATH_MODS == PATH_MODS_NET4:
                regex_filename_cs = r'.*\\Mods\\(.*)'
            elif PATH_MODS == PATH_MODS_NET7:
                regex_filename_cs = r'.*\\(.*)'
            result_filename_cs = re.search(regex_filename_cs, elem_cs, flags=re.IGNORECASE)
            mod_filename.append(result_filename_cs.group(1))
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
        # print(f'arr1:{arr1} - arr2:{arr2}')  # debug
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
        if n > m:
            for i in range(m, n):
                arr2.append(0)
        elif m > n:
            for i in range(n, m):
                arr1.append(0)

        # returns -1 if version 1 is bigger and 1 if version 2 is bigger and 0 if equal
        for i in range(len(arr1)):
            # print(f'arr1[i]:{type(arr1[i])} - arr2[i]:{type(arr2[i])}')  # debug
            if arr1[i] > arr2[i]:
                return -1
            elif arr2[i] > arr1[i]:
                return 1
        return 0


    def get_max_version(versions):  # uniquement versions stables
        # print(f'liste versions: {versions}')  # debug
        regexp_max_version = 'v([\d.]*)([\W\w]*)'
        max_version = re.search(regexp_max_version, max(versions))
        max_version = max_version[1]
        return max_version


    def get_changelog(url):
        # Scrap pour recuperer le changelog
        req_url = urllib.request.Request(url)
        log = {}
        try:
            urllib.request.urlopen(req_url)
            req_page_url = requests.get(url)
            page = req_page_url.content
            soup = BeautifulSoup(page, features="html.parser")
            soup_changelog = soup.find("div", {"class": "changelogtext"})
            # on recupere la version du chanlog
            regexp_ch_log_ver = '<strong>(.*)</strong>'
            ch_log_ver = re.search(regexp_ch_log_ver, str(soup_changelog))
            # on récupère le changelog
            regexp_ch_log_txt = '<li>(.*)</li>'
            ch_log_txt = re.findall(regexp_ch_log_txt, str(soup_changelog))
            if not ch_log_txt:
                regexp_ch_log_txt = '<p>\W\s(.*)</p>'
                ch_log_txt = re.findall(regexp_ch_log_txt, str(soup_changelog))
                if not ch_log_txt:
                    regexp_ch_log_txt = '<p>(.*)</p>'
                    ch_log_txt = re.findall(regexp_ch_log_txt, str(soup_changelog))
                    ch_log_txt = re.split(r'<br>|</br>|<br/>', ch_log_txt[0])
            log[ch_log_ver.group(1)] = ch_log_txt
            log['url'] = url
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(err_url.reason)
        return log


    # ######

    if gamever_max == str(100):
        version = 'Toute version'
    else:
        version = gamever_max
    # *** Texte d'accueil ***
    print(f'\n\n\t\t\t[bold cyan]{title} - {num_version}[/bold cyan]')
    print(f'\t\t\t\t\t\t[cyan]{title2}[bold]{version}[/bold][/cyan]')
    print('\n\t\t\t\t\thttps://mods.vintagestory.at/list/mod\n\n')

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
        if modid_value == '':
            modid_value = re.sub(r'\s', '', modname_value).lower()
        filename_value = extract_modinfo(mod_maj)[3]
        mod_self.url_api = os.path.join(self.url_api, modid_value)
        # On teste la validité du lien url
        req = urllib.request.Request(mod_self.url_api)
        try:
            urllib.request.urlopen(req)  # On teste l'existence du lien
            req_page = requests.get(mod_self.url_api)
            resp_dict = req_page.json()
            mod_assetID = (resp_dict['mod']['assetid'])
            mod_last_version = (resp_dict['mod']['releases'][0]['modversion'])
            mod_file_onlinepath = (resp_dict['mod']['releases'][0]['mainfile'])
            # compare les versions des mods
            result_compversion = compversion(version_value, mod_last_version)
            print(f' [green]{modname_value}[/green]: {compver1}{version_value} - {compver2}{mod_last_version}')
            # On récupère les version du jeu nécessaire pour le mod
            mod_game_versions = resp_dict['mod']['releases'][0]['tags']
            mod_game_version_max = get_max_version(mod_game_versions)
            # print(f'ver max: {mod_game_version_max}\n ver max jeu souhaitée {gamever_max}')  # debug
            # On compare la version max souhaité à la version necessaire pour le mod
            result_game_version = compversion(mod_game_version_max, gamever_max)
            if result_game_version == 0 or result_game_version == 1:
                # print('on peut mettre à jour')  # debug
                #  #####
                if result_compversion == 1:
                    dl_link = os.path.join(self.url_mods, mod_file_onlinepath)
                    resp = requests.get(dl_link, stream=True)
                    file_size = int(resp.headers.get("Content-length"))
                    file_size_mo = round(file_size / (1024 ** 2), 2)
                    print(f'\t{compver3}{file_size_mo} {compver3a}')
                    print(f'\t[green] {modname_value} v.{mod_last_version}[/green] {compver4}')
                    os.remove(filename_value)
                    wget.download(dl_link, PATH_MODS)
                    Path_Changelog = f'https://mods.vintagestory.at/show/mod/{mod_assetID}#tab-files'
                    log_txt = get_changelog(Path_Changelog)  # On récupère le changelog
                    mods_updated[modname_value] = log_txt
                    print('\n')
                    nb_maj += 1
        except urllib.error.URLError as e:
            # Affiche de l'erreur si le lien n'est pas valide
            print(e.reason)
        except KeyError as err:
            # print(err.args)  # pour debuggage
            print(f'[green] {modname_value}[/green]: [red]{Error} !!! {Error_modid}[/red]')

    # Résumé de la maj
    if nb_maj > 1:
        print(f'  [yellow]{summary1}[/yellow] \n')
        print(f'{summary2}')
        with open('updates.log', 'w', encoding='utf-8-sig') as logfile:
            logfile.write(f'\n\t\t\t{last_update} : {datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            for key, value in mods_updated.items():
                # print(f' - [green]{key} {value["url"]} :[/green]')  # affiche en plus l'url du mod
                print(f' - [green]{key} :[/green]')
                logfile.write(f'\n {key} ({value["url"]}) :\n')  # affiche en plus l'url du mod
                for log_version, log_txt in value.items():
                    if log_version != 'url':
                        print(f'\t[bold][yellow]Changelog {log_version} :[/yellow][/bold]')
                        logfile.write(f'\tChangelog {log_version} :\n')
                        for line in log_txt:
                            print(f'\t\t[yellow]* {line}[/yellow]')
                            logfile.write(f'\t\t* {line}\n')

    elif nb_maj == 1:
        print(f'  [yellow]{summary3}[/yellow] \n')
        print(f'{summary4}')
        with open('updates.log', 'w', encoding='utf-8-sig') as logfile:
            logfile.write(f'\n\t\t\t{last_update} : {datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            for key, value in mods_updated.items():
                # print(f' - [green]{key} {value["url"]} :[/green]')  # affiche en plus l'url du mod
                print(f' - [green]{key} :[/green]')
                logfile.write(f'\n {key} ({value["url"]}) :\n')  # affiche en plus l'url du mod
                for log_version, log_txt in value.items():
                    if log_version != 'url':
                        print(f'\t[bold][yellow]Changelog {log_version} :[/yellow][/bold]')
                        logfile.write(f'\tChangelog {log_version} :\n')
                        for line in log_txt:
                            print(f'\t\t[yellow]* {line}[/yellow]')
                            logfile.write(f'\t\t* {line}\n')

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
            print(f' - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')

# On efface le dossier temp
try:
    shutil.rmtree(self.path_temp)
except OSError as e:
    print(f"Error:{ e.strerror}")
os.system("pause")
