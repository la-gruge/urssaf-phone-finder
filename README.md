# urssaf-phone-finder


urssaf-phone-finder est un script python **totalement gratuit** et **open-source** permettant d'automatiser la recherche de numéros de téléphone d'entreprises renseignés dans les bases de données de l'[URSSAF](https://www.urssaf.fr) française.


Il utilise le numéro de SIRET de chaque société/entreprise (voire de certaines associations pour celles en possédant un), puis interroge les serveurs de l'URSSAF pour retrouver un numéro de téléphone.

Il faut conserver à l'esprit que l'URSSAF peut du jour au lendemain corriger cette fuite de données.


## Quelle utilité ?


Ce script permet d'accéder à des numéros de téléphones non publics, c'est-à-dire :


* non référencé sur annuaire,

* non disponible sur le ou les sites/réseaux sociaux des entreprises,

* non disponible via les fiches établissement de Google.



Le plus intéressant est qu'il permet de trouver des numéros de lignes mobiles (débutants par les préfixes 06 ou 07 en France). Il renvoie évidemment aussi des numéros de téléphones fixes ou mobiles qui sont disponibles, ou non, publiquement.


Ces numéros de téléphones sont transmis à l'URSSAF par le/les dirigeants des entreprises ou par leurs conseillers (comptables en général).


Ces numéros ne devraient pas être disponibles publiquement via des requêtes HTTP POST transmises aux serveurs de l'URSSAF, mais ils le sont... alors j'ai envie de dire [ALLONS-Y QUOI](https://youtu.be/PzyDHTHBFFM) 👽

**Bon à savoir** : vous pouvez tester des numéros de SIRET de sociétés ayant été radiées (c'est-à-dire d'entreprise qui n'existe tout simplement plus). Oui oui, c'est aussi ça la magie de l'URSSAF 🧙‍♂️

## Cas d'usage

* Ce script peut servir dans des tâches d'OSINT, pour retrouver le numéro de téléphone d'une ou plusieurs personnes. Par exemple, vous souhaitez trouver le/les numéros de Monsieur XXX. Ce dernier possède plusieurs sociétés. Récupérer les SIRET respectifs de ses entreprises et tester les avec le script. Comme précisé précédemment, vous pouvez même tester les ANCIENNES entreprises de Monsieur XXX, puisque des numéros de mobiles m'ont été renvoyés avec des SIRET de sociétés radiées.

* Il peut aussi être utilisé par des marketeurs un peu bourrins pour faire de l'enrichissement de données ou de _l'outbound marketing_ (à vous de gérer les questions de RGPD 🥶). En utilisant la base officielle Sirène, vous sélectionnez les sociétés corespondant à vos critères, par exemple "_Entreprise créée il y a moins de 5 ans, ayant entre 10 et 50 salariés et basée dans la région Bretagne ou Nouvelle-Aquitaine_" (de nombreux autres critères sont disponibles). Cela vous permettra de récupérer les numéros de SIRET correspondants à votre recherche puis des numéros de téléphone à l'aide du script.

## Ce qui est nécessaire


Un ordinateur en état de marche avec ⚠️⚠️ **la version 3.10 minimum** ⚠️⚠️ de Python installée ainsi qu'une connexion internet et... c'est tout.


Le script prend en entrée :


* un numéro (ou une liste) de numéro(s) de SIRET valide(s) (composé de 14 chiffres).



Il renvoie :


* des numéros de téléphones fixe ou mobile lorsqu'ils sont disponibles pour le numéro de SIRET testé, le tout dans un fichier CSV (et XLSX si vous le souhaitez).




## Fonctionnement (derrière le rideau)


Pour chaque numéro de SIRET à tester, le script envoie une requête HTTP avec la méthode POST aux serveurs de l'URSSAF.


Si un numéro de téléphone est disponible, alors la réponse du serveur contient celui-ci. Si aucun numéro de téléphone n'est disponible, alors la réponse du serveur est _None_ ou "" (_empty string_)


Pour tester 1,000 numéros SIRET, il faudra compter environ 1min 30sec, soit plus ou moins 11 SIRET testés par seconde.


## Utilisation


Premièrement, il vous faut une liste de SIRET dont vous aimeriez récupérer les numéros de téléphones. Vous pouvez **facilement et gratuitement** vous créer une telle liste de SIRET en utilisant [la base publique officielle de données d'entreprise Sirène](https://www.sirene.fr/sirene/public/creation-fichier).


Sur le site Sirène, triez les entreprises selon les critères de votre choix, par exemple le nombre de salariés, la localisation (par département, code postal etc), le/les domaines de leurs activités ou encore leur date de création etc.


Une fois le fichier CSV téléchargé, repérez la colonne SIRET. ⚠️ **A NE PAS CONFONDRE AVEC LA COLONNE SIREN** ⚠️

![SIRET sur Excel](/img/liste_excel.png "SIRET sur excel")


Sélectionnez les numéros de SIRET, puis copiez-les (Crtl+C).


Créez un nouveau fichier texte à l'aide du logiciel Notepad ou équivalent. ⚠️**PAS DE LOGICIELS DE TRAITEMENT DE TEXTE WORD, LIBRE OFFICE OU AUTRE**⚠️


Copiez-y les numéros de SIRET. Chaque ligne ne doit comporter qu'un seul numéro de SIRET (voir capture d'écran). Enregistrez ce fichier. À moins que vous ne soyez à l'aise avec la ligne de commande, ne mettez que des lettres, des chiffres ou des tirets dans le nom du fichier, mais pas d'espace ou de caractères accentués. Exemple de noms possibles :


* maliste01.txt

* maliste-02.txt

* ma_liste_de_sirets_BORDEAUX.txt

![fichier texte SIRET](/img/liste_texte.png "SIRET fichier texte")

Créez un nouvel environnement et installez les dépendances à l'aide de :
```bash
pip install -r requirements.txt
```
Lancer le script à l'aide de votre shell (bash sur Linux dans mon cas). Si vous utilisez MacOS, ce sera probablement le shell zsh. Si vous utilisez Windows (😷), ce sera plutôt PowerShell.

```bash
python3 main.py --data_src /home/la_gruge/liste_sirets.txt --data_dir 
/home/la_gruge/dossier_sirets/numeros_trouves --excel
```


* __main.py__ est le fichier d'entrée du script.
* __--data_src__ permet de renseigner le chemin du fichier contenant la liste de SIRET à tester. Ici, mon fichier se nomme "liste_siret.txt".
* __--data_dir__ permet de renseigner le chemin de destination du fichier .csv contenant les numéros de téléphones découverts. Je souhaite que mon fichier se nomme "numeros_trouves". Ne précisez pas l'extension ("numeros_trouves.csv" sera invalide), le script se cargera de la renseigner.
* __--excel__ est un drapeau. S'il est présent, alors les données seront aussi exportéés au format .xlsx. S'il n'est pas présent, seul le fichier .csv sera créé.

![Script ligne de commande](/img/script_cli.png "Script Bash")

## Améliorations possibles


Le script actuel est assez rudimentaire. C'est plus un POC réalisé pour le fun. Voici quelques-unes des améliorations possibles :


* Permettre d'extraire les numéros de SIRET directement depuis une feuille de calcul d'un classeur .xls, .xlsx (Microsoft Excel) ou encore .ods (Libre Office Calc)

* Permettre en entrée plusieurs fichiers contenant des listes de numéros SIRET.

* Récupération, en plus des numéros de téléphones, des autres informations disponibles (code NAF/APE, nom/raison sociale, adresse) dans les réponses HTTPS des serveurs de l'URSSAF. Contrairement aux numéros de téléphones, ces informations sont disponibles dans la base sirène.

* Transformer les requêtes synchrones en requêtes asynchrones (d'où le choix d'utiliser dès la création du script la librairie HTTPX plutôt que Requests).
