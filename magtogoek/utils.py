"""
magotogek utils
"""
import json
import typing as tp

import click
import numpy as np
from nptyping import NDArray
from pandas import Timestamp
from path import Path


def get_files_from_expresion(filenames: tp.Tuple[str, tp.List[str]]) -> tp.List[str]:
    """Get existing files from expression.

    Returns a list of existing files.

    Raises:
    -------
    FileNotFoundError:
        If files does not exist, or a matching regex not found.
    """
    if isinstance(filenames, str):
        p = Path(filenames)
        if p.isfile():
            filenames = [filenames]
        else:
            filenames = sorted(map(str, p.parent.glob(p.name)))
            if len(filenames) == 0:
                raise FileNotFoundError(f"Expression `{p}` does not match any files.")

    return sorted(filenames)


def validate_filename(filename: str, ext: str) -> str:
    """Check if directory or/and file name exist.

    Ask to make the directories if they don't exist.
    Ask  to ovewrite the file if a file already exist.

    Appends the correct suffix (extension) if none was given
    but keeps other suffixes.
    Ex. path/to/file.ext1.ext2.ini

    """
    print(filename)
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
            return validate_filename(ask_for_filename(ext), ext)
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
    Parameters:
    -----------
    indent:
        argument is passed to json.dump(..., indent=indent)
    """
    with open(file_name, "w") as f:
        json.dump(dictionnary, f, indent=indent)


def json2dict(json_file: str):
    """Open json file as a dictionnary."""
    with open(json_file) as f:
        dictionary = json.load(f)
    return dictionary


def nans(shape: tp.Tuple[list, tuple, NDArray]) -> NDArray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


class Logger:
    def __init__(self, logbook: str = "", level: int = 0):

        self.logbook = logbook
        self.w_count = 0
        self.level = level

    def __repr__(self):
        return self.logbook

    def section(self, section: str, t: bool = False):
        """
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
        """
        Parameters:
        -----------
        msg:
           Message to log.
        t:
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
        """
        Parameters:
        -----------
        msg:
           Message to log.
        t:
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

    @staticmethod
    def _timestamp():
        return Timestamp.now().strftime("%Y-%m-%d %Hh%M:%S")


def circular_distance(a1, a2, units="rad"):
    """
    Function circdist usage:
        d   =   circdist(a1,a2,units='rad')

    Returns to 'd' the distance between angles a1 and a2
    expected to be radians by default, or degrees if units
    is specified to 'deg'.
    Parameters
    ----------
    a1, a2 : float
        Input angle.
    units: str
        Units of input angles ('deg', 'rad')
    Returns
    -------
    float
        Angular distance between `a1` and `a2`.

    Notes:
    ------
    Taken from jeanlucshaw adcp2nc: https://github.com/jeanlucshaw/adcp2nc/
    """
    if units == "deg":
        a1 = np.pi * a1 / 180
        a2 = np.pi * a2 / 180

    if np.isscalar(a1) and np.isscalar(a2):
        v1 = np.array([np.cos(a1), np.sin(a1)])
        v2 = np.array([np.cos(a2), np.sin(a2)])
        dot = np.dot(v1, v2)
    elif not np.isscalar(a1) and np.isscalar(a2):
        a2 = np.tile(a2, a1.size)
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)
    else:
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)

    res = np.arccos(np.clip(dot, -1.0, 1.0))

    if units == "deg":
        res = 180 * res / np.pi

    return res
