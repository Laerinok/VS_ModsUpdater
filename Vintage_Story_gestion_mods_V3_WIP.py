# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des mods de Vintage Story :
- Liste les mods installés et vérifie s'il existe une version plus récente
- Affiche la liste de mods (nom - version installée - version la plus récente - Lien de DL) sous la forme d'un fichier .pdf
"""
__author__ = "Jay"
__date__ = "2023-05-31"

import csv
import glob
import json
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

# Définition des chemins
PATH_MODS = os.path.join(os.getenv('APPDATA'), "VintagestoryData\\Mods")
PATH_TEMP = "temp"  # Dossier temporaire pour l'extraction pour le json à l'interieur du zip
ADRESS_FILE_CSV = "VS_mods_link_list.csv"  # Emplacement du fichier csv où est stocké la liste des jeux et adresse web
EXCLUSION_FILE = os.path.join(os.getenv('APPDATA'), "VintagestoryData\\Mods\\exclusion_maj.txt")

# Initialisation des listes
mod_elem = []
mod_filename = []

# Initialisation des dico
dic_mods = {}
dic_url = {}

# Initialisation des variables
URL_MOD_PAGE = "https://mods.vintagestory.at"
nb_maj = 0

# Creation du dossier temp
if not os.path.isdir(PATH_TEMP):
    os.mkdir('temp')


class CsvFile:
    def __init__(self):
        self.csv_file_path = os.path.join(PATH_MODS, 'liste_mods.csv')

    @staticmethod
    def clean_file(file):
        if os.path.isfile(file):
            os.remove(file)

    def add_csv_line(self, modname, version, lastversion, moddurl):
        with open(self.csv_file_path, "a", encoding="utf-8", newline='') as file:
            csv_object = csv.writer(file)
            csv_object.writerow([modname, version, lastversion, moddurl])

    # Creation du csv
    def csv_create(self):
        # On efface le csv précédant si il existe
        self.clean_file(self.csv_file_path)
        # ajout entetes dans csv
        self.add_csv_line('mod', 'version installée', 'dernière version', 'url page')


def json_correct(txt_json):
    name_json = ''
    version_json = ''
    regex_name_json = r'(\"name\": \")([\w*\s*]*)'
    result_name_json = re.search(regex_name_json, txt_json, flags=re.IGNORECASE)
    regex_version_json = r'(\"version\": \")([\d*.]*)'
    result_version_json = re.search(regex_version_json, txt_json, flags=re.IGNORECASE)
    if result_name_json:
        name_json = result_name_json.group(2)
    if result_version_json:
        version_json = result_version_json.group(2)
    return name_json, version_json


# *** Texte d'accueil ***
print('\n\n\t\t\t\t[bold cyan]Script de mise à jour des mods de Vintage Story (par Laerinok).[/bold cyan]')
print('\t\t\t\t\t  https://mods.vintagestory.at/list/mod\n\n')

# Charge la liste des mods à exclure de la maj, si le fichier n'existe pas, on le crée
if os.path.isfile(EXCLUSION_FILE):
    with open(EXCLUSION_FILE, 'r') as exclu_file:
        mods_exclu = exclu_file.read().splitlines()
else:
    with open(EXCLUSION_FILE, 'a') as exclu_file:
        mods_exclu = []

for elem in glob.glob(PATH_MODS + "\*.zip"):
    regex_filename = r'.*\\Mods\\(.*)'
    result_filename = re.search(regex_filename, elem, flags=re.IGNORECASE)
    mod_filename.append(result_filename.group(1))

# Ouvrir le fichier csv contenant les liens et creation du dico mod_name:link
if os.path.isfile(ADRESS_FILE_CSV):
    with open(ADRESS_FILE_CSV, 'r') as csv_f:
        # Créer un objet csv à partir du fichier
        content_csvfile = csv.reader(csv_f)
        for row in content_csvfile:
            dic_url[row[0]] = row[1]
else:
    print(f'[red]ERREUR !!![/red]Fichier [yellow]{ADRESS_FILE_CSV}[/yellow] introuvable.\n')

# Création du fichier csv (contenant la liste des mods) et ajout des en-tete
"""csv_file = CsvFile()
csv_file.csv_create()"""

for filename in mod_filename:
    if filename not in mods_exclu:
        path_mod_file = os.path.join(PATH_MODS, filename)
        if zipfile.is_zipfile(path_mod_file):  # Vérifie si fichier est un Zip valide
            archive = zipfile.ZipFile(path_mod_file, 'r')
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
                    regex_version = r'version'
                    result_version = re.search(regex_version, content_file, flags=re.IGNORECASE)
                    mod_name = des[result_name.group()]
                    mod_version = des[result_version.group()]
                except Exception as err:
                    json_correct = json_correct(content_file)
                    mod_name = json_correct[0]
                    mod_version = json_correct[1]
            print(f'  [green]{mod_name}[/green] - [white]{filename}[/white]')
            mod_elem.append(mod_version)
            mod_elem.append(filename)
            try:
                mod_elem.append(dic_url[mod_name])
            except KeyError:
                print(f'[red]ERREUR !![/red] : Veuillez ajouter le mod [yellow]{mod_name}[/yellow] au fichier VS_mods_link_list.csv.')
                print('Programme interrompu.')
                os.system("pause")
                break
            dic_mods[mod_name] = mod_elem  # Création du dico contenant le nom du mod, la version installée, le nom du fichier et le lien de téléchargement
            mod_elem = []  # On réinitialise la liste pour la ligne suivante
            print(f'\tRecherche de maj...')
            # On compare la version installée avec celle en ligne:
            url = dic_mods[mod_name][2] + '#tab-files'  # Lien de la page à scraper
            # On teste la validité du lien url
            req = urllib.request.Request(url)
            try:
                urllib.request.urlopen(req)  # On teste l'existence du lien
                # *** On poursuit le script si le lien est valide ***
                req_page = requests.get(url)
                page = req_page.content
                soup = BeautifulSoup(page, features="html.parser")
                soup_last_version = soup.find("div", {"class": "changelogtext"})
                soup_dl_link = soup.find("a", {"class": "downloadbutton"})
                regex_html_version = r'<strong>v(.*)</strong>'
                version_online = re.search(regex_html_version, str(soup_last_version))
                online_mod_version = version_online.group(1)
                regex_dl_link = r'href=\"(.*)\">'
                link = re.search(regex_dl_link, str(soup_dl_link))
                dl_link = f'{URL_MOD_PAGE}{link.group(1)}'

                if dic_mods[mod_name][0] != online_mod_version:
                    print(f'\tversion installée : {dic_mods[mod_name][0]} / version en ligne {online_mod_version} (URL page : {dic_mods[mod_name][2]} )')
                    resp = requests.get(dl_link, stream=True)
                    file_size = int(resp.headers.get("Content-length"))
                    file_size_mo = round(file_size / (1024**2), 2)
                    print(f'\tTaille du fichier : {file_size_mo} Mo')
                    print("\tTéléchargement de " + mod_name + " en cours...")
                    wget.download(dl_link, PATH_MODS)
                    print('\n')
                    os.remove(path_mod_file)
                    nb_maj += 1
                else:
                    print(f'\tPas de nouvelle version pour le mod {mod_name}\n')
                # csv_file.add_csv_line(mod_name, dic_mods[mod_name][0], online_mod_version, dic_url[mod_name])

            except urllib.error.URLError as e:
                # Affiche de l'erreur si le lien n'est pas valide
                print(e.reason)

if nb_maj > 1:
    message_final = f'  [yellow]Fin de la recherche. \n\t{nb_maj} mods ont été mis à jour.[/yellow]'
elif nb_maj == 1:
    message_final = f'  [yellow]Fin de recherche. \n\t{nb_maj} mod a été mis à jour.[/yellow]'
else:
    message_final = f'  [yellow]Aucune mise à jour disponible.[/yellow]\n'
print(message_final)

# On efface le dossier temp
try:
    shutil.rmtree(PATH_TEMP)
except OSError as e:
    print(f"Error:{ e.strerror}")
os.system("pause")
