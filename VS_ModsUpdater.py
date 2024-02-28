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
__date__ = "2023-02-28"
__version__ = "1.3.3"

import argparse
import configparser
import csv
import datetime as dt
import glob
import json
import locale
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
from contextlib import redirect_stderr
from datetime import datetime
from pathlib import Path

import requests
import semver
import wget
from bs4 import BeautifulSoup
from fpdf import FPDF, YPos, XPos
from rich import print
from rich.prompt import Prompt


# Creation of a logfile
def write_log(info_crash):
    if not Path('logs').is_dir():
        os.mkdir('logs')
    log_path = Path('logs').joinpath(f'crash-log-{dt.datetime.today().strftime("%Y%m%d%H%M%S")}.txt')
    with open(log_path, 'a', encoding='UTF-8') as crashlog_file:
        crashlog_file.write(f'{dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")} : {info_crash}\n')


class LanguageChoice:
    def __init__(self):
        self.num_version = __version__
        self.url_mods = 'https://mods.vintagestory.at/'
        self.path_lang = Path("lang")
        # Si on définit manuellement la langue via le fichier config
        self.config_file = Path('config.ini')
        self.config_read = configparser.ConfigParser(allow_no_value=True)
        self.config_read.read(self.config_file, encoding='utf-8-sig')
        # On vérifie si args.language existe
        if args.language:
            self.lang = f'{args.language}.json'
        # Sinon on récupère manuellement la langue vvia config.ini
        else:
            try:
                self.config_lang = self.config_read.get('Language', 'language')
                self.lang = f'{self.config_lang}.json'

            # ou on récupère la langue du système
            except (configparser.NoOptionError, configparser.NoSectionError):
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
            self.language_comment = desc['language']
            self.makePDFTitle = desc['makePDFTitle']
            self.makepdf = desc['makePDF']
            self.addingmodsinprogress = desc['addingmodsinprogress']
            self.makingpdfended = desc['makingpdfended']
            self.pdfTitle = desc['pdfTitle']
            self.ErrorCreationPDF = desc['ErrorCreationPDF']
            self.end_of_prg = desc['end_of_prg']

        # On crée une liste pour les réponses O/N
        self.list_yesno = [self.yes.lower(), self.no.lower(), self.yes[0].lower(), self.no[0].lower()]


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
                column, row = os.get_terminal_size()
                maj_txt = f'[red]{self.existing_update}[/red]{self.url_mods.rstrip("/")}{soup_link_prg["href"]}'
                lines_update = maj_txt.splitlines()
                for line in lines_update:
                    print(f'{line.center(column)}')

        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            msg_error = f'{err_url.reason} : {url_script}'
            write_log(msg_error)


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
        self.crashlog_path = Path('logs').joinpath('crash-log.txt')
        # Creation des dossiers et fichiers
        if not self.path_temp.is_dir():
            os.mkdir('temp')
        # On crée le fichier config.ini si inexistant, puis (si lancement du script via l'executable et non en ligne de commande) on sort du programme si on veut ajouter des mods à exclure
        if not self.config_file.is_file():
            self.set_config_ini()
            if not args.modspath:
                print(f'\t[bold cyan]{self.first_launch}[/bold cyan]')
                print(f'\t[bold cyan]{self.first_launch2}[/bold cyan]')
                maj_ok = Prompt.ask(f'\n\t{self.first_launch3}', choices=[self.list_yesno[0], self.list_yesno[1], self.list_yesno[2], self.list_yesno[3]])
                if maj_ok == self.list_yesno[1] or maj_ok == self.list_yesno[3]:
                    print(f'{lang.end_of_prg} ')
                    if Path('temp').is_dir():
                        shutil.rmtree('temp')
                    time.sleep(2)
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
        self.modinfo_content = None
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
        with open(self.config_file, "w", encoding="utf-8") as cfgfile:
            # Ajout du contenu
            config = configparser.ConfigParser(allow_no_value=True)
            mu_ver = f'# ModsUpdater v{__version__}'
            config.set('', mu_ver)
            config.add_section('ModPath')
            config.set('ModPath', 'path', str(self.path_mods))
            config.add_section('Language')
            config.set('Language', str(self.language_comment))
            if args.language:
                config.set('Language', 'language', args.language)  # from command line
            else:
                config.set('Language', '#language', 'fr_FR')
            config.add_section('Game_Version_max')
            config.set('Game_Version_max', self.setconfig01)
            config.set('Game_Version_max', 'version', '100.0.0')
            config.add_section('Mod_Exclusion')
            config.set('Mod_Exclusion', self.setconfig)
            if args.exclusion:
                for i in range(0, len(args.exclusion)):
                    config.set('Mod_Exclusion', 'mod' + str(i+1), args.exclusion[i])
            else:
                for i in range(1, 11):
                    config.set('Mod_Exclusion', 'mod' + str(i), '')
            config.write(cfgfile)

    def json_correction(self, txt_json):
        self.regex_name_json = r'"name" {0,}: {0,}"(.*)",{0,}'
        self.result_name_json = re.search(self.regex_name_json, txt_json, flags=re.IGNORECASE)
        self.regex_version_json = r'"version" {0,}: {0,}"(.*)",{0,}'
        self.result_version_json = re.search(self.regex_version_json, txt_json, flags=re.IGNORECASE)
        self.regex_modid_json = r'"modid" {0,}: {0,}"(.*)",{0,}'
        self.result_modid_json = re.search(self.regex_modid_json, txt_json, flags=re.IGNORECASE)
        self.regex_moddesc_json = r'"description" {0,}: {0,}"(.*)",{0,}'
        self.result_moddesc_json = re.search(self.regex_moddesc_json, txt_json, flags=re.IGNORECASE)
        if self.result_name_json:
            self.name_json = self.result_name_json.group(2)
        if self.result_version_json:
            self.version_json = self.result_version_json.group(2)
        if self.result_modid_json:
            self.modid_json = self.result_modid_json.group(2)
        if self.result_moddesc_json:
            self.moddesc_json = self.result_moddesc_json.group(2)
        return self.name_json, self.version_json, self.modid_json, self.moddesc_json

    def extract_modinfo(self, file):
        # On trie les fichiers .zip et .cs
        type_file = Path(file).suffix
        if type_file == '.zip':
            # On lit le fichier modinfo.json de l'archive et on recupere le modid, name et version
            self.filepath = Path(self.path_mods, file)
            if zipfile.is_zipfile(self.filepath):  # Vérifie si fichier est un Zip valide
                with zipfile.ZipFile(self.filepath) as fichier_zip:
                    with fichier_zip.open('modinfo.json') as modinfo_json:
                        self.modinfo_content = modinfo_json.read().decode('utf-8-sig')
            try:
                regex_name = r'"name" {0,}: {0,}"(.*)",{0,}'
                result_name = re.search(regex_name, self.modinfo_content, flags=re.IGNORECASE)
                regex_modid = r'"modid" {0,}: {0,}"(.*)",{0,}'
                result_modid = re.search(regex_modid, self.modinfo_content, flags=re.IGNORECASE)
                regex_version = r'"version" {0,}: {0,}"(.*)",{0,}'
                result_version = re.search(regex_version, self.modinfo_content, flags=re.IGNORECASE)
                regex_description = r'"description" {0,}: {0,}"(.*)",{0,}'
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
                    msg_error = f'{file} :\n\n\t {traceback.format_exc()}'
                    write_log(msg_error)
                msg_error = f'{file} :\n\n\t {traceback.format_exc()}'
                write_log(msg_error)
        elif type_file == '.cs':
            self.filepath = Path(self.path_mods, file)
            with open(self.filepath, "r", encoding='utf-8-sig') as fichier_cs:
                cs_file = fichier_cs.read()
                regexp_name = '(namespace )(\w*)'
                result_name = re.search(regexp_name, cs_file, flags=re.IGNORECASE)
                regexp_version = '(Version\s=\s\")([\d.]*)\"'
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
        compver = ''
        try:
            ver = VSUpdate.verif_formatversion(v1, v2)
            compver = semver.compare(ver[0], ver[1])
        except Exception:
            write_log(traceback.format_exc())
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
            msg_error = f'{err_url.reason} : {url}'
            write_log(msg_error)
        return log

    def accueil(self, _net_version):  # le _ en debut permet de lever le message "Parameter 'net_version' value is not used
        if self.gamever_max == '100.0.0':
            self.version = self.version_max
        else:
            self.version = self.gamever_max
        # *** Texte d'accueil ***
        column, row = os.get_terminal_size()
        txt_title01 = f'\n\n[bold cyan]{self.title} - v.{self.num_version} {self.author}[/bold cyan]'
        lines01 = txt_title01.splitlines()
        for line in lines01:
            print(line.center(column))
        # On vérifie si une version plus récente du script est en ligne
        maj_script = MajScript()
        maj_script.check_update_script()
        txt_title02 = f'\n[cyan]{self.title2} : [bold]{self.version}[/bold][/cyan]\n'
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
                print(f'Error in config.ini [Mod_Exclusion] mod{str(j)} : {err_parsing}')
                with open('errors.txt', 'a') as stderr_parsing, redirect_stderr(stderr_parsing):
                    print(dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' : ' + 'Error in config.ini [Mod_Exclusion] - mod' + str(j) + ' : ' + str(err_parsing), file=sys.stderr)
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
            version_value = self.extract_modinfo(mod_maj)[2]
            modid_value = self.extract_modinfo(mod_maj)[1]
            if modid_value == '':
                modid_value = re.sub(r'\s', '', modname_value).lower()
            filename_value = self.extract_modinfo(mod_maj)[4]
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
                print(f' [green]{modname_value[0].upper()}{modname_value[1:]}[/green]: {self.compver1} : {version_value} - {self.compver2} : {mod_last_version}')
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
                        print(f'\t{self.compver3} : {file_size_mo} {self.compver3a}')
                        print(f'\t[green] {modname_value} v.{mod_last_version}[/green] {self.compver4}')
                        try:
                            os.remove(filename_value)
                        except PermissionError:
                            msg_error = f'{filename_value} :\n\n\t {traceback.format_exc()}'
                            write_log(msg_error)
                            sys.exit()
                        wget.download(dl_link, str(self.path_mods))
                        self.Path_Changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
                        log_txt = self.get_changelog(self.Path_Changelog)  # On récupère le changelog
                        self.mods_updated[modname_value] = log_txt
                        print('\n')
                        self.nb_maj += 1
            except urllib.error.URLError as err_url:
                # Affiche de l'erreur si le lien n'est pas valide
                msg_error = f'{err_url.reason} : {modname_value}'
                write_log(msg_error)
            except KeyError:
                print(f'[green] {modname_value}[/green]: [red]{self.error} !!! {self.error_modid}[/red]')

    def resume(self, netversion):
        # Résumé de la maj
        if self.nb_maj > 1:
            print(f'  [yellow]{self.summary1}[/yellow] \n')
            print(f'{self.summary2} :')
            log_filename = f'updates_{dt.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not self.path_logs.is_dir():
                os.mkdir('logs')
            log_path = Path(self.path_logs, log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(f'\n\t\t\tMods Vintage Story {netversion} - {self.last_update} : {dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
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
            print(f'{self.summary4} :')
            log_filename = f'updates_{dt.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            if not self.path_logs.is_dir():
                os.mkdir('logs')
            log_path = Path(self.path_logs, log_filename)
            with open(log_path, 'w', encoding='utf-8-sig') as logfile:
                logfile.write(f'\n\t\t\tMods Vintage Story {netversion} - {self.last_update} : {dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
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
            print(f'\n {self.summary6} :\n - [red]{modinfo_values[0]} [italic](v.{modinfo_values[2]})[italic][/red]')
        if len(self.mods_exclu) > 1:
            print(f'\n {self.summary7} :')
            for k in range(0, len(self.mods_exclu)):
                # On appelle la fonction pour extraire modinfo.json
                modinfo_values = self.extract_modinfo(self.mods_exclu[k])
                print(f' - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')


# Création du pdf.
class GetInfo:
    def __init__(self, mod_name, mod_id, mod_moddesc, mod_filepath):
        # path
        self.csvfile = Path('temp', 'csvtemp.csv')
        self.filepath = mod_filepath
        self.path_temp = 'temp'
        self.path_png = Path('temp', 'png')
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
        with open(self.csvfile, "a", encoding="windows-1252", newline='') as fichier:
            objet_csv = csv.writer(fichier)
            for items in self.modsinfo_dic:
                objet_csv.writerow([items, self.modsinfo_dic[items][0], self.modsinfo_dic[items][1], self.modsinfo_dic[items][2]])
        return self.modsinfo_dic

    def get_url(self, modid):
        url = os.path.join(self.api_url, modid)
        req = urllib.request.Request(url)
        try:
            urllib.request.urlopen(req)  # On teste l'existence du lien
            req_page = requests.get(url)
            resp_dict = req_page.json()
            mod_asset_id = str(resp_dict['mod']['assetid'])
            mod_urlalias = str(resp_dict['mod']['urlalias'])
            if mod_urlalias:
                self.test_url_mod = f'https://mods.vintagestory.at/{mod_urlalias}'
            else:
                self.test_url_mod = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}'
            return self.test_url_mod
        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            msg_error = f'{err_url.reason} : {self.test_url_mod}'
            write_log(msg_error)
        except KeyError:
            msg_error = traceback.format_exc()
            write_log(msg_error)
            sys.exit()


class MakePdf:
    def __init__(self):
        self.langchoice = LanguageChoice()
        # var temps
        self.current_dateTime = datetime.now()
        self.date_dl = self.current_dateTime.strftime("%Y-%m-%d %H:%M")
        self.annee = self.current_dateTime.strftime("%Y")
        self.mois = self.current_dateTime.strftime("%m")
        self.jour = self.current_dateTime.strftime("%d")
        # path
        self.csvfile = Path('temp', 'csvtemp.csv')

    def makepdf(self):
        # On crée le pdf
        monpdf = FPDF('P', 'mm', 'A4')
        margintop_page = 10
        monpdf.set_top_margin(margintop_page)
        monpdf.set_auto_page_break(True, margin=10)
        monpdf.set_page_background((200, 215, 150))
        monpdf.add_page(same=True)
        nom_fichier_pdf = f'VS_Mods_{self.annee}_{self.mois}_{self.jour}.pdf'
        monpdf.oversized_images = "DOWNSCALE"
        monpdf.oversized_images_ratio = 5
        width_img = 180
        x = (210-width_img)/2
        monpdf.image('banner.png', x=x, y=5, w=width_img)
        # Titre
        monpdf.set_font("helvetica", size=20, style='B')
        monpdf.set_text_color(6, 6, 65)  # Couleur RGB pour le titre
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
                monpdf.set_font("helvetica", size=7, style='B')
                row.cell(ligne[0], link=ligne[2])
                # cellule 3 - description
                monpdf.set_font("helvetica", size=6)
                row.cell(ligne[1])

        try:
            monpdf.output(nom_fichier_pdf)
        except PermissionError:
            print(f'[red]{lang.ErrorCreationPDF}[/red]')


# Définitions des arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("--modspath", help='Enter the mods directory (in quotes)', required=False, type=pathlib.Path)
argParser.add_argument("--language", help='Set the language file', required=False)
argParser.add_argument("--nopause", help="Disable the pause at the end of the script", choices=['false', 'true'], type=str.lower, required=False, default='false')
argParser.add_argument("--exclusion", help="Write filenames of mods with extension (in quotes) you want to exclude (each mod separated by space)", nargs="+")
args = argParser.parse_args()
# Fin des arguments

# Efface le fichier crash-log-XXXXXXXXXXX.txt si présents
crashlog_path = Path('logs').joinpath('crash-log.txt')
if crashlog_path.is_file():
    os.remove(crashlog_path)


# Test si il existe un fichier langue. (english par defaut)
try:
    lang = LanguageChoice()
except Exception:
    traceback_info = traceback.format_exc()
    write_log(traceback_info)
    sys.exit()


def datapath():
    new_path_data = Prompt.ask(f'{lang.datapath} : ')
    new_path_data = Path(new_path_data)
    return new_path_data


# On récupère le dossier des mods par argument, sinon on definit par defaut
if args.modspath:
    path_mods = Path(args.modspath)
else:
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
config_make_pdf = None
if not Path(config_path).is_file():
    if not args.modspath:
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

# Création du pdf (si argument nopause est false)
if args.nopause == 'false':
    make_pdf = None
    while make_pdf not in {str(lang.yes).lower(), str(lang.yes[0]).lower(), str(lang.no).lower(), str(lang.no[0]).lower()}:
        make_pdf = Prompt.ask(f'{lang.makepdf}', choices=[lang.list_yesno[0], lang.list_yesno[1], lang.list_yesno[2], lang.list_yesno[3]])
    if make_pdf == str(lang.yes).lower() or make_pdf == str(lang.yes[0]).lower():
        # Construction du titre
        asterisk = '*'
        nb_asterisk = len(lang.makePDFTitle) + 4
        string_asterisk = asterisk * nb_asterisk
        print(f'\t[green]{string_asterisk}[/green]')
        print(f'\t[green]* {lang.makePDFTitle} *[/green]')
        print(f'\t[green]{string_asterisk}[/green]')

        # uniquement pour avoir le nb de mods (plus rapide car juste listing)
        nb_mods = 0
        nb_mods_ok = 0
        print('\n')
        for mod in glob.glob(f'{path_mods}\*.*'):
            if os.path.splitext(mod)[1] == '.zip' or os.path.splitext(mod)[1] == '.cs':
                nb_mods += 1
        for modfilepath in glob.glob(f'{path_mods}\*.*'):
            if os.path.splitext(modfilepath)[1] == '.zip' or os.path.splitext(modfilepath)[1] == '.cs':
                nb_mods_ok += 1
                info_content = VSUpdate(modfilepath).extract_modinfo(modfilepath)
                GetInfo(info_content[0], info_content[1], info_content[3], info_content[4]).get_infos()
                print(f'\t\t{lang.addingmodsinprogress} {nb_mods_ok}/{nb_mods}', end="\r")
        pdf = MakePdf()
        pdf.makepdf()
        print(f'\n\n\t\t[blue]{lang.makingpdfended}\n[/blue]')
        input(f'{lang.exiting_script}')
    elif make_pdf == str(lang.no).lower() or make_pdf == str(lang.no[0]).lower():
        print(f'{lang.end_of_prg} ')
        time.sleep(3)

# On efface le dossier temp
if Path('temp').is_dir():
    shutil.rmtree('temp')
