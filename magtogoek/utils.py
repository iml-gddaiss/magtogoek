"""
magotogek utils
"""
import json
import typing as tp
from pathlib import Path

import click
import numpy as np


def ensure_list_format(value: tp.Union[str, int, float, tp.List[tp.Union[str, int, float]]]) -> tp.List[str]:
    """
    """
    if isinstance(value, (set, tuple)):
        value = list(value)
    elif not isinstance(value, list):
        value = [value]

    return value


def print_filenames(file_type: str, filenames: tp.List) -> str:
    """Format a string of filenames for prints

    `file_type` files :
      |-filename1
           :
      |-filenameN

    """
    return (
        file_type
        + " files : \n  |-"
        + "\n  |-".join([p.name for p in list(map(Path, filenames))])
    )


def get_files_from_expression(filenames: tp.Union[str, tp.List[str]]) -> tp.List[str]: # TODO tester
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

    else:
        _filenames = []
        for filename in filenames:
            _filenames += get_files_from_expression(filename)
        filenames = _filenames

    return sorted(filenames)


def is_valid_filename(filename: str, ext: str) -> str:
    """Check if directory or/and file name exist.

    -Ask to make the directories if they don't exist.
    -Ask  to overwrite the file if a file already exist.
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


def dict2json(filename: str, dictionary: tp.Dict, indent: int = 4) -> None:
    """Makes json file from dictionary

    Parameters
    ----------
    dictionary
    filename
    indent :
        argument is passed to json.dump(..., indent=indent)
    """
    with open(filename, "w") as f:
        json.dump(dictionary, f, indent=indent)


def json2dict(json_file: tp.Union[str, Path]):
    """Open json file as a dictionary."""
    with open(json_file) as f:
        dictionary = json.load(f)
    return dictionary


def resolve_relative_path(relative_path, current_path):
    """ """
    return Path(current_path).resolve().parent.joinpath(relative_path).resolve()


def nans(shape: tp.Union[list, tuple, np.ndarray]) -> np.ndarray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)