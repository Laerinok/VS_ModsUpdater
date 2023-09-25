#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story v.1.1.3:
- Liste les mods installés et vérifie s'il existe une version plus récente et la télécharge
- Affiche le résumé
- Crée un fichier updates.log
- maj des mods pour une version donnée du jeu
- Verification de la présence d'une maj du script sur moddb
- Localisation OK
- Windows + Linux
"""
__author__ = "Laerinok"
__date__ = "2023-09-25"

import configparser
import datetime
import json
import locale
import os
import platform
import re
import shutil
import sys
import urllib.request
import urllib.error
import zipfile
import requests
import semver
import wget
from pathlib import Path
from bs4 import BeautifulSoup
from rich import print
from contextlib import redirect_stderr


class LanguageChoice:
    def __init__(self):
        self.num_version = '1.1.3'
        self.url_mods = 'https://mods.vintagestory.at/'
        self.path_lang = Path("lang")
        # On récupère la langue du système
        myos = platform.system()
        if myos == 'Windows':
            import ctypes
            windll = ctypes.windll.kernel32
            try:
                default_locale = locale.windows_locale[windll.GetUserDefaultLangID()]
                self.lang = f'{default_locale}.json'
            except KeyError:
                self.lang = 'en_US.json'
        else:
            self.loc = locale.getlocale()
            self.lang = f"{self.loc[0]}.json"
        # Def des path
        self.file_lang_path = Path(self.path_lang, self.lang)
        if not self.file_lang_path.is_file():
            self.file_lang_path = Path(self.path_lang, 'en_US.json')  # on charge en.json si aucun fichier de langue n'est présent
        # On charge le fichier de langue
        with open(self.file_lang_path, "r", encoding='utf-8-sig') as lang_json:
            desc = json.load(lang_json)
            self.setconfig = desc['setconfig']
            self.setconfig01 = desc['setconfig01']
            self.datapath = desc['datapath']
            self.title = desc['title']
            self.title2 = desc['title2']
            self.version_max = desc['version_max']
            self.author = desc['author']
            self.first_launch = desc['first_launch']
            self.first_launch2 = desc['first_launch2']
            self.first_launch3 = desc['first_launch3']
            self.err_list = desc['err_list']
            self.compver1 = desc['compver1']
            self.compver2 = desc['compver2']
            self.compver3 = desc['compver3']
            self.compver3a = desc['compver3a']
            self.compver4 = desc['compver4']
            self.summary1 = desc['summary1']
            self.summary2 = desc['summary2']
            self.summary3 = desc['summary3']
            self.summary4 = desc['summary4']
            self.summary5 = desc['summary5']
            self.summary6 = desc['summary6']
            self.summary7 = desc['summary7']
            self.error_modid = desc['error_modid']
            self.error = desc['error']
            self.last_update = desc['last_update']
            self.yes = desc['yes']
            self.no = desc['no']
            self.existing_update = desc['existing_update']
            self.exiting_script = desc['exiting_script']


class MajScript(LanguageChoice):
    def __init__(self):
        # Version du script pour affichage titre.
        super().__init__()

    def check_update_script(self):
        # Scrap pour recuperer la derniere version en ligne du script
        url_script = 'https://mods.vintagestory.at/modsupdater#tab-files'
        req_url_script = urllib.request.Request(url_script)
        try:
            urllib.request.urlopen(req_url_script)
            req_page_url = requests.get(url_script)
            page = req_page_url.content
            soup = BeautifulSoup(page, features="html.parser")
            soup_changelog = soup.find("div", {"class": "changelogtext"})
            soup_link_prg = soup.find("a", {"class": "downloadbutton"})
            # on recupere la version du chanlog
            regexp_ch_log_ver = '<strong>v(.*)</strong>'
            ch_log_ver = re.search(regexp_ch_log_ver, str(soup_changelog))
            # On compare les versions
            result = VSUpdate.compversion(self.num_version, ch_log_ver[1])
            if result == -1:
                print(f'[red]\n\t\t{self.existing_update}[/red]{self.url_mods.rstrip("/")}{soup_link_prg["href"]}\n')

        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(err_url.reason)
            with open('errors.log', 'a') as stderr_url, redirect_stderr(stderr_url):
                print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + str(err_lang), file=sys.stderr)


class VSUpdate(LanguageChoice):
    def __init__(self, pathmods):
        # ##### Version du script pour affichage titre.
        super().__init__()
        # #####
        # Définition des chemins
        self.config_file = Path('config.ini')
        self.path_temp = Path("temp")
        self.path_logs = Path("logs")
        self.path_mods = Path(pathmods)
        self.url_api = 'https://mods.vintagestory.at/api/mod/'
        # Creation des dossiers et fichiers
        if not self.path_temp.is_dir():
            os.mkdir('temp')
        # Ancien emplacement du chargement du fichier langue
        LanguageChoice()
        # On crée le fichier config.ini si inexistant, puis on sort du programme si on veut ajouter des mods à exclure
        if not self.config_file.is_file():
            self.set_config_ini()
            print(f'\t\t[bold cyan]{self.first_launch}[/bold cyan]')
            print(f'\t\t[bold cyan]{self.first_launch2}[/bold cyan]')
            maj_ok = input(f'\t\t{self.first_launch3} ({self.yes}/{self.no}) : ')
            if maj_ok == str(self.no).lower() or maj_ok == str(self.no[0]).lower():
                sys.exit()
        # On charge le fichier config.ini
        self.config_read = configparser.ConfigParser(allow_no_value=True)
        self.config_read.read(self.config_file, encoding='utf-8-sig')
        self.config_path = Path(self.config_read.get('ModPath', 'path'))
        self.path_mods = Path(self.config_path)
        # Définition des listes
        self.mod_filename = []
        self.mod_name_list = []
        self.mods_exclu = []
        self.non_mods_zipfile = []
        # Mods_list
        self.liste_mod_maj_filename = []
        # Définition des dico
        self.mods_updated = {}
        # Définition des variables
        self.modename = None
        self.nb_maj = 0
        self.gamever_max = self.config_read.get('Game_Version_max', 'version')  # On récupère la version max du jeu pour la maj
        # variables json_correction
        self.name_json = ''
        self.version_json = ''
        self.modid_json = ''
        self.regex_name_json = ''
        self.result_name_json = ''
        self.regex_version_json = ''
        self.result_version_json = ''
        self.regex_modid_json = ''
        self.result_modid_json = ''
        # variables extract_modinfo
        self.filepath = ''
        # Accueil
        self.version = ''
        # Update_mods
        self.Path_Changelog = ''
        # config_file
        self.exclusion_size = None

    def set_config_ini(self):
        # Création du config.ini si inexistant
        with open(self.config_file, "w", encoding="utf-8") as cfgfile:
            # Ajout du contenu
            config = configparser.ConfigParser(allow_no_value=True)
            config.add_section('ModPath')
            config.set('ModPath', 'path', str(self.path_mods))
            config.add_section('Game_Version_max')
            config.set('Game_Version_max', self.setconfig01)
            config.set('Game_Version_max', 'version', '100.0.0')
            config.add_section('Mod_Exclusion')
            config.set('Mod_Exclusion', self.setconfig)
            for i in range(1, 11):
                config.set('Mod_Exclusion', 'mod' + str(i), '')
            config.write(cfgfile)

    def json_correction(self, txt_json):
        self.regex_name_json = r'(\"name\": \")([\w*\s*]*)'
        self.result_name_json = re.search(self.regex_name_json, txt_json, flags=re.IGNORECASE)
        self.regex_version_json = r'(\"version\": \")([\d*.]*)'
        self.result_version_json = re.search(self.regex_version_json, txt_json, flags=re.IGNORECASE)
        self.regex_modid_json = r'(\"modid\": \")([\w*\s*]*)'
        self.result_modid_json = re.search(self.regex_modid_json, txt_json, flags=re.IGNORECASE)
        if self.result_name_json:
            self.name_json = self.result_name_json.group(2)
        if self.result_version_json:
            self.version_json = self.result_version_json.group(2)
        if self.result_modid_json:
            self.modid_json = self.result_modid_json.group(2)
        return self.name_json, self.version_json, self.modid_json

    def extract_modinfo(self, file):
        # On trie les fichiers .zip et .cs
        type_file = Path(file).suffix
        if type_file == '.zip':
            # On extrait le fichier modinfo.json de l'archive et on recupere le modid, name et version
            self.filepath = Path(self.path_mods, file)
            if zipfile.is_zipfile(self.filepath):  # Vérifie si fichier est un Zip valide
                archive = zipfile.ZipFile(self.filepath, 'r')
                try:
                    archive.extract('modinfo.json', self.path_temp)
                except KeyError:
                    # On crée une liste contenant les fichiers zip qui ne sont pas des mods.
                    self.non_mods_zipfile.append(file)
                zipfile.ZipFile.close(archive)
            json_file_path = Path(self.path_temp, "modinfo.json")
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
                    json_correct = self.json_correction(content_file)
                    mod_name = json_correct[0]
                    mod_version = json_correct[1]
                    mod_modid = json_correct[2]
        elif type_file == '.cs':
            self.filepath = Path(self.path_mods, file)
            with open(self.filepath, "r", encoding='utf-8-sig') as fichier_cs:
                cs_file = fichier_cs.read()
                regexp_name = '(namespace )(\w*)'
                result_name = re.search(regexp_name, cs_file, flags=re.IGNORECASE)
                regexp_version = '(Version\s=\s\")([\d.]*)\"'
                result_version = re.search(regexp_version, cs_file, flags=re.IGNORECASE)
                mod_name = result_name[2]
                mod_version = result_version[2]
                mod_modid = mod_name
        return mod_name, mod_modid, mod_version, self.filepath

    def liste_complete_mods(self):
        # On crée la liste contenant les noms des fichiers zip des mods
        for elem in self.path_mods.glob('*.zip'):
            mod_zipfile = zipfile.ZipFile(elem, 'r')
            with mod_zipfile:
                try:  # On ajoute uniquement les fichiers zip qui sont des mods
                    zipfile.ZipFile.getinfo(mod_zipfile, 'modinfo.json')
                    self.mod_filename.append(elem.name)
                except KeyError:
                    pass
        # On ajoute les fichiers .cs
        for elem_cs in self.path_mods.glob('*.cs'):
            self.mod_filename.append(elem_cs.name)
        if len(self.mod_filename) == 0:
            print(f"{self.err_list}")
            os.system("pause")
            sys.exit()
        return self.mod_filename

    @staticmethod
    def verif_formatversion(v1, v2):
        new_ver1 = []
        new_ver2 = []
        ver1 = v1.split('.')
        for elem in ver1:
            if len(elem) == 2 and elem[0] == str(0):
                new_ver1.append(elem[1:])
            else:
                new_ver1.append(elem)
        version1 = f'{new_ver1[0]}.{new_ver1[1]}.{new_ver1[2]}'

        ver2 = v2.split('.')
        for elem in ver2:
            if len(elem) == 2 and str(elem[0]) == str(0):
                new_ver2.append(elem[1:])
            else:
                new_ver2.append(elem)
        version2 = f'{new_ver2[0]}.{new_ver2[1]}.{new_ver2[2]}'
        return version1, version2

    @staticmethod
    def compversion(v1, v2):
        ver = VSUpdate.verif_formatversion(v1, v2)
        compver = semver.compare(ver[0], ver[1])
        return compver

    @staticmethod
    def get_max_version(versions):  # uniquement versions stables
        regexp_max_version = 'v([\d.]*)([\W\w]*)'
        max_version = re.search(regexp_max_version, max(versions))
        max_version = max_version[1]
        return max_version

    @staticmethod
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
                    try:
                        ch_log_txt = re.split(r'<br>|</br>|<br/>', ch_log_txt[0])
                    except IndexError:
                        ch_log_txt = ""
            log[ch_log_ver.group(1)] = ch_log_txt
            log['url'] = url
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(err_url.reason)
            with open('errors.log', 'a') as stderr_link, redirect_stderr(stderr_link):
                print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + str(err_lang), file=sys.stderr)
        return log

    def accueil(self, _net_version):  # le _ en debut permet de lever le message "Parameter 'net_version' value is not used
        if self.gamever_max == '100.0.0':
            self.version = self.version_max
        else:
            self.version = self.gamever_max
        # *** Texte d'accueil ***
        print(f'\n\n\t\t\t[bold cyan]{self.title} - v.{self.num_version} {self.author}[/bold cyan]')
        # On vérifie si une version plus récente du script est en ligne
        maj_script = MajScript()
        maj_script.check_update_script()
        print(f'\n\t\t\t\t\t\t[cyan]{self.title2}[bold] {self.version}[/bold][/cyan]\n')

    def mods_exclusion(self):
        # On crée la liste des mods à exclure de la maj
        for j in range(1, len(self.config_read.options('Mod_Exclusion')) + 1):
            try:
                modfile = self.config_read.get('Mod_Exclusion', 'mod' + str(j))
                if modfile != '':
                    self.mods_exclu.append(modfile)
                self.mods_exclu.sort()
            except configparser.NoSectionError:
                pass
            except configparser.InterpolationSyntaxError as err_parsing:
                print(f'Error in config.ini [Mod_Exclusion] mod{str(j)} : {err_parsing}')
                with open('errors.log', 'a') as stderr_parsing, redirect_stderr(stderr_parsing):
                    print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + 'Error in config.ini [Mod_Exclusion] - mod' + str(j) + ' : ' + str(err_parsing), file=sys.stderr)
                sys.exit()

    def mods_list(self):
        # Création de la liste des mods à mettre à jour
        # On retire les mods de la liste d'exclusion
        self.liste_mod_maj_filename = self.liste_complete_mods()
        for modexclu in self.mods_exclu:
            if modexclu in self.liste_mod_maj_filename:
                self.liste_mod_maj_filename.remove(modexclu)  # contient la liste des mods à mettre a jour avec les noms de fichier
        for elem in self.liste_mod_maj_filename:
            name = self.extract_modinfo(elem)
            self.mod_name_list.append(name[0])

    def update_mods(self):
        # Comparaison et maj des mods
        self.liste_mod_maj_filename.sort(key=lambda s: s.casefold())
        for mod_maj in self.liste_mod_maj_filename:
            modname_value = self.extract_modinfo(mod_maj)[0]
            version_value = self.extract_modinfo(mod_maj)[2]
            modid_value = self.extract_modinfo(mod_maj)[1]
            if modid_value == '':
                modid_value = re.sub(r'\s', '', modname_value).lower()
            filename_value = self.extract_modinfo(mod_maj)[3]
            mod_url_api = f'{self.url_api}{modid_value}'
            # On teste la validité du lien url
            req = urllib.request.Request(str(mod_url_api))
            try:
                urllib.request.urlopen(req)  # On teste l'existence du lien
                req_page = requests.get(str(mod_url_api))
                resp_dict = req_page.json()
                mod_asset_id = (resp_dict['mod']['assetid'])
                mod_last_version = (resp_dict['mod']['releases'][0]['modversion'])
                mod_file_onlinepath = (resp_dict['mod']['releases'][0]['mainfile'])
                # compare les versions des mods
                result_compversion = self.compversion(version_value, mod_last_version)
                print(f' [green]{modname_value[0].upper()}{modname_value[1:]}[/green]: {self.compver1}{version_value} - {self.compver2}{mod_last_version}')
                # On récupère les version du jeu nécessaire pour le mod
                mod_game_versions = resp_dict['mod']['releases'][0]['tags']
                mod_game_version_max = self.get_max_version(mod_game_versions)
                # On compare la version max souhaité à la version necessaire pour le mod
                result_game_version = self.compversion(mod_game_version_max, self.gamever_max)
                if result_game_version == 0 or result_game_version == -1:
                    #  #####
                    if result_compversion == -1:
                        dl_link = f'{self.url_mods}{mod_file_onlinepath}'
                        resp = requests.get(str(dl_link), stream=True)
                        file_size = int(resp.headers.get("Content-length"))
                        file_size_mo = round(file_size / (1024 ** 2), 2)
                        print(f'\t{self.compver3}{file_size_mo} {self.compver3a}')
                        print(f'\t[green] {modname_value} v.{mod_last_version}[/green] {self.compver4}')
                        os.remove(filename_value)
                        wget.download(dl_link, str(self.path_mods))
                        self.Path_Changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
                        log_txt = self.get_changelog(self.Path_Changelog)  # On récupère le changelog
                        self.mods_updated[modname_value] = log_txt
                        print('\n')
                        self.nb_maj += 1
            except urllib.error.URLError as er:
                # Affiche de l'erreur si le lien n'est pas valide
                print(er.reason)
                with open('errors.log', 'a') as stderr_link, redirect_stderr(stderr_link):
                    print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + str(err_lang), file=sys.stderr)
            except KeyError:
                print(f'[green] {modname_value}[/green]: [red]{self.error} !!! {self.error_modid}[/red]')

    def resume(self, netversion):
        # Résumé de la maj
        if self.nb_maj > 1:
            print(f'  [yellow]{self.summary1}[/yellow] \n')
            print(f'{self.summary2}')
            log_filename = f'updates_{datetime.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not self.path_logs.is_dir():
                os.mkdir('logs')
            log_path = Path(self.path_logs, log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(f'\n\t\t\tMods Vintage Story {netversion} - {self.last_update} : {datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                for key, value in self.mods_updated.items():
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

        elif self.nb_maj == 1:
            print(f'  [yellow]{self.summary3}[/yellow] \n')
            print(f'{self.summary4}')
            log_filename = f'updates_{datetime.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not self.path_logs.is_dir():
                os.mkdir('logs')
            log_path = Path(self.path_logs, log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(f'\n\t\t\tMods Vintage Story {netversion} - {self.last_update} : {datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                for key, value in self.mods_updated.items():
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
            print(f'  [yellow]{self.summary5}[/yellow]\n')

        if len(self.mods_exclu) == 1:
            modinfo_values = self.extract_modinfo(self.mods_exclu[0])
            print(f'\n {self.summary6}\n - [red]{modinfo_values[0]} [italic](v.{modinfo_values[2]})[italic][/red]')
        if len(self.mods_exclu) > 1:
            print(f'\n {self.summary7}')
            for k in range(0, len(self.mods_exclu)):
                # On appelle la fonction pour extraire modinfo.json
                modinfo_values = self.extract_modinfo(self.mods_exclu[k])
                print(f' - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')


# Efface le fichier errors.log si présent
if Path('errors.log').is_file():
    os.remove('errors.log')

# Test si il existe un fichier langue. (english par defaut)
try:
    lang = LanguageChoice()
except OSError | KeyError as err_lang:
    print(err_lang, file=sys.stderr)
    with open('errors.log', 'a') as stderr, redirect_stderr(stderr):
        print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + str(err_lang), file=sys.stderr)
    sys.exit()


def datapath():
    new_path_data = input(f'{lang.datapath}')
    new_path_data = Path(new_path_data)
    return new_path_data


# On récupère le système d'exploitation
my_os = platform.system()

if my_os == 'Windows':
    # On cherche les versions installées de Vintage Story
    path_mods = Path(os.getenv('appdata'), 'VintagestoryData', 'Mods')
elif my_os == 'Linux':
    path_mods = Path(Path.home(), '.config', 'VintagestoryData', 'Mods')
else:
    path_mods = None


# Charge le chemin du dossier data de VS à partir du config.ini si il exsite
config_path = Path(Path.cwd(), 'config.ini')
if not Path(config_path).is_file():
    while not path_mods.is_dir():
        path_mods = datapath()
else:
    # On charge le fichier config.ini
    config_read = configparser.ConfigParser(allow_no_value=True)
    config_read.read('config.ini', encoding='utf-8-sig')
    config_path = config_read.get('ModPath', 'path')
    path_mods = Path(config_path)

if path_mods.is_dir():
    inst = VSUpdate(path_mods)
    inst.accueil('inst')
    inst.mods_exclusion()
    inst.mods_list()
    inst.update_mods()
    inst.resume('inst')

# On efface le dossier temp
if Path('temp').is_dir():
    shutil.rmtree('temp')
input(lang.exiting_script)
