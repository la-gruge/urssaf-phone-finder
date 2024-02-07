import argparse
import fonctions

def run_main():
    parser = argparse.ArgumentParser()

    fonctions.arg_add_arguments(parser)

    args = parser.parse_args()
    fichier_siret = args.fichier

    logger = fonctions.logging_params()

    liste_sirets = fonctions.open_file(fichier_siret)

    logger.info(f"Votre fichier contient {len(liste_sirets)} numéros de SIRET valides.")

    content_var, cookies_var = fonctions.get_content(logger)
    fonctions.data['javax.faces.ViewState'] = fonctions.get_balise(content_var)
    fonctions.cookies['JSESSIONID'] = fonctions.get_cookie(cookies_var)

    logger.debug(f"{fonctions.cookies['JSESSIONID'] = }\n {fonctions.data['javax.faces.ViewState'] = }")

    dict_phones = fonctions.get_num(liste_sirets, logger=logger)

    logger.info(dict_phones)

    fonctions.to_csv(dict_phones, logger=logger)

    if args.excel:
        fonctions.to_xlsx(dict_phones, logger=logger)

if __name__ == "__main__":
    run_main()