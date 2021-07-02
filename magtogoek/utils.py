"""
magotogek utils
"""
import json
import typing as tp
import warnings
from datetime import datetime
from pathlib import Path

import click


class FileNotFoundError(Exception):
    pass


class Logger:
    """Logger object can log and print messages.

    Logger objects print log and warning messages  while building a
    logbook from them. The logbook is formatted as a string in
    `self.logbook`. Logger objects keep count of the warnings in
    `self.w_count`.

    Parameters
    ----------
    logbook : str, default None.
        Formatted logbook.
    level : int  Default 0.
        Level controls which messages are printed.
        [0: prints all, 1: print only warnings, 2: prints None]

    Attributes
    ----------
    logbook :
        String of the formatted logbook build from the different entries.
    w_count :
        Number of Warning.

    Methods
    -------
    section :
        Makes a new sections.

    log :
        Log and print a log message. Prints if level is greater or equal 0
    warning :
        Log and print warning message. Prints if level is greater or equal 1
    reset :
        Resets the logbook and the warning count.
    """

    def __init__(self, logbook: str = "", level: int = 0):

        self.logbook = logbook
        self.w_count = 0
        self.level = level

    def __repr__(self):
        return self.logbook

    def section(self, section: str, t: bool = False):
        """Add a new section.
        Parameters:
        -----------
        section:
           Section's names.
        t:
           Log time if True.

        """
        time = "" if t is False else " " + self._timestamp()
        self.logbook += "[" + section + "]" + time + "\n"
        click.secho(section, fg="green") if self.level < 1 else None

    def log(self, msg: str, t: bool = False):
        """Add a log.
        Parameters
        ----------
        msg :
           Message to log.
        t :
           Log time if True.
        """
        if isinstance(msg, list):
            [self.log(m, t=t) for m in msg]
        else:
            if self.level < 1:
                print(msg)
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    def warning(self, msg: str, t: bool = False):
        """Add a warning.
        Parameters
        ----------
        msg :
           Message to log.
        t :
           Log time if True.
        """
        if isinstance(msg, list):
            [self.warning(m, t=t) for m in msg]
        else:
            if self.level < 2:
                click.echo(click.style("WARNING:", fg="yellow") + msg)
                self.w_count += 1
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    def reset(self):
        """Reset w_count and logbook."""
        self.logbook = ""
        self.w_count = 0

    @staticmethod
    def _timestamp():
        """Make a time stamp"""
        return datetime.now().strftime("%Y-%m-%d %Hh%M:%S")


def get_files_from_expresion(filenames: tp.Tuple[str, tp.List[str]]) -> tp.List[str]:
    """Get existing files from expression.

    Returns a list of existing files.

    Raises
    ------
    FileNotFoundError :
        If files does not exist, or a matching regex not found.
    """
    if isinstance(filenames, str):
        p = Path(filenames)
        if p.is_file():
            filenames = [filenames]
        else:
            filenames = sorted(map(str, p.parent.glob(p.name)))
            if len(filenames) == 0:
                raise FileNotFoundError(f"Expression `{p}` does not match any files.")

    return sorted(filenames)


def is_valid_filename(filename: str, ext: str) -> str:
    """Check if directory or/and file name exist.

    -Ask to make the directories if they don't exist.
    -Ask  to ovewrite the file if a file already exist.
    -Adds the correct suffix (extension) if it was not added
     but keeps other suffixes.
        Ex. path/to/file.ext1.ext2.ini
    """
    if Path(filename).suffix != ext:
        filename += f"{ext}"

    while not Path(filename).parents[0].is_dir():
        if click.confirm(
            click.style(
                "Directory does not exist. Do you want to create it ?", bold=True
            ),
            default=False,
        ):
            Path(filename).parents[0].mkdir(parents=True)
        else:
            filename = ask_for_filename(ext)

    if Path(filename).is_file():
        if not click.confirm(
            click.style(
                f"A `{ext}` file with this name already exists. Overwrite ?", bold=True
            ),
            default=True,
        ):
            return is_valid_filename(ask_for_filename(ext), ext)
    return filename


def ask_for_filename(ext: str) -> str:
    """ckick.prompt that ask for `filename`"""
    return click.prompt(
        click.style(
            f"\nEnter a filename (path/to/file) for the `{ext}` file. ", bold=True
        )
    )


def dict2json(file_name: str, dictionnary: tp.Dict, indent: int = 4) -> None:
    """Makes json file from dictionnary

    Parameters
    ----------
    indent :
        argument is passed to json.dump(..., indent=indent)
    """
    with open(file_name, "w") as f:
        json.dump(dictionnary, f, indent=indent)


def json2dict(json_file: str):
    """Open json file as a dictionnary."""
    with open(json_file) as f:
        dictionary = json.load(f)
    return dictionary
