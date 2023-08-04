# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story v.1.0.6:
Pour NET4 ET NET7
- Liste les mods installés et vérifie s'il existe une version plus récente et la télécharge
- Affiche le résumé
- Crée un fichier updates.log
- maj des mods pour une version donnée du jeu
- Verification de la présence d'une maj du script sur moddb
"""
__author__ = "Laerinok"
__date__ = "2023-08-04"


import configparser
import datetime
import glob
import json
import locale
import os
import re
import shutil
import sys
import urllib.request
import urllib.error
import zipfile
import requests
import semver
import wget
from bs4 import BeautifulSoup
from rich import print


class Language:
    def __init__(self):
        self.num_version = '1.0.6'
        self.url_mods = 'https://mods.vintagestory.at/'
        self.path_lang = "lang"
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
            self.setconfig = desc['setconfig']
            self.setconfig01 = desc['setconfig01']
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


class MajScript(Language):
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
            regexp_ch_log_ver = '<strong>(.*)</strong>'
            ch_log_ver = re.search(regexp_ch_log_ver, str(soup_changelog))
            # On compare les versions
            result = VSUpdate.compversion(self.num_version, ch_log_ver[1])
            if result == -1:
                print(f'[red]\t\t{self.existing_update}[/red]{self.url_mods.rstrip("/")}{soup_link_prg["href"]}\n')

        except urllib.error.URLError as err_url:
            # Affiche de l'erreur si le lien n'est pas valide
            print(err_url.reason)


class VSUpdate(Language):
    def __init__(self, vsdata_path):
        # ##### Version du script pour affichage titre.
        super().__init__()
        # #####
        # Définition des chemins
        self.path_config = os.path.join(vsdata_path, 'ModConfig', 'ModsUpdater')
        self.config_file = os.path.join(self.path_config, 'config.ini')
        self.path_temp = "temp"
        self.path_mods = os.path.join(vsdata_path, 'Mods')
        self.url_api = 'https://mods.vintagestory.at/api/mod/'
        # Creation des dossiers et fichiers
        if not os.path.isdir(self.path_temp):
            os.mkdir('temp')
        if not os.path.isdir(self.path_config):
            try:
                os.mkdir(self.path_config)
            except FileNotFoundError:
                os.mkdir(os.path.join(vsdata_path, 'ModConfig'))
                os.mkdir(self.path_config)
        # Ancien emplacement du chargement du fichier langue
        Language()
        # On crée le fichier config.ini si inexistant, puis on sort du programme si on veut ajouter des mods à exclure
        if not os.path.isfile(self.config_file):
            self.set_config_ini()
            print(f'\t\t[bold cyan]{self.first_launch}[/bold cyan]')
            print(f'\t\t[bold cyan]{self.first_launch2}[/bold cyan]')
            maj_ok = input(f'\t\t{self.first_launch3} ({self.yes}/{self.no}) : ')
            if maj_ok == str(self.no).lower() or maj_ok == str(self.no[0]).lower():
                sys.exit()
        # On charge le fichier config.ini
        self.config_read = configparser.ConfigParser(allow_no_value=True)
        self.config_read.read(self.config_file, encoding='utf-8-sig')
        self.config_path = self.config_read.get('ModPath', 'path')
        self.path_mods = self.config_path
        # Définition des listes
        self.mod_filename = []
        self.mods_exclu = []
        # Mods_list
        self.liste_mod_maj = []
        # Définition des dico
        self.mods_updated = {}
        # Définition des variables
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

    def set_config_ini(self):
        # Création du config.ini si inexistant
        with open(self.config_file, "w", encoding="utf-8") as cfgfile:
            # Ajout du contenu
            config = configparser.ConfigParser(allow_no_value=True)
            config.add_section('ModPath')
            config.set('ModPath', 'path', self.path_mods)
            config.add_section('Game_Version_max')
            config.set('Game_Version_max', self.setconfig01)
            config.set('Game_Version_max', 'version', '100')
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
        type_file = os.path.splitext(file)[1]
        if type_file == '.zip':
            # On extrait le fichier modinfo.json de l'archive et on recupere le modid, name et version
            self.filepath = os.path.join(self.path_mods, file)
            if zipfile.is_zipfile(self.filepath):  # Vérifie si fichier est un Zip valide
                archive = zipfile.ZipFile(self.filepath, 'r')
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
                    json_correct = self.json_correction(content_file)
                    mod_name = json_correct[0]
                    mod_version = json_correct[1]
                    mod_modid = json_correct[2]
        elif type_file == '.cs':
            self.filepath = os.path.join(self.path_mods, file)
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
        # On crée la liste contenant les noms des fichiers zip
        for elem in glob.glob(self.path_mods + "\*.zip"):
            regex_filename = r'.*\\Mods\\(.*)'
            result_filename = re.search(regex_filename, elem, flags=re.IGNORECASE)
            self.mod_filename.append(result_filename.group(1))
        # On ajoute les fichiers .cs
        for elem_cs in glob.glob(self.path_mods + "\*.cs"):
            regex_filename_cs = r'.*\\Mods\\(.*)'
            result_filename_cs = re.search(regex_filename_cs, elem_cs, flags=re.IGNORECASE)
            self.mod_filename.append(result_filename_cs.group(1))
        if len(self.mod_filename) == 0:
            print(f"{self.err_list}")
            os.system("pause")
            sys.exit()
        return self.mod_filename

    @staticmethod
    def compversion(v1, v2):
        regex_ver = '(\d.*)'
        ver1 = re.search(regex_ver, v1)
        ver2 = re.search(regex_ver, v2)
        compver = semver.compare(ver1[1], ver2[1])
        return compver

    @staticmethod
    def get_max_version(versions):  # uniquement versions stables
        # print(f'liste versions: {versions}')  # debug
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
        return log

    def accueil(self, net_version):
        if self.gamever_max == str(100):
            self.version = self.version_max
        else:
            self.version = self.gamever_max
        # *** Texte d'accueil ***
        print(f'\n\n\t\t\t[bold cyan]{self.title} ({net_version}). v.{self.num_version} {self.author}[/bold cyan]')
        # On vérifie si une version plus récente du script est en ligne
        maj_script = MajScript()
        maj_script.check_update_script()
        print(f'\n\t\t\t\t\t\t[cyan]{self.title2}[bold] {self.version}[/bold][/cyan]\n')
        # print('\n\t\t\t\t\thttps://mods.vintagestory.at/list/mod\n\n')

    def mods_exclusion(self):
        # On crée la liste des mods à exclure de la maj
        for j in range(1, 11):
            try:
                modfile = self.config_read.get('Mod_Exclusion', 'mod' + str(j))
                if modfile != '':
                    self.mods_exclu.append(modfile)
            except configparser.NoSectionError:
                pass

    def mods_list(self):
        # Création de la liste des mods à mettre à jour
        # On retire les mods de la liste d'exclusion
        self.liste_mod_maj = self.liste_complete_mods()
        for modexclu in self.mods_exclu:
            if modexclu in self.liste_mod_maj:
                self.liste_mod_maj.remove(modexclu)

    def update_mods(self):
        # Comparaison et maj des mods
        for mod_maj in self.liste_mod_maj:
            modname_value = self.extract_modinfo(mod_maj)[0]
            version_value = self.extract_modinfo(mod_maj)[2]
            modid_value = self.extract_modinfo(mod_maj)[1]
            if modid_value == '':
                modid_value = re.sub(r'\s', '', modname_value).lower()
            filename_value = self.extract_modinfo(mod_maj)[3]
            mod_url_api = os.path.join(self.url_api, modid_value)
            # On teste la validité du lien url
            req = urllib.request.Request(mod_url_api)
            try:
                urllib.request.urlopen(req)  # On teste l'existence du lien
                req_page = requests.get(mod_url_api)
                resp_dict = req_page.json()
                mod_asset_id = (resp_dict['mod']['assetid'])
                mod_last_version = (resp_dict['mod']['releases'][0]['modversion'])
                mod_file_onlinepath = (resp_dict['mod']['releases'][0]['mainfile'])
                # compare les versions des mods
                result_compversion = self.compversion(version_value, mod_last_version)
                print(f' [green]{modname_value}[/green]: {self.compver1}{version_value} - {self.compver2}{mod_last_version}')
                # On récupère les version du jeu nécessaire pour le mod
                mod_game_versions = resp_dict['mod']['releases'][0]['tags']
                mod_game_version_max = self.get_max_version(mod_game_versions)
                # print(f'ver max: {mod_game_version_max}\n ver max jeu souhaitée {gamever_max}')  # debug
                # On compare la version max souhaité à la version necessaire pour le mod
                result_game_version = self.compversion(mod_game_version_max, self.gamever_max)
                # print(result_compversion)  # debug
                # print(result_game_version)  # debug
                if result_game_version == 0 or result_game_version == -1:
                    # print('on peut mettre à jour')  # debug
                    #  #####
                    if result_compversion == -1:
                        dl_link = os.path.join(self.url_mods, mod_file_onlinepath)
                        resp = requests.get(dl_link, stream=True)
                        file_size = int(resp.headers.get("Content-length"))
                        file_size_mo = round(file_size / (1024 ** 2), 2)
                        print(f'\t{self.compver3}{file_size_mo} {self.compver3a}')
                        print(f'\t[green] {modname_value} v.{mod_last_version}[/green] {self.compver4}')
                        os.remove(filename_value)
                        wget.download(dl_link, self.path_mods)
                        self.Path_Changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
                        log_txt = self.get_changelog(self.Path_Changelog)  # On récupère le changelog
                        self.mods_updated[modname_value] = log_txt
                        print('\n')
                        self.nb_maj += 1
            except urllib.error.URLError as er:
                # Affiche de l'erreur si le lien n'est pas valide
                print(er.reason)
            except KeyError:  # as err: decommenter pour debugage
                # print(err.args)  # pour debuggage
                print(f'[green] {modname_value}[/green]: [red]{self.error} !!! {self.error_modid}[/red]')

    def resume(self, netversion):
        # Résumé de la maj
        if self.nb_maj > 1:
            print(f'  [yellow]{self.summary1}[/yellow] \n')
            print(f'{self.summary2}')
            log_filename = f'{netversion}_updates_{datetime.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(log_filename, 'w', encoding='utf-8-sig') as logfile:
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
            log_filename = f'{netversion}_updates_{datetime.datetime.today().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(log_filename, 'w', encoding='utf-8-sig') as logfile:
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

        else:
            print(f'  [yellow]{self.summary5}[/yellow]\n')

        if len(self.mods_exclu) == 1:
            modinfo_values = self.extract_modinfo(self.mods_exclu[0])
            print(f'\n {self.summary6}\n - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')
        if len(self.mods_exclu) > 1:
            print(f'\n {self.summary7}')
            for k in range(0, len(self.mods_exclu)):
                # On appelle la fonction pour extraire modinfo.json
                modinfo_values = self.extract_modinfo(self.mods_exclu[k])
                print(f' - [red]{modinfo_values[0]} v.{modinfo_values[2]}[/red]')


# On cherche les versions installées de Vintage Story (Net4 et/ou NET7)
path_VS_net4 = os.path.join(os.getenv('appdata'), 'VintagestoryData')
path_VS_net7 = os.path.join(os.getenv('appdata'), 'VintagestoryDataNet7')
if os.path.isdir(path_VS_net4):
    # On lance l'instance pour net4
    net4 = VSUpdate(path_VS_net4)
    net4.accueil('Net4')
    net4.mods_exclusion()
    net4.mods_list()
    net4.update_mods()
    net4.resume('Net4')
if os.path.isdir(path_VS_net7):
    # On lance l'instance pour net7
    net7 = VSUpdate(path_VS_net7)
    net7.accueil('Net7')
    net7.mods_exclusion()
    net7.mods_list()
    net7.update_mods()
    net7.resume('Net7')

# On efface le dossier temp
try:
    shutil.rmtree('temp')
except OSError as e:
    print(f"Error:{e.strerror}")
os.system("pause")
