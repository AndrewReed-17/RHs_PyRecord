"""
Robert Henning's, Python Record, 2026
RHs_PyRecord.py

Bibliothèque légère de journalisation pour Python, orientée simplicité, lisibilité et réutilisation.

Compatibility:
- Python

Author: Robert Henning
Licence : MIT, 2026
Repos : https://github.com/AndrewReed-17/RHs_PyRecord
"""

from __future__ import annotations

import inspect
import platform
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Callable, Optional, TextIO, Union

__all__ = ["Level", "Record"]


class Level(IntEnum):
    """
    Niveaux de détail du journal.

    L'ordre numérique est volontairement orienté vers la verbosité :
    une valeur plus élevée signifie davantage de détails.

    Attributes:
        UNKNOWN: Niveau indéterminé.
        ERROR: Erreur.
        WARNING: Avertissement.
        SUCCESS: Succès.
        INFO: Information.
        DEBUG: Débogage.
    """
    UNKNOWN = 0
    ERROR = 10
    WARNING = 20
    SUCCESS = 25
    INFO = 30
    DEBUG = 40


LEVEL_LABEL = {
    Level.UNKNOWN: "UNK",
    Level.ERROR: "ERROR",
    Level.WARNING: "WARN",
    Level.SUCCESS: "SUCESS",
    Level.INFO: "INFO",
    Level.DEBUG: "DEBUG",
}


def _coerce_level(value: Union[int, str, Level, None]) -> Level:
    """
    Convertit une valeur arbitraire en niveau de journal valide.

    Args:
        value: Valeur source. Peut être un entier, une chaîne, un `Level`,
            ou `None`.

    Returns:
        Un membre de `Level`.

    Doctest:
        >>> _coerce_level(Level.INFO)
        <Level.INFO: 30>
        >>> _coerce_level(20)
        <Level.WARNING: 20>
        >>> _coerce_level("40")
        <Level.DEBUG: 40>
        >>> _coerce_level(None)
        <Level.UNKNOWN: 0>
    """
    if isinstance(value, Level):
        return value

    if value is None:
        return Level.UNKNOWN

    try:
        return Level(int(value))
    except Exception:
        return Level.UNKNOWN


def _default_cpu_name() -> Optional[str]:
    """
    Déduit un nom de processeur lisible sans dépendre d'un module projet.

    La fonction essaie d'abord `platform.processor()`, puis `platform.machine()`.
    Si rien n'est exploitable, elle renvoie `None`.

    Returns:
        Le nom du processeur, ou `None`.

    Doctest:
        >>> isinstance(_default_cpu_name(), (str, type(None)))
        True
    """
    cpu = platform.processor().strip() if platform.processor() else ""
    if cpu:
        return cpu

    machine = platform.machine().strip() if platform.machine() else ""
    if machine:
        return machine

    return None


def _default_kernel() -> Optional[str]:
    """
    Déduit le kernel de l'OS sous forme lisible.

    La forme retenue est généralement du type `Linux 6.8.0-...`.

    Returns:
        Le kernel lisible, ou `None`.

    Doctest:
        >>> k = _default_kernel()
        >>> isinstance(k, (str, type(None)))
        True
    """
    system = platform.system().strip() if platform.system() else ""
    release = platform.release().strip() if platform.release() else ""

    if system and release:
        return f"{system} {release}"
    if system:
        return system
    if release:
        return release
    return None


def _caller_name(depth: int = 2) -> Optional[str]:
    """
    Retourne le nom de la fonction appelante.

    Args:
        depth: Distance de remontée dans la pile d'appels.
            La valeur par défaut convient à l'usage interne de `Record`.

    Returns:
        Le nom de la fonction appelante, ou `None` si inaccessible.

    Doctest:
        >>> isinstance(_caller_name(), (str, type(None)))
        True
    """
    frame = inspect.currentframe()
    if frame is None:
        return None

    try:
        for _ in range(depth):
            frame = frame.f_back
            if frame is None:
                return None
        return frame.f_code.co_name
    finally:
        del frame


class Record:
    """
    Journaliseur léger, orienté bibliothèque publique.

    Le comportement est volontairement simple :
    - un en-tête est écrit à l'initialisation ;
    - les messages sont filtrés par niveau de détail ;
    - la sortie console et la sortie fichier sont optionnelles ;
    - les champs `None` sont omis au lieu d'être imprimés.

    Args:
        name: Nom logique du journal ou du projet.
        version: Version logicielle affichée dans l'en-tête.
        mode: Mode d'usage affiché dans l'en-tête (`CLI`, `GUI`, `API`, etc.).
        filepath: Chemin du fichier de sortie. Si `None`, aucun fichier n'est écrit.
        print_console: Active l'affichage console.
        write_file: Active l'écriture fichier.
        cpu_name: Nom du processeur à afficher. Si `None`, la ligne est omise.
        kernel: Chaîne du kernel à afficher. Si `None`, la ligne est omise.
        level: Niveau de détail maximal affiché.
        cpu_provider: Fonction optionnelle qui fournit un nom de CPU.

    Doctest:
        >>> r = Record(name="Demo", version="1.0", print_console=False, write_file=False, cpu_name="Intel i386", kernel="Linux 6.6", level=Level.INFO)
        >>> line = r.info("Bonjour", func="main")
        >>> "[INF]" in line and "Bonjour" in line and "@ main" in line
        True
        >>> r2 = Record(print_console=False, write_file=False, level=Level.WARNING)
        >>> r2.debug("caché") == ""
        True
    """

    def __init__(
        self,
        name: str = "Unnamed",
        version: str = "Unknown",
        mode: str = "CLI",
        filepath: Optional[str] = None,
        *,
        print_console: bool = False,
        write_file: bool = False,
        cpu_name: Optional[str] = None,
        kernel: Optional[str] = None,
        level: Union[int, str, Level] = Level.INFO,
        cpu_provider: Optional[Callable[[], Optional[str]]] = None,
    ) -> None:
        self.bool_initialized = False
        self.bool_print = bool(print_console)
        self.bool_file = bool(write_file)

        self.str_name = str(name)
        self.str_version = str(version)
        self.str_mode = str(mode).upper()
        self.str_CPU = cpu_provider() if cpu_provider else cpu_name
        self.str_kernel = kernel
        self.level = _coerce_level(level)

        self.str_date: Optional[str] = None
        self.str_type: Optional[str] = None
        self.str_messages: Optional[str] = None
        self.func: Optional[str] = None

        self.filepath = Path(filepath) if filepath else None
        self._fh: Optional[TextIO] = None

    # ------------------------------
    # Configuration
    # ------------------------------

    def set_level(self, level: Union[int, str, Level]) -> None:
        """
        Définit le niveau de détail maximal affiché.

        Plus le niveau est élevé, plus le journal devient bavard.

        Args:
            level: Niveau cible. Peut être un entier, une chaîne numérique,
                ou un membre de `Level`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.set_level(Level.DEBUG)
            >>> r.level
            <Level.DEBUG: 40>
            >>> r.set_level("20")
            >>> r.level
            <Level.WARNING: 20>
        """
        self.level = _coerce_level(level)

    def configure_mode(self, mode: str = "CLI") -> None:
        """
        Définit le mode d'interface affiché dans l'en-tête.

        La fonction ne fait qu'enregistrer une étiquette textuelle.

        Args:
            mode: Mode à afficher. Exemple : `CLI`, `GUI`, `API`, `TUI`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.configure_mode("gui")
            >>> r.str_mode
            'GUI'
        """
        mode = (mode or "CLI").strip().upper()
        self.str_mode = mode if mode else "CLI"

    def set_name(self, name: str) -> None:
        """
        Définit le nom logique du journal.

        Args:
            name: Nom à afficher dans l'en-tête.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.set_name("Projet X")
            >>> r.str_name
            'Projet X'
        """
        self.str_name = str(name)

    def set_version(self, version: str) -> None:
        """
        Définit la version logicielle affichée dans l'en-tête.

        Args:
            version: Chaîne de version.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.set_version("2.1.4")
            >>> r.str_version
            '2.1.4'
        """
        self.str_version = str(version)

    def set_cpu_info(self, cpu_name: Optional[str]) -> None:
        """
        Définit le nom du processeur affiché dans l'en-tête.

        Args:
            cpu_name: Nom du CPU. Si `None`, la ligne correspondante est omise.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.set_cpu_info("Intel i386")
            >>> r.str_CPU
            'Intel i386'
        """
        self.str_CPU = cpu_name

    def set_kernel_info(self, kernel: Optional[str]) -> None:
        """
        Définit le kernel de l'OS affiché dans l'en-tête.

        Args:
            kernel: Chaîne kernel. Si `None`, la ligne correspondante est omise.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.set_kernel_info("Linux 6.6.0")
            >>> r.str_kernel
            'Linux 6.6.0'
        """
        self.str_kernel = kernel

    def configure_output(
        self,
        *,
        print_console: Optional[bool] = None,
        write_file: Optional[bool] = None,
        filepath: Optional[str] = None,
    ) -> None:
        """
        Ajuste les destinations de sortie.

        Args:
            print_console: Active ou non l'affichage console.
            write_file: Active ou non l'écriture fichier.
            filepath: Chemin de sortie. Si fourni, il remplace l'existant.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.configure_output(print_console=True, filepath="x.log")
            >>> r.bool_print, str(r.filepath)
            (True, 'x.log')
        """
        if print_console is not None:
            self.bool_print = bool(print_console)

        if write_file is not None:
            self.bool_file = bool(write_file)

        if filepath is not None:
            self.filepath = Path(filepath)

    # ------------------------------
    # Initialisation / fermeture
    # ------------------------------

    def _open_file_if_needed(self) -> None:
        """
        Ouvre le fichier de journalisation si l'écriture fichier est active.

        Le fichier est toujours ouvert en écriture simple (`w`), donc recréé
        à chaque nouveau journal.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r._open_file_if_needed() is None
            True
        """
        if not self.bool_file or self.filepath is None or self._fh is not None:
            return

        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.filepath.open("w", encoding="utf-8")

    def _header_lines(self) -> list[str]:
        """
        Construit les lignes de l'en-tête.

        Les champs `None` sont omis.

        Doctest:
            >>> r = Record(name="A", version="1", print_console=False, write_file=False, cpu_name=None, kernel=None)
            >>> lines = r._header_lines()
            >>> any("CPU" in x for x in lines)
            False
        """
        lines = [
            "\n $ New record initiated ;\n",
            f"  - Name           : {self.str_name}\n",
            f"  - Version        : {self.str_version}\n",
            f"  - Interface Mode : {self.str_mode}\n",
            f"  - Started at     : {datetime.now().isoformat(timespec='seconds')}\n",
        ]

        if self.str_CPU is not None:
            lines.append(f"  - Processing Unit : {self.str_CPU}\n")

        if self.str_kernel is not None:
            lines.append(f"  - Kernel         : {self.str_kernel}\n")

        return lines

    def set_header(self) -> None:
        """
        Écrit l'en-tête du journal.

        Cette méthode initialise le flux si nécessaire, puis écrit un en-tête
        composé des métadonnées disponibles. Les champs valant `None` sont
        ignorés.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, name="Demo", version="1.0", cpu_name=None, kernel=None)
            >>> r.set_header()
            >>> r.bool_initialized
            True
        """
        self._open_file_if_needed()

        header = "".join(self._header_lines())
        self._write_raw(header)
        self.bool_initialized = True

    def close(self) -> None:
        """
        Ferme proprement le fichier de sortie.

        La méthode est sans effet si aucun fichier n'est ouvert.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r.close()
            >>> r.bool_initialized
            False
        """
        if self._fh is not None:
            try:
                self._fh.close()
            finally:
                self._fh = None

        self.bool_initialized = False

    def __enter__(self) -> "Record":
        """
        Entre dans un contexte `with`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> isinstance(r.__enter__(), Record)
            True
        """
        if not self.bool_initialized:
            self.set_header()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Quitte un contexte `with` et ferme le journal.

        Args:
            exc_type: Type d'exception éventuelle.
            exc: Instance d'exception éventuelle.
            tb: Traceback éventuel.
        """
        self.close()

    # ------------------------------
    # Écriture interne
    # ------------------------------

    def _write_raw(self, text: str) -> None:
        """
        Écrit une chaîne brute sur les sorties actives.

        Args:
            text: Texte à écrire.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> r._write_raw("abc\\n")
        """
        if self.bool_file:
            self._open_file_if_needed()
            if self._fh is not None:
                try:
                    self._fh.write(text)
                    self._fh.flush()
                except Exception:
                    pass

        if self.bool_print:
            print(text, end="" if text.endswith("\n") else "\n")

    def _format(self, message: str, level: Level, func: Optional[str]) -> str:
        """
        Construit une ligne de journal formatée.

        Si `func` est fourni, il est affiché après `@`. Sinon, cette partie
        est omise.

        Args:
            message: Message principal.
            level: Niveau de journalisation.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False)
            >>> line = r._format("salut", Level.INFO, "main")
            >>> "[INF]" in line and "@ main" in line
            True
            >>> line2 = r._format("salut", Level.INFO, None)
            >>> "@ " in line2
            False
        """
        self.str_date = datetime.now().isoformat(timespec="seconds")
        self.str_type = LEVEL_LABEL.get(level, "UNK")
        self.str_messages = str(message)
        self.func = func

        base = f" $ [{self.str_date}] - [{self.str_type}] | {self.str_messages}"
        if func is not None:
            base += f" @ {func}"
        return base + "\n"

    # ------------------------------
    # API publique
    # ------------------------------

    def log(
        self,
        message: str,
        level: Union[int, str, Level] = Level.INFO,
        func: Optional[str] = None,
    ) -> str:
        """
        Écrit une entrée de journal si le niveau demandé est autorisé.

        Le filtrage s'effectue à partir du niveau de détail fixé par `set_level`.
        Un message plus verbeux que le seuil courant est ignoré.

        Args:
            message: Texte à journaliser.
            level: Niveau du message.
            func: Nom de la fonction source. Si `None`, le nom de l'appelant
                est tenté automatiquement.

        Returns:
            La ligne écrite, ou une chaîne vide si le message est filtré.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.INFO)
            >>> ok = r.log("visible", Level.WARNING, func="main")
            >>> "visible" in ok
            True
            >>> hidden = r.log("cache", Level.DEBUG, func="main")
            >>> hidden == ""
            True
        """
        if not self.bool_initialized:
            self.set_header()

        level = _coerce_level(level)

        if level > self.level:
            return ""

        if func is None:
            func = _caller_name()

        line = self._format(message, level, func)

        try:
            self._write_raw(line)
        except Exception:
            pass

        return line

    def info(self, message: str, func: Optional[str] = None) -> str:
        """
        Journalise un message de type information.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.INFO)
            >>> "INF" in r.info("bonjour", func="main")
            True
        """
        return self.log(message, Level.INFO, func)

    def warn(self, message: str, func: Optional[str] = None) -> str:
        """
        Journalise un avertissement.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.WARNING)
            >>> "WAR" in r.warn("attention", func="main")
            True
        """
        return self.log(message, Level.WARNING, func)

    def error(self, message: str, func: Optional[str] = None) -> str:
        """
        Journalise une erreur.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.ERROR)
            >>> "ERR" in r.error("panne", func="main")
            True
        """
        return self.log(message, Level.ERROR, func)

    def debug(self, message: str, func: Optional[str] = None) -> str:
        """
        Journalise un message de débogage.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.DEBUG)
            >>> "DBG" in r.debug("trace", func="main")
            True
        """
        return self.log(message, Level.DEBUG, func)

    def success(self, message: str, func: Optional[str] = None) -> str:
        """
        Journalise un succès.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.SUCCESS)
            >>> "SUC" in r.success("ok", func="main")
            True
        """
        return self.log(message, Level.SUCCESS, func)

    def sucess(self, message: str, func: Optional[str] = None) -> str:
        """
        Alias conservé pour compatibilité avec l'ancien nom fautif.

        Args:
            message: Texte à écrire.
            func: Nom de la fonction appelante, ou `None`.

        Doctest:
            >>> r = Record(print_console=False, write_file=False, level=Level.SUCCESS)
            >>> "SUC" in r.sucess("ok", func="main")
            True
        """
        return self.success(message, func)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)