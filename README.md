# Robert Henning's, Python Record, 2026

Bibliothèque légère de journalisation pour Python, orientée simplicité, lisibilité et réutilisation.

## Présentation

`RHs_PyRecord` fournit une classe `Record` destinée à produire des journaux structurés avec :

- un en-tête de session ;
- des niveaux de détail filtrables ;
- une sortie console facultative ;
- une sortie fichier facultative ;
- un format stable avec indication de la fonction appelante ;
- une prise en charge des champs optionnels : toute valeur `None` est omise.

Le module a été pensé comme une brique publique, sans dépendance à un module de projet spécifique.

## Contenu du module

Le module expose :

- `Level` : énumération des niveaux de journalisation ;
- `Record` : classe principale de journalisation.

## Niveaux disponibles

- `UNKNOWN`
- `ERROR`
- `WARNING`
- `SUCCESS`
- `INFO`
- `DEBUG`

Le filtrage s'effectue selon le niveau de détail fixé sur l'instance.  
Un message dont le niveau est supérieur au seuil courant est ignoré.

## En-tête

L'en-tête peut inclure, selon disponibilité :

- le nom du projet ;
- la version ;
- le mode d'interface ;
- la date de démarrage ;
- le nom du processeur ;
- le kernel de l'OS.

Tout champ valant `None` est omis.

## Fonctionnement général

La classe `Record` peut :

- écrire dans un fichier ;
- écrire dans la console ;
- retourner la ligne formatée produite ;
- être utilisée avec `with`.

Le nom de la fonction appelante peut être injecté explicitement via `func`, ou déduit automatiquement.

## Installation

Copiez simplement `RHs_PyRecord.py` dans votre projet.

Exemple :

```python
from RHs_PyRecord import Record, Level
```

## Exemple minimal

```python
from RHs_PyRecord import Record, Level

logger = Record(
    name="Demo",
    version="1.0.0",
    print_console=True,
    write_file=False,
    cpu_name="Intel i386",
    kernel="Linux 6.6.0",
    level=Level.INFO,
)

logger.info("Démarrage correct.", func="main")
logger.warn("Paramètre inhabituel.", func="main")
logger.debug("Trace interne.", func="main")  # ignoré si niveau courant = INFO
```

## Exemple avec fichier

```python
from RHs_PyRecord import Record

logger = Record(
    name="Demo",
    version="1.0.0",
    filepath="demo.log",
    print_console=False,
    write_file=True,
)

logger.set_header()
logger.error("Échec de lecture.", func="load_data")
logger.close()
```

## Utilisation avec `with`

```python
from RHs_PyRecord import Record

with Record(
    name="Demo",
    version="1.0.0",
    filepath="demo.log",
    write_file=True,
) as logger:
    logger.success("Initialisation terminée.", func="main")
```

## Notes de conception

- Le fichier est ouvert en écriture simple, donc recréé à chaque nouvelle initialisation.
- Les champs `None` ne sont jamais imprimés.
- L'alias `sucess()` est conservé pour compatibilité avec l'ancien nom fautif.
- La méthode `set_level()` contrôle le niveau de détail maximal affiché.

## Documentation intégrée

Le module contient des docstrings et des doctests.  
Pour les exécuter :

```bash
python RHs_PyRecord.py
```

ou, de manière explicite :

```bash
python -m doctest -v RHs_PyRecord.py
```

## Licence MIT

Permission est accordée, sans frais, à toute personne obtenant une copie de ce logiciel et des fichiers de documentation associés, d'utiliser, copier, modifier, fusionner, publier, distribuer, sous-licencier et/ou vendre des copies du logiciel, sous réserve de conserver l'avis de copyright et l'avis de licence.

Le texte complet de la licence MIT peut être placé dans un fichier séparé `LICENSE`.
