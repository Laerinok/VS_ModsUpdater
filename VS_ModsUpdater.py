#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vintage Story mod management:
- Lists installed mods, checks for newer versions and downloads them
- Displays summary
- Creates an updates.log file
- You can limit the game version for mod updates
- Check for ModsUpdater updates on moddb
- Windows + Linux
- script execution by command line for servers.
- Possibility of generating a pdf file of the mod list
"""
__author__ = "Laerinok"
__date__ = "2023-03-29"
__version__ = "1.4.0"

import argparse
import configparser
import csv
import datetime as dt
import glob
import json
import os
import pathlib
import platform
import re
import shutil
import sys
import time
import traceback
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

import requests
import semver
import wget
from bs4 import BeautifulSoup
from fpdf import FPDF, YPos, XPos
from rich import print
from rich.prompt import Prompt


# On récupère le system
current_os = platform.system()

mods_path = None
config_file_path = None


# Mods path that is the default for system
def get_default_mods_path():
    # On vérifie si le chemin contient des variables d'environnement
    # On vérifie si la variable %appdata% (ou HOME) est dans le chemin et on la remplace par la variable systeme.
    if current_os == 'Windows':
        # On cherche les versions installées de Vintage Story
        return Path(os.getenv('appdata'), 'VintagestoryData', 'Mods')
    elif current_os == 'Linux':
        return Path(Path.home(), '.config', 'VintagestoryData', 'Mods')
    return None


# On récupère l'argument modspath
def get_mods_path():
    global mods_path

    system_mods_path = get_default_mods_path()

    if mods_path is not None and Path(mods_path).is_dir():
        return Path(mods_path)
    elif system_mods_path is not None and system_mods_path.is_dir():
        return system_mods_path
    return None


def get_config_path():
    # On cherche les versions installées de Vintage Story
    if current_os == 'Windows':
        config_path = Path(os.getenv('appdata'), 'VS_ModsUpdater')
    elif current_os == 'Linux':
        config_path = Path(Path.home(), '.config', 'VS_ModsUpdater')
    else:
        config_path = None

    if config_path is None:
        raise Exception('OS not supported')
    if not config_path.is_dir():
        os.mkdir(config_path)
    return config_path


def get_configfile_path():
    global config_file_path

    if config_file_path.is_file() and os.stat(config_file_path).st_size == 0:
        os.remove(config_file_path)
    return config_file_path


def get_logs_path():
    log_path = Path(get_config_path(), 'logs')
    if not log_path.is_dir():
        os.mkdir(log_path)
    return Path(log_path)


def get_temp_path():
    temp_path = Path(get_config_path(), 'temp')
    if not temp_path.is_dir():
        os.mkdir(temp_path)
    return Path(temp_path)


def get_lang_path():
    return Path(Path.cwd(), 'lang')


# Creation of a logfile
def write_log(info_crash):
    print('An error occured. Please see the debug-log file in logs folder for more information.')
    log_path = get_logs_path().joinpath(f'debug-log-{dt.datetime.today().strftime("%Y%m%d%H%M%S")}.txt')
    with open(log_path, 'a', encoding='UTF-8') as crashlog_file:
        crashlog_file.write(f'{dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")} : {info_crash}\n')


class LanguageChoice:
    def __init__(self):
        self.url_mods = 'https://mods.vintagestory.at/'
        # Si on définit manuellement la langue via le fichier config
        self.config_read = configparser.ConfigParser(allow_no_value=True, interpolation=None)
        self.config_read.read(get_configfile_path(), encoding='utf-8-sig')
        # On vérifie si args.language existe
        if args.language:
            self.lang = f'{args.language}.json'
        # Sinon on récupère la langue via config.ini
        else:
            try:
                self.config_lang = self.config_read.get('Language', 'language')
                self.lang = f'{self.config_lang}.json'
            # On charge le fichier en_US.json
            except (configparser.NoOptionError, configparser.NoSectionError):
                self.lang = 'en_US.json'
        self.file_lang_path = Path(get_lang_path(), self.lang)

        if not self.file_lang_path.is_file():
            self.file_lang_path = Path(get_lang_path(), 'en_US.json')  # on charge en.json si aucun fichier de langue n'est présent
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
            self.first_launch_title = desc['first_launch_title']
            self.first_launch_lang_choice = desc['first_launch_lang_choice']
            self.first_launch_config_done = desc['first_launch_config_done']
            self.first_launch_pathmods = desc['first_launch_pathmods']
            self.first_launch_lang_txt = desc['first_launch_lang_txt']
            self.first_launch_game_ver_max = desc['first_launch_game_ver_max']
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
            self.language_comment = desc['language']
            self.makePDFTitle = desc['makePDFTitle']
            self.makepdf = desc['makePDF']
            self.addingmodsinprogress = desc['addingmodsinprogress']
            self.makingpdfended = desc['makingpdfended']
            self.pdfTitle = desc['pdfTitle']
            self.ErrorCreationPDF = desc['ErrorCreationPDF']
            self.end_of_prg = desc['end_of_prg']
            self.error_msg = desc['error_msg']

        # On crée une liste pour les réponses O/N
        self.list_yesno = [self.yes.lower(), self.no.lower(), self.yes[0].lower(), self.no[0].lower()]
        # Dico pour les langues - Region, langue-abr, langue, index
        self.dic_lang = {
            "DE": ["de", "Deutsch", '1'],
            "US": ["en", "English", '2'],
            "ES": ["es", "Español", '3'],
            "FR": ["fr", "Français", '4'],
            "IT": ["it", "Italiano", '5'],
            "BR": ["pt", "Português", '6'],
            "RU": ["ru", "Русский", '7'],
            "UA": ["uk", "Українська", '8']
        }


class MajScript:
    def __init__(self):
        # Version du script pour affichage titre.
        super().__init__()
        # system

    def check_update_script(self):
        # Scrap pour recuperer la derniere version en ligne du script
        if current_os == "Windows":
            url_script = 'https://mods.vintagestory.at/modsupdater#tab-files'
        elif current_os == 'Linux':
            url_script = 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
        else:
            url_script = ''
        req_url_script = urllib.request.Request(url_script)

        try:
            urllib.request.urlopen(req_url_script)
            req_page_url = requests.get(url_script, timeout=2)
            page = req_page_url.content
            soup = BeautifulSoup(page, features="html.parser")
            soup_changelog = soup.find("div", {"class": "changelogtext"})
            soup_link_prg = soup.find("a", {"class": "downloadbutton"})
            # on recupere la version du chanlog
            regexp_online_ver_modsupdater = '<strong>v(.*)</strong>'
            online_ver_modsupdater = re.search(regexp_online_ver_modsupdater, str(soup_changelog))
            # On compare les versions
            result = VSUpdate.compversion_local(__version__, online_ver_modsupdater[1])
            if result == -1:
                column, row = os.get_terminal_size()
                maj_txt = f'[red]{LanguageChoice().existing_update}[/red]{LanguageChoice().url_mods.rstrip("/")}{soup_link_prg["href"]}'
                lines_update = maj_txt.splitlines()
                for line in lines_update:
                    print(f'{line.center(column)}')
        except requests.exceptions.ReadTimeout:
            write_log('ReadTimeout error: Server did not respond within the specified timeout.')
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(f'[red]{LanguageChoice().error_msg}[/red]')
            msg_error = f'{err_url.reason} : {url_script}'
            write_log(msg_error)


class VSUpdate:
    def __init__(self):
        # ##### Version du script pour affichage titre.
        super().__init__()
        # #####
        # Définition des chemins
        self.url_api = 'https://mods.vintagestory.at/api/mod/'
        self.crashlog_path = get_logs_path().joinpath('crash-log.txt')
        self.lang_name = ''
        # On crée le fichier config.ini si inexistant, puis (si lancement du script via l'executable et non en ligne de commande) on sort du programme si on veut ajouter des mods à exclure
        if not get_configfile_path().is_file():
            if args.nopause == 'false':
                print(f'\n\t\t[bold cyan]{LanguageChoice().first_launch_title}[/bold cyan]\n')
                i = 1
                for lan_2L, item in LanguageChoice().dic_lang.items():
                    print(f'\t\t - {i}) {item[1]}, {item[0]}')
                    i += 1
                lang_choice_result = Prompt.ask(f'\n\t\t[bold cyan]{LanguageChoice().first_launch_lang_choice}[/bold cyan]', choices=[str(i) for i in range(1, 9)], show_choices=False, default='2')
                for region, lang_ext in LanguageChoice().dic_lang.items():
                    if lang_choice_result == lang_ext[2]:
                        self.file_lang_path = Path(get_lang_path(), f'{lang_ext[0]}_{region}.json')
                        self.lang_name = lang_ext[1]
            elif args.language:
                self.file_lang_path = Path(get_lang_path(), f'{args.language}.json')
                for region, lang_ext in LanguageChoice().dic_lang.items():
                    # On récupere le nom de la langue
                    if region == args.language.split('_')[1]:
                        self.lang_name = lang_ext[1]
            else:
                self.file_lang_path = Path(get_lang_path(), 'en_US.json')
                self.lang_name = 'English'

            # On crée le fichier config.ini
            self.set_config_ini()
            # On récupère les valeurs de config.ini
            self.config_read = configparser.ConfigParser(allow_no_value=True, interpolation=None)
            self.config_read.read(get_configfile_path(), encoding='utf-8-sig')
            self.force_update = self.config_read.get('ModsUpdater', 'force_update')  # On récupère la valeur de force_update
            self.disable_mod_dev = self.config_read.get('ModsUpdater', 'disable_mod_dev')  # On récupère l'option pour la maj ou non des version dev des mod.
            print(f'\n\t[bold cyan]{LanguageChoice().first_launch_config_done}[/bold cyan] :')
            print(f'\t\t- [bold cyan]{LanguageChoice().first_launch_lang_txt}[/bold cyan] : {self.lang_name}')
            print(f'\t\t- [bold cyan]{LanguageChoice().first_launch_pathmods} : {get_mods_path()}[/bold cyan]')
            print(f'\t\t- [bold cyan]{LanguageChoice().first_launch_game_ver_max}[/bold cyan]')
            print(f'\t\t- [bold cyan]force_Update : {self.force_update}[/bold cyan]')
            print(f'\t\t- [bold cyan]disable_mod_dev : {self.disable_mod_dev}[/bold cyan]')
            # On demande de continuer ou on quitte
            if args.nopause == 'false':
                print(f'\n\t[bold cyan]{LanguageChoice().first_launch2}[/bold cyan]')
                maj_ok = Prompt.ask(f'\n\t{LanguageChoice().first_launch3}', choices=[LanguageChoice().list_yesno[0], LanguageChoice().list_yesno[1], LanguageChoice().list_yesno[2], LanguageChoice().list_yesno[3]])
                if maj_ok == LanguageChoice().list_yesno[1] or maj_ok == LanguageChoice().list_yesno[3]:
                    print(f'{lang.end_of_prg} ')
                    if get_temp_path().is_dir():
                        shutil.rmtree(get_temp_path())
                    time.sleep(2)
                    sys.exit()

        # On charge le fichier config.ini
        self.config_read = configparser.ConfigParser(allow_no_value=True, interpolation=None)
        self.config_read.read(get_configfile_path(), encoding='utf-8-sig')
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
        self.gamever_limit = self.config_read.get('Game_Version_max', 'version')  # On récupère la version max du jeu pour la maj
        if args.forceupdate:  # On récupère la valeur de force_update
            self.force_update = args.forceupdate
        else:
            self.force_update = self.config_read.get('ModsUpdater', 'force_update')
        if args.disable_mod_dev:
            self.disable_mod_dev = args.disable_mod_dev
        else:
            self.disable_mod_dev = self.config_read.get('ModsUpdater', 'disable_mod_dev')
        self.modinfo_content = None
        self.version_locale = ''
        self.mod_last_version_online = ''
        self.user_language = ''
        # variables json_correction
        self.name_json = ''
        self.version_json = ''
        self.modid_json = ''
        self.moddesc_json = ''
        self.regex_name_json = ''
        self.result_name_json = ''
        self.regex_version_json = ''
        self.result_version_json = ''
        self.regex_modid_json = ''
        self.result_modid_json = ''
        self.regex_moddesc_json = ''
        self.result_moddesc_json = ''
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
        # Ajout du contenu
        config = configparser.ConfigParser(allow_no_value=True, interpolation=None)
        mu_ver = __version__
        config.add_section('ModsUpdater')
        config.set('ModsUpdater', '# Info about the creation of the config.ini file')
        config.set('ModsUpdater', 'ver', mu_ver)
        config.set('ModsUpdater', '# Enable or disable Force_Update for every mods. If enabled, it will download the last version for ALL mods, even if the version is already the latest. (true/false default=false)')
        config.set('ModsUpdater', 'force_update', 'false')
        config.set('ModsUpdater', '# Allow to disable or enable update of mod in dev or prerelease (true/false default=false).')
        config.set('ModsUpdater', 'disable_mod_dev', 'false')
        config.add_section('ModPath')
        config.set('ModPath', 'path', str(get_mods_path()))
        config.add_section('Language')
        config.set('Language', str(LanguageChoice().language_comment))
        #  Si l'argument lang a été transmis
        if args.language:
            config.set('Language', 'language', args.language)  # from command line
        else:
            regex_lang = r"\/[a-z]{1,2}_[A-Z]{1,2}\.json$"
            result_lang = re.search(regex_lang, str(self.file_lang_path))
            config.set('Language', 'language', result_lang[1])
        config.add_section('Game_Version_max')
        config.set('Game_Version_max', LanguageChoice().setconfig01)
        config.set('Game_Version_max', 'version', '100.0.0')
        config.add_section('Mod_Exclusion')
        config.set('Mod_Exclusion', LanguageChoice().setconfig)
        if args.exclusion:
            for i in range(0, len(args.exclusion)):
                config.set('Mod_Exclusion', 'mod' + str(i + 1), args.exclusion[i])
        else:
            for i in range(1, 11):
                config.set('Mod_Exclusion', 'mod' + str(i), '')
        with open(get_configfile_path(), 'w', encoding="utf-8") as cfgfile:
            config.write(cfgfile)

    def json_correction(self, txt_json):
        self.regex_name_json = r'"{0,1}name"{0,1} {0,}: {0,}"(.*)",{0,}'
        self.result_name_json = re.search(self.regex_name_json, txt_json, flags=re.IGNORECASE)
        self.regex_version_json = r'"{0,1}version"{0,1} {0,}: {0,}"(.*)",{0,}'
        self.result_version_json = re.search(self.regex_version_json, txt_json, flags=re.IGNORECASE)
        self.regex_modid_json = r'"{0,1}modid"{0,1} {0,}: {0,}"(.*)",{0,}'
        self.result_modid_json = re.search(self.regex_modid_json, txt_json, flags=re.IGNORECASE)
        self.regex_moddesc_json = r'"{0,1}description"{0,1} {0,}: {0,}"(.*)",{0,}'
        self.result_moddesc_json = re.search(self.regex_moddesc_json, txt_json, flags=re.IGNORECASE)
        if self.result_name_json:
            self.name_json = self.result_name_json.group(2)
        if self.result_version_json:
            self.version_json = self.result_version_json.group(2)
        if self.result_modid_json:
            self.modid_json = self.result_modid_json.group(2)
        if self.result_moddesc_json:
            self.moddesc_json = self.result_moddesc_json.group(2)
        print(f'self.name_json:{self.name_json}\nself.version_json:{self.version_json}\nself.modid_json:{self.modid_json}\nself.moddesc_json:{self.moddesc_json}')
        return self.name_json, self.version_json, self.modid_json, self.moddesc_json

    def extract_modinfo(self, file):
        # On trie les fichiers .zip et .cs
        type_file = Path(file).suffix
        if type_file == '.zip':
            # On lit le fichier modinfo.json de l'archive et on recupere le modid, name et version
            self.filepath = Path(get_mods_path(), file)
            if zipfile.is_zipfile(self.filepath):  # Vérifie si fichier est un Zip valide
                with zipfile.ZipFile(self.filepath) as fichier_zip:
                    with fichier_zip.open('modinfo.json') as modinfo_json:
                        self.modinfo_content = modinfo_json.read().decode('utf-8-sig')
            try:
                regex_name = r'"{0,1}name"{0,1} {0,}: {0,}"(.*)",{0,}'
                result_name = re.search(regex_name, self.modinfo_content, flags=re.IGNORECASE)
                regex_modid = r'"{0,1}modid"{0,1} {0,}: {0,}"(.*)",{0,}'
                result_modid = re.search(regex_modid, self.modinfo_content, flags=re.IGNORECASE)
                regex_version = r'"{0,1}version"{0,1} {0,}: {0,}"(.*)",{0,}'
                result_version = re.search(regex_version, self.modinfo_content, flags=re.IGNORECASE)
                regex_description = r'"{0,1}description"{0,1} {0,}: {0,}"(.*)",{0,}'
                result_description = re.search(regex_description, self.modinfo_content, flags=re.IGNORECASE)
                mod_name = result_name.group(1)
                if result_modid is not None:
                    mod_modid = result_modid.group(1)
                else:
                    mod_modid = mod_name.replace(" ", "").lower()
                mod_version = result_version.group(1)
                if result_description is not None:
                    mod_description = result_description.group(1)
                else:
                    mod_description = ''
            except Exception:
                try:
                    json_correct = self.json_correction(self.modinfo_content)
                    mod_name = json_correct[0]
                    mod_version = json_correct[1]
                    mod_modid = json_correct[2]
                    if json_correct[3] is not None:
                        mod_description = json_correct[3]
                    else:
                        mod_description = ''
                except Exception:
                    print(f'[red]{LanguageChoice().error_msg}[/red]')
                    msg_error = f'{file} :\n\n\t {traceback.format_exc()}'
                    write_log(msg_error)
                print(f'[red]{LanguageChoice().error_msg}[/red]')
                msg_error = f'{file} :\n\n\t {traceback.format_exc()}'
                write_log(msg_error)
        elif type_file == '.cs':
            self.filepath = Path(get_mods_path(), file)
            with open(self.filepath, "r", encoding='utf-8-sig') as fichier_cs:
                cs_file = fichier_cs.read()
                regexp_name = '(namespace )(\\w*)'
                result_name = re.search(regexp_name, cs_file, flags=re.IGNORECASE)
                regexp_version = '(Version\\s=\\s\")([\\d.]*)\"'
                result_version = re.search(regexp_version, cs_file, flags=re.IGNORECASE)
                regexp_description = 'Description = "(.*)",'
                result_description = re.search(regexp_description, cs_file, flags=re.IGNORECASE)
                mod_name = result_name[2]
                mod_version = result_version[2]
                mod_modid = mod_name
                mod_description = result_description[1]
        return mod_name, mod_modid, mod_version, mod_description, self.filepath

    def liste_complete_mods(self):
        # On crée la liste contenant les noms des fichiers zip des mods
        for elem in get_mods_path().glob('*.zip'):
            mod_zipfile = zipfile.ZipFile(elem, 'r')
            with mod_zipfile:
                try:  # On ajoute uniquement les fichiers zip qui sont des mods
                    zipfile.ZipFile.getinfo(mod_zipfile, 'modinfo.json')
                    self.mod_filename.append(elem.name)
                except KeyError:
                    pass
        # On ajoute les fichiers .cs
        for elem_cs in get_mods_path().glob('*.cs'):
            self.mod_filename.append(elem_cs.name)
        if len(self.mod_filename) == 0:
            print(f"{LanguageChoice().err_list}")
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
    # Pour comparer la version locale et online
    def compversion_local(ver_loc, ver_online):  # (version locale, version online)
        compver = ''
        try:
            compver = semver.compare(ver_loc, ver_online)
        except Exception:
            write_log(traceback.format_exc())
        return compver

    @staticmethod
    # Pour comparer avec la version minimal nécessaire du jeu
    def compversion_first_min_version(ver_locale, first_min_ver):
        compver = ''
        try:
            ver = VSUpdate.verif_formatversion(first_min_ver, ver_locale)
            compver = semver.compare(ver[0], ver[1])
        except Exception:
            write_log(traceback.format_exc())
        return compver

    @staticmethod
    def get_max_version(versions):  # uniquement versions stables
        regexp_max_version = 'v([\\d.]*)([\\W\\w]*)'
        max_version = re.search(regexp_max_version, max(versions))
        max_version = max_version[1]
        return max_version

    @staticmethod
    def get_changelog(url):
        # Scrap pour recuperer le changelog
        req_url = urllib.request.Request(url)
        log = {}
        lst_log_desc = []
        try:
            urllib.request.urlopen(req_url)
            req_page_url = requests.get(url, timeout=2)
            page = req_page_url.content
            soup = BeautifulSoup(page, features="html.parser")
            soup_full_changelog = soup.find("div", {"class": "changelogtext"})
            # version
            last_version = soup_full_changelog.find('strong').text
            # On regarde si formatage par <ul></ul>
            balise_ul = soup_full_changelog.find("li")
            if balise_ul is not None:
                lst_log_desc.append(balise_ul.text)
            else:
                # recherche des paragraphes, on remplace les balises <br>, </br>, <br/> par un saut de ligne \n
                regexp_br = r'</{0,1}br/{0,1}>'
                new_desc_log = re.sub(regexp_br, '\n', str(soup_full_changelog.p))
                # recherche des paragraphes, on remplace les balises </p> par un saut de ligne \n
                regexp_p = r'</{0,1}p>'
                new_desc_log_2 = re.sub(regexp_p, '\n', new_desc_log)
                # On supprime le tout premier \n
                regex_final_desc_log_01 = r'[\n]^'
                new_desc_log_3 = re.sub(regex_final_desc_log_01, '', new_desc_log_2)
                # On supprime le(s) dernier(s) \n en fin de chaine
                regex_final_desc_log = r'[\n]$'
                final_desc_log = re.sub(regex_final_desc_log, '', new_desc_log_3)
                # on separe la chaine au niveau de \n pour avoir un élément par ligne
                lst_log_desc = final_desc_log.split('\n')
                # On nettoie la liste
                for entry in lst_log_desc:
                    if entry == '':  # On supprime les entrées vide la liste
                        lst_log_desc.remove(entry)
                # On retire les caratceres spéciaux en début de ligne si il y en a
                for item in lst_log_desc:
                    index_item = lst_log_desc.index(item)
                    regex_carspe = r'^[\W*]*'
                    new_item = re.sub(regex_carspe, '', item)
                    lst_log_desc[int(index_item)] = new_item
            # #######
            log[last_version] = lst_log_desc
            log['url'] = url
        except requests.exceptions.ReadTimeout:
            write_log('ReadTimeout error: Server did not respond within the specified timeout.')
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(f'[red]{LanguageChoice().error_msg}[/red]')
            msg_error = f'{err_url.reason} : {url}'
            write_log(msg_error)
        return log

    def accueil(self):  # le _ en debut permet de lever le message "Parameter 'net_version' value is not used
        if self.gamever_limit == '100.0.0':
            self.version = LanguageChoice().version_max
        else:
            self.version = self.gamever_limit
        # *** Texte d'accueil ***
        column, row = os.get_terminal_size()
        txt_title01 = f'\n\n[bold cyan]{LanguageChoice().title} - v.{__version__} {LanguageChoice().author}[/bold cyan]'
        lines01 = txt_title01.splitlines()
        for line in lines01:
            print(line.center(column))
        # On vérifie si une version plus récente du script est en ligne
        maj_script = MajScript()
        maj_script.check_update_script()
        txt_title02 = f'\n[cyan]{LanguageChoice().title2} : [bold]{self.version}[/bold][/cyan]\n'
        lines02 = txt_title02.splitlines()
        for line in lines02:
            print(f'{line.center(column)}')
        print('\n')

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
                print(f'[red]{LanguageChoice().error_msg}[/red]')
                msg_error = f'Error in config.ini [Mod_Exclusion] - mod{str(j)} : {str(err_parsing)}'
                write_log(msg_error)
                sys.exit()

    def mods_list(self):
        # Création de la liste des mods à mettre à jour
        # On retire les mods de la liste d'exclusion
        self.liste_mod_maj_filename = self.liste_complete_mods()
        for modexclu in self.mods_exclu:
            if modexclu in self.liste_mod_maj_filename:
                self.liste_mod_maj_filename.remove(modexclu)  # contient la liste des mods à mettre a jour avec les noms de fichier
        for elem in self.liste_mod_maj_filename:
            name = self.extract_modinfo(elem)[0]
            self.mod_name_list.append(name[0])

    def update_mods(self):
        # Comparaison et maj des mods
        self.liste_mod_maj_filename.sort(key=lambda s: s.casefold())
        for mod_maj in self.liste_mod_maj_filename:
            modname_value = self.extract_modinfo(mod_maj)[0]
            self.version_locale = self.extract_modinfo(mod_maj)[2]
            modid_value = self.extract_modinfo(mod_maj)[1]
            if modid_value == '':
                modid_value = re.sub(r'\s', '', modname_value).lower()
            filename_value = self.extract_modinfo(mod_maj)[4]
            mod_url_api = f'{self.url_api}{modid_value}'
            # On teste la validité du lien url
            req = urllib.request.Request(str(mod_url_api))
            try:
                urllib.request.urlopen(req)  # On teste l'existence du lien
                req_page = requests.get(str(mod_url_api), timeout=2)
                resp_dict = req_page.json()
                mod_asset_id = (resp_dict['mod']['assetid'])
                self.mod_last_version_online = (resp_dict['mod']['releases'][0]['modversion'])
                mod_file_onlinepath = (resp_dict['mod']['releases'][0]['mainfile'])
                mod_prerelease_value = semver.Version.parse(self.mod_last_version_online)
                # compare les versions des mods
                print(f' [green]{modname_value[0].upper()}{modname_value[1:]}[/green]: {LanguageChoice().compver1} : {self.version_locale} - {LanguageChoice().compver2} : {self.mod_last_version_online}')
                if self.disable_mod_dev == 'false' or mod_prerelease_value.prerelease is None:
                    # On récupère les version du jeu nécessaire pour le mod (cad la version la plus basse necessaire)
                    mod_game_versions = resp_dict['mod']['releases'][0]['tags']
                    first_min_ver = None
                    for ver in mod_game_versions:
                        first_min_ver = ver.split('v', 1)[1]
                    result_compversion_local = self.compversion_local(self.version_locale, self.mod_last_version_online)  # (version locale, version online)
                    # On compare la version max souhaité à la version necessaire pour le mod
                    result_game_compare_version = self.compversion_first_min_version(self.gamever_limit, first_min_ver)  # (version locale, version online,)
                    if result_game_compare_version == -1 or result_game_compare_version == 0:  # On met à jour
                        if result_compversion_local == -1 or (result_compversion_local == 0 and self.force_update.lower() == 'true'):
                            dl_link = f'{LanguageChoice().url_mods}{mod_file_onlinepath}'
                            resp = requests.get(str(dl_link), stream=True, timeout=2)
                            file_size = int(resp.headers.get("Content-length"))
                            file_size_mo = round(file_size / (1024 ** 2), 2)
                            print(f'\t{LanguageChoice().compver3} : {file_size_mo} {LanguageChoice().compver3a}')
                            print(f'\t[green] {modname_value} v.{self.mod_last_version_online}[/green] {LanguageChoice().compver4}')
                            try:
                                os.remove(filename_value)
                            except PermissionError:
                                print(f'[red]{LanguageChoice().error_msg}[/red]')
                                msg_error = f'{filename_value} :\n\n\t {traceback.format_exc()}'
                                write_log(msg_error)
                                sys.exit()
                            wget.download(dl_link, str(get_mods_path()))  # debug
                            self.changelog_path = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
                            log_txt = self.get_changelog(self.changelog_path)  # On récupère le changelog
                            content_lst_mods_updated = [
                                self.version_locale,
                                self.mod_last_version_online,
                                log_txt
                            ]
                            self.mods_updated[modname_value] = content_lst_mods_updated
                            print('\n')
                            self.nb_maj += 1
            except requests.exceptions.ReadTimeout:
                write_log('ReadTimeout error: Server did not respond within the specified timeout.')
            except urllib.error.URLError as err_url:
                # Affiche de l'erreur si le lien n'est pas valide
                print(f'[red]{LanguageChoice().error_msg}[/red]')
                msg_error = f'{err_url.reason} : {modname_value}'
                write_log(msg_error)
            except Exception:
                msg = f'{modname_value}\n{traceback.format_exc()}'
                write_log(msg)

    def resume(self):
        # Résumé de la maj
        if self.nb_maj > 1:
            print(f'  [yellow]{LanguageChoice().summary1}[/yellow] \n')
            print(f'{LanguageChoice().summary2} :')
            log_filename = f'updates_{dt.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not get_logs_path().is_dir():
                os.mkdir('logs')
            log_path = Path(get_logs_path(), log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(f'\n\t\t\tMods Vintage Story - {LanguageChoice().last_update} : {dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                for modname, value in self.mods_updated.items():
                    local_version = value[0]
                    online_last_version = value[1]
                    print(f' * [green]{modname} :[/green]')
                    logfile.write(f'\n\n- {modname} : v{local_version} -> v{online_last_version} ({value[2]["url"]}) :\n')  # affiche en plus l'url du mod
                    for log_version, log_txt in value[2].items():
                        if log_version != 'url':
                            print(f'\t[bold][yellow]Changelog {log_version} :[/yellow][/bold]')
                            logfile.write(f'\tChangelog {log_version} :\n')
                            for line in log_txt:
                                print(f'\t\t[yellow]- {line}[/yellow]')
                                logfile.write(f'\t\t- {line}\n')

        elif self.nb_maj == 1:
            print(f'  [yellow]{LanguageChoice().summary3}[/yellow] \n')
            print(f'{LanguageChoice().summary4} :')
            log_filename = f'updates_{dt.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not get_logs_path().is_dir():
                os.mkdir(get_logs_path())
            log_path = Path(get_logs_path(), log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(
                    f'\n\t\t\tMods Vintage Story - {LanguageChoice().last_update} : {dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                for modname, value in self.mods_updated.items():
                    local_version = value[0]
                    online_last_version = value[1]
                    print(f' * [green]{modname} :[/green]')
                    logfile.write(f'\n\n- {modname} : v{local_version} -> v{online_last_version} ({value[2]["url"]}) :\n')  # affiche en plus l'url du mod
                    for log_version, log_txt in value[2].items():
                        if log_version != 'url':
                            print(f'\t[bold][yellow]Changelog {log_version} :[/yellow][/bold]')
                            logfile.write(f'\tChangelog {log_version} :\n')
                            for line in log_txt:
                                print(f'\t\t[yellow]- {line}[/yellow]')
                                logfile.write(f'\t\t- {line}\n')
        else:
            print(f'  [yellow]{LanguageChoice().summary5}[/yellow]\n')

        if len(self.mods_exclu) == 1:
            modinfo_values = self.extract_modinfo(self.mods_exclu[0])
            print(f'\n {LanguageChoice().summary6} :\n - [red]{modinfo_values[0]} [italic](v.{modinfo_values[2]})[italic][/red]')
        if len(self.mods_exclu) > 1:
            print(f'\n {LanguageChoice().summary7} :')
            for k in range(0, len(self.mods_exclu)):
                # On appelle la fonction pour extraire modinfo.json
                modinfo_values = self.extract_modinfo(self.mods_exclu[k])
                print(f' - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')


# Création du pdf.
class GetInfo:
    def __init__(self, mod_name, mod_id, mod_moddesc, mod_filepath):
        # path
        self.csvfile = Path(get_temp_path(), 'csvtemp.csv')
        self.filepath = mod_filepath
        self.path_png = Path(get_temp_path(), 'png')
        self.path_modicon = None
        self.path_url = 'https://mods.vintagestory.at/'
        self.api_url = 'https://mods.vintagestory.at/api/mod/'
        # dico
        self.modsinfo_dic = {}
        # list
        self.moddesc_lst = []
        # var
        self.mod_moddesc = mod_moddesc
        self.mod_name = mod_name
        self.mod_url = None
        self.mod_id = mod_id
        self.modinfo_content = None
        self.test_url_mod = ''

    def get_infos(self):
        # extraction modicon.png et renommage avec modid
        if zipfile.is_zipfile(self.filepath):
            archive = zipfile.ZipFile(self.filepath, 'r')
            try:
                archive.extract('modicon.png', self.path_png)
                png_name = f'{self.mod_id}.png'
                self.path_modicon = Path(self.path_png, png_name)
                try:
                    os.rename(Path(self.path_png, 'modicon.png'), self.path_modicon)
                except FileExistsError:
                    pass
            except KeyError:
                pass
            zipfile.ZipFile.close(archive)
        self.mod_url = self.get_url(self.mod_id)
        self.moddesc_lst.append(self.mod_moddesc)
        self.moddesc_lst.append(self.mod_url)
        self.moddesc_lst.append(self.path_modicon)
        self.modsinfo_dic[self.mod_name] = self.moddesc_lst
        # On crée le csv
        with open(self.csvfile, "a", encoding="UTF-8", newline='') as fichier:
            objet_csv = csv.writer(fichier)
            for items in self.modsinfo_dic:
                objet_csv.writerow([items, self.modsinfo_dic[items][0], self.modsinfo_dic[items][1], self.modsinfo_dic[items][2]])
        return self.modsinfo_dic

    def get_url(self, modid):
        url = os.path.join(self.api_url, modid)
        req = urllib.request.Request(url)
        try:
            urllib.request.urlopen(req)  # On teste l'existence du lien
            req_page = requests.get(url, timeout=2)
            resp_dict = req_page.json()
            mod_asset_id = str(resp_dict['mod']['assetid'])
            mod_urlalias = str(resp_dict['mod']['urlalias'])
            if mod_urlalias == 'None':
                self.test_url_mod = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}'
            else:
                self.test_url_mod = f'https://mods.vintagestory.at/{mod_urlalias}'
            return self.test_url_mod
        except requests.exceptions.ReadTimeout:
            write_log('ReadTimeout error: Server did not respond within the specified timeout.')
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(f'[red]{LanguageChoice().error_msg}[/red]')
            msg_error = f'{err_url.reason} : {self.test_url_mod}'
            write_log(msg_error)
        except KeyError:
            print(f'[red]{LanguageChoice().error_msg}[/red]')
            msg_error = traceback.format_exc()
            write_log(msg_error)
            sys.exit()


class MakePdf:
    def __init__(self):
        self.langchoice = LanguageChoice()
        # var temps
        self.current_dateTime = datetime.now()
        self.date_dl = self.current_dateTime.strftime("%Y-%m-%d %H:%M")
        self.year = self.current_dateTime.strftime("%Y")
        self.month = self.current_dateTime.strftime("%m")
        self.day = self.current_dateTime.strftime("%d")
        # path
        self.csvfile = Path(get_temp_path(), 'csvtemp.csv')

    def makepdf(self):
        try:
            # On crée le pdf
            monpdf = FPDF('P', 'mm', 'A4')
            monpdf.add_font('FreeSans', '', str(Path('font', 'FreeSans.ttf')))
            monpdf.add_font('FreeSansBold', '', str(Path('font', 'FreeSansBold.ttf')))
            margintop_page = 10
            monpdf.set_top_margin(margintop_page)
            monpdf.set_auto_page_break(True, margin=10)
            monpdf.set_page_background((200, 215, 150))
            monpdf.add_page(same=True)
            nom_fichier_pdf = Path(get_config_path(), f'VS_Mods_{self.year}_{self.month}_{self.day}.pdf')
            monpdf.oversized_images = "DOWNSCALE"
            monpdf.oversized_images_ratio = 5
            width_img = 180
            x = (210 - width_img) / 2
            monpdf.image('banner.png', x=x, y=5, w=width_img)
            # Titre
            monpdf.set_font("FreeSansBold", '', size=20)
            monpdf.set_text_color(0, 0, 0)  # Couleur RGB pour le titre
            monpdf.set_y(45)
            monpdf.cell(w=0, h=20, text=f'{self.langchoice.pdfTitle}', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=False)
            table_data = []
            # On remplit la liste table_data
            with open(self.csvfile, newline='') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                for ligne in reader:
                    table_data.append(ligne)
            with monpdf.table(first_row_as_headings=False,
                              line_height=5,
                              width=190,
                              col_widths=(5, 55, 130)) as table:
                for ligne in table_data:
                    # cellule 1 - icone
                    row = table.row()
                    row.cell(img=ligne[3], img_fill_width=True, link=ligne[2])
                    # cellule 2 - nom du mod
                    monpdf.set_font("FreeSansBold", '', size=7)
                    row.cell(ligne[0], link=ligne[2])
                    # cellule 3 - description
                    monpdf.set_font("FreeSans", '', size=7)
                    row.cell(ligne[1])
        except Exception:
            print(f'[red]{LanguageChoice().error_msg}[/red]')
            msg_error = traceback.format_exc()
            write_log(msg_error)
            sys.exit()

        try:
            monpdf.output(nom_fichier_pdf)
            print(f'\n\n\t\t[blue]{lang.makingpdfended}\n[/blue]')
        except PermissionError:
            print(f'[red]{lang.ErrorCreationPDF}[/red]')


if __name__ == "__main__":
    mods_path = get_default_mods_path()
    config_file_path = Path(get_config_path(), 'config.ini')

    # Définitions des arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--modspath", help='Path to the mods folder', required=False, type=pathlib.Path)
    argParser.add_argument("--configfile", help='Path to the config.ini', required=False, type=pathlib.Path, default=get_configfile_path())
    argParser.add_argument("--language", help='Set the language file (Default=en_US - see the lang directory).', required=False, default='en_US')
    argParser.add_argument("--nopause", help="Disable the pause at the end of the script (default=false).", choices=['false', 'true'], type=str.lower, required=False, default='false')
    argParser.add_argument("--exclusion", help="Write filenames of mods with extension (in quotes) you want to exclude (each mod separated by space).", nargs="+")
    argParser.add_argument("--forceupdate", help="Force ModsUpdater to download the latest versions for ALL the mods (default=false).", choices=['false', 'true'], type=str.lower, required=False, default='false')
    argParser.add_argument("--makepdf", help="Create,at the end of the Update, a PDF file of all mods in the mods folder (default=false).", choices=['false', 'true'], type=str.lower, required=False, default='false')
    argParser.add_argument("--disable_mod_dev", help="enable or disable the update of mods in dev or prerelease (true/false default=false)", choices=['false', 'true'], type=str.lower, required=False, default='false')
    args = argParser.parse_args()
    # Fin des arguments

    if get_config_path() is None:
        raise Exception('OS not supported')
    elif not get_config_path().is_dir():
        os.mkdir(get_config_path())

    if args.configfile:
        config_file_path = Path(args.configfile)

    # Test si il existe un fichier langue. (english par defaut)
    try:
        lang = LanguageChoice()
    except Exception:
        traceback_info = traceback.format_exc()
        write_log(traceback_info)
        sys.exit()

    if args.modspath and Path(args.modspath).is_dir():
        mods_path = Path(args.modspath)

    if not (args.modspath and Path(args.modspath).is_dir()) and get_configfile_path().is_file():
        # On charge le fichier config.ini si --modspath non donné
        config_read = configparser.ConfigParser(allow_no_value=True, interpolation=None)
        config_read.read('config.ini', encoding='utf-8-sig')
        mods_path = config_read.get('ModPath', 'path')

        # On récupère le dossier des mods par argument, sinon on definit par defaut

    inst = VSUpdate()

    if not Path(get_configfile_path()).is_file():
        print(get_configfile_path())
        raise OSError("Config file doesn't exist")

    if mods_path is None:
        raise Exception('No mods path defined')

    inst.accueil()
    inst.mods_exclusion()
    inst.mods_list()
    inst.update_mods()
    inst.resume()

    # Création du pdf (si argument nopause est false)
    if args.nopause == 'false' or args.makepdf == 'true':
        make_pdf = None
        if args.makepdf == 'false':
            while make_pdf not in {str(LanguageChoice().yes).lower(), str(LanguageChoice().yes[0]).lower(), str(LanguageChoice().no).lower(), str(LanguageChoice().no[0]).lower()}:
                make_pdf = Prompt.ask(f'{LanguageChoice().makepdf}', choices=[LanguageChoice().list_yesno[0], LanguageChoice().list_yesno[1], LanguageChoice().list_yesno[2], LanguageChoice().list_yesno[3]])
        else:
            make_pdf = str(LanguageChoice().yes).lower()

        if make_pdf == str(LanguageChoice().yes).lower() or make_pdf == str(LanguageChoice().yes[0]).lower():
            # Construction du titre
            asterisk = '*'
            nb_asterisk = len(LanguageChoice().makePDFTitle) + 4
            string_asterisk = asterisk * nb_asterisk
            print(f'\t[green]{string_asterisk}[/green]')
            print(f'\t[green]* {LanguageChoice().makePDFTitle} *[/green]')
            print(f'\t[green]{string_asterisk}[/green]')

            # uniquement pour avoir le nb de mods (plus rapide car juste listing)
            nb_mods = 0
            nb_mods_ok = 0
            print('\n')
            mod_files_path = Path(mods_path, '*.*')
            for mod in glob.glob(str(mod_files_path)):
                if os.path.splitext(mod)[1] == '.zip' or os.path.splitext(mod)[1] == '.cs':
                    nb_mods += 1

            for modfilepath in glob.glob(str(mod_files_path)):
                if os.path.splitext(modfilepath)[1] == '.zip' or os.path.splitext(modfilepath)[1] == '.cs':
                    nb_mods_ok += 1
                    info_content = inst.extract_modinfo(modfilepath)
                    GetInfo(info_content[0], info_content[1], info_content[3], info_content[4]).get_infos()
                    print(f'\t\t{LanguageChoice().addingmodsinprogress} {nb_mods_ok}/{nb_mods}', end="\r")
            pdf = MakePdf()
            pdf.makepdf()

            if args.makepdf == 'false':
                input(f'{LanguageChoice().exiting_script}')
        elif make_pdf == str(lang.no).lower() or make_pdf == str(LanguageChoice().no[0]).lower():
            print(f'{LanguageChoice().end_of_prg} ')
            time.sleep(2)

    # On efface le dossier temp
    if get_temp_path().is_dir():
        shutil.rmtree(get_temp_path())
