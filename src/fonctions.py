import argparse
import csv
import logging
import platform
import random
import re

import httpx
import xlsxwriter

from pathlib import Path
from parsel import Selector
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed, wait_random, RetryCallState
from user_agents_os import liste_user_agents_os

def match_ua() -> str:
    '''Récupère le nom du système d'exploitation pour matcher le user-agent des futures requêtes'''
    match platform.system():
       case "Linux":
           ua_utilise = "Linux"

       case "Windows":
           ua_utilise = "Windows"

       case "Darwin":
           ua_utilise = "Macintosh"

       case _:
           ua_utilise = "Windows"
    
    return ua_utilise

cookies = {
    'JSESSIONID': None,
}

headers = {
    'User-Agent': random.choice(liste_user_agents_os[match_ua()]),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.due.urssaf.fr',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.due.urssaf.fr/declarant/index.jsf',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

data = {
    'form_siret': 'form_siret',
    'form_siret:form-compte-submit': 'OK',
}

url_base = 'https://www.due.urssaf.fr/declarant/index.jsf'
nombre_retry = 3
my_list = []

def logging_params() -> logging.Logger:
    FORMAT = '%(levelname)s: %(message)s'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler()
    logger_handler.setLevel(logging.INFO)
    logger_format = logging.Formatter(FORMAT)
    logger_handler.setFormatter(logger_format)
    logger.addHandler(logger_handler)

    return logger

def arg_add_arguments(parser: argparse.ArgumentParser) -> None:
    '''Ajoute les arguments au parser du module built-in Argparse'''
    parser.add_argument(
                    "--data_src",
                    type=Path,
                    default=Path(__file__).resolve().parent.parent / "data" / "liste_sirets.txt",
                    help="Chemin du fichier source contenant la liste des numéros de SIRET à tester.",
                    )

    parser.add_argument(
                    "--data_dir",
                    type=Path,
                    default=Path(__file__).resolve().parent.parent / "data" / "liste_sirets",
                    help="Chemin du fichier de sortie qui contiendra les numéros de SIRET enrichis des numéros de téléphone.",
                    )

    parser.add_argument(
                    "--excel",
                    action="store_true",
                    help="Permet d'exporter les données au format XLSX",
                    )

def open_file(fichier_siret) -> list:
    '''Ouvre le fichier contenant les numéros de SIRET puis applique une regex pour vérifier leurs bon formatage'''
    sirets = []
    with open(fichier_siret, encoding="utf-8") as file:
        while line := file.readline():

            if (len(line.strip()) == 0):
                continue
            temp = re.sub(r'[\s+]', '', line)
            apply_regex(sirets, temp)
    
    return sirets

def apply_regex(sirets: list, temp: str) -> None:
    '''Vérification, avec l'utilisation de regex, du bon formatage des numéros de SIRET'''
    if all([(len(temp)) == 14,
            temp.isascii() == True,
            temp.isdigit() == True],):
        sirets.append(temp)

def return_after_failing_retry(retry_state: RetryCallState, my_list: list = my_list):
    """Return my_list après les retry infructueux"""
    print(f"Return last value.\n{retry_state = }")
    return my_list

@retry(stop=stop_after_attempt(nombre_retry),
       retry=retry_if_exception_type(httpx.HTTPStatusError),
       retry_error_callback=return_after_failing_retry,
       wait=wait_fixed(2) + wait_random(0, 4))
def get_content(logger: logging.Logger,
                url: str = url_base) -> tuple[str, httpx.Cookies]:
    '''Requête HTTP get à l'url de base. Retourne la réponse et les cookies'''
    logger.debug(f"ESSAI NUMERO {get_content.retry.statistics['attempt_number']}")
    response = httpx.get(url, headers=headers).raise_for_status()
    logger.debug(f"STATUSCODE = {response.status_code}")
    return response.text, response.cookies

def get_balise(content: str) -> str:
    '''Enregistre les données d'une balise HTML pour formater convenablement nos futures requêtes HTTP'''
    selector = Selector(text=content)
    xpath_balise_html = "//input[@id='j_id1:javax.faces.ViewState:0']/@value"
    return selector.xpath(xpath_balise_html).get()

def get_cookie(cookies: httpx.Cookies) -> dict:
    '''Enregistre un cookie nécessaire aux futures requêtes HTTP'''
    cookie = cookies["JSESSIONID"]
    return cookie

@retry(stop=stop_after_attempt(nombre_retry),
      retry=retry_if_exception_type(httpx.HTTPStatusError or httpx.ConnectError),
      retry_error_callback=return_after_failing_retry,
      wait=wait_fixed(2) + wait_random(0, 4))
def get_num(liste_sirets: list,
            logger: logging.Logger,
            cookies: dict = cookies,
            data: dict = data,) -> dict:
    '''Récupère, si disponible, le numéro de téléphone correspondant au SIRET'''
    dict_phones = {}
    with httpx.Client() as client:
        while liste_sirets:
            cookies['_siretUtilisateur'] = liste_sirets[0]
            data['form_siret:form-grey-siret'] = liste_sirets[0]
    
            response = client.post(url_base,
                                cookies=cookies,
                                headers=headers,
                                data=data
                                ).raise_for_status()

            logger.debug(f"STATUSCODE = {response.status_code}")

            selector = Selector(text=response.text)
            numero = selector.xpath("//input[@id='form_declaration:champ_tel']/@value").get()
            if numero:
                logger.info(f"Le téléphone du SIRET n° {liste_sirets[0]} est {numero}")
            else:
                logger.info(f"Le SIRET n° {liste_sirets[0]} ne contient pas de numéro de téléphone")
                logger.debug(f"Le SIRET n° {liste_sirets[0]} est {numero}")

            dict_phones[liste_sirets[0]] = numero

            liste_sirets.pop(0)

        logger.debug("La liste des SIRETS est maintenant vide")

    return dict_phones
    
def to_csv(dict_phones: dict, chemin: Path, logger: logging.Logger) -> None:
    '''Convertit le dictionnaire en un fichier CSV'''
    with open(chemin.with_suffix('.csv'), 'w', newline='') as csv_file:  
        writer = csv.writer(csv_file)
        writer.writerow(["SIRET", "Numero_de_tel"])
        for key, value in dict_phones.items():
           writer.writerow([key, value])

    logger.info("Fichier CSV créé avec succés")

def to_xlsx(dict_phones: dict, chemin: Path, logger: logging.Logger) -> None:
    '''Convertit le dictionnaire (qui contient les SIRET et les numéros correspondants) en un fichier au format XLSX'''
    workbook = xlsxwriter.Workbook(chemin.with_suffix('.xlsx'), {'strings_to_numbers': False})
    worksheet = workbook.add_worksheet()

    worksheet.write(0, 0, "SIRET")
    worksheet.write(0, 1, "Téléphones")
    
    row_num, col_num = 1, 0
    for key, value in dict_phones.items():
        worksheet.write(row_num, col_num, key)
        worksheet.write(row_num, col_num+1, value)
        row_num += 1
    
    workbook.close()

    logger.info("Fichier XLSX créé avec succés")