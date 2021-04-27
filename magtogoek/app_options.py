"""
Script that contains different click options and the functions to add them to the click command.

FIXME
"""

import click


def add_options(options):
    """decorator to pass list of options to click commands."""

    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def adcp_options(input_files=True, yearbase=True, sonar=True):
    """return shared adcp options. They can they be passe with the add option decorator
    Paramters:
    ----------
    inputs_files:
        Adds input_options
    yearbase:
        Adds yearbase
    sonar:
        Adds sonar
    """
    options = []
    if input_files:
        options += [
            click.option(
                "-i",
                "--input-files",
                multiple=True,
                type=click.Path(exists=True),
                help="Expression identifying adcp files. Call `-i` for each files.",
            )
        ]

    options += [
        click.option(
            "-n",
            "--netcdf-output",
            nargs=1,
            type=click.STRING,
            help="Expression for netcdf output file or files name",
        ),
        click.option(
            "-o",
            "--odf-output",
            nargs=1,
            type=click.STRING,
            help="Expression for odf file or files name",
        ),
        click.option(
            "--merge/--no-merge",
            help="""Merge input into one output file.,
    Default --merge""",
            default=True,
        ),
        click.option(
            "-N",
            "--nav",
            type=click.Path(exists=True),
            help="""path/to/netcdf4 file containing the nav data made with
            the `make_navigation` function. (`from magtogoek.utils import make_navigation`)""",
        ),
    ]
    if sonar:
        options += [
            click.option(
                "-s",
                "--sonar",
                type=click.Choice(["wh", "sv", "os", "sw", "sw_pd0"]),
                help="""String designating type of adcp. This
    is fed to CODAS Multiread or switches to the magtogoek RtiReader.""",
            )
        ]
    if yearbase:
        options += [
            click.option(
                "-y",
                "--yearbase",
                type=click.INT,
                help="""year when the adcp sampling started. ex: `1970`""",
            )
        ]
    options += [
        click.option(
            "-O",
            "--adcp-orientation",
            type=click.Choice(["up", "down"]),
            help="""Vertical orientation of the adcp.""",
            default=None,
            show_default=True,
        ),
        click.option(
            "-m",
            "--magnetic-declination",
            type=click.FLOAT,
            help="""Declination of the magnetic north in degree east.
            Corrects from magnetic to true (geographic) coordinates and heading.""",
            default=None,
            show_default=True,
        ),
        click.option(
            "-l",
            "--leading-trim",
            type=click.STRING,
            help="""Removes a count of leading data or data before a given date or datetime.
    Formats: Date "YYYYMMDDT" or "YYYYMMDDThhmmss.ssss",  Count (int): """,
            nargs=1,
            default=None,
        ),
        click.option(
            "-t",
            "--trailing-trim",
            type=click.STRING,
            help="""Removes a count of trailing data or data after a given date or datetime.
    Formats: Date "YYYYMMDDT" or "YYYYMMDDThhmmss.ssss",  Count (int): """,
            nargs=1,
            default=None,
        ),
        click.option(
            "--qc/--no-qc",
            help="Do quality control.",
            default=True,
            show_default=True,
        ),
        click.option(
            "-a",
            "--amplitude-threshold",
            type=click.FLOAT,
            help="Amplitude threshold (0-255). Defaults to 0.",
            nargs=1,
            default=0,
            show_default=True,
        ),
        click.option(
            "-p",
            "--percentgood-threshold",
            type=click.FLOAT,
            help="Percentage of 4 beam threshold (0-100). Defaults to 90.",
            default=90,
            show_default=True,
        ),
        click.option(
            "-c",
            "--correlation-threshold",
            type=click.FLOAT,
            help="Correlation threshold (0-255).",
            nargs=1,
            default=64,
            show_default=True,
        ),
        click.option(
            "-u",
            "--horizontal-velocity-threshold",
            type=click.FLOAT,
            help="Horizontal velocity threshold (u,v). [m/s]",
            nargs=1,
            default=5,
            show_default=True,
        ),
        click.option(
            "-w",
            "--vertical-velocity-threshold",
            type=click.FLOAT,
            help="Vertial velocity threshold (w).  [m/s]",
            nargs=1,
            default=5,
            show_default=True,
        ),
        click.option(
            "-e",
            "--error-velocity-threshold",
            type=click.FLOAT,
            help="Error velocity threshold. [m/s]",
            nargs=1,
            default=5,
            show_default=True,
        ),
        click.option(
            "--sidelobes/--no-sidelobes",
            help="Do side lobe correction.",
            default=True,
            show_default=True,
        ),
        click.option(
            "-d",
            "--bottom-depth",
            type=click.FLOAT,
            help="""If provided, this fixed depth will be
            used for sidelobes correction.""",
            default=None,
            show_default=True,
        ),
        click.option(
            "-D",
            "--sensor-depth",
            type=click.FLOAT,
            help="""If provided, this fixed depth will be
            used for the adcp depth (XducerDepth).""",
            default=None,
            show_default=True,
        ),
        click.option(
            "-m_cor",
            "--motion_correction_mode",
            help="""Corrects motion with bottomTrack `bt` or navigation `nav`.
            For `nav`, a netcdf file made with `magtogoek.navigation` needs to be
            with options `-N` for the `nav` option""",
            default="bt",
            type=click.Choice(["bt", "nav"]),
        ),
        click.option(
            "-P",
            "--pitch-threshold",
            type=click.FLOAT,
            help="Pitch threshold (0-180).",
            nargs=1,
            default=20,
            show_default=True,
        ),
        click.option(
            "-R",
            "--roll-threshold",
            type=click.FLOAT,
            help="Roll threshold (0-180).Defaults to 20.",
            nargs=1,
            default=20,
            show_default=True,
        ),
        click.option(
            "--drop-pg/--keep-pg",
            help="""Drop the percent good data from the output dataset.
    [default: --drop-pg]""",
            default=True,
        ),
        click.option(
            "--drop-corr/--keep-corr",
            help="""Drop the correlation data from the output dataset.
    [default: --drop-corr]""",
            default=True,
        ),
        click.option(
            "--drop-amp/--keep-amp",
            help="""Drop the amplitude data from the output dataset.
    [default: --drop-amp]""",
            default=True,
        ),
        click.option(
            "--mk-log/--no-mk-log",
            help="""Make an output log of the processing.""",
            default=True,
            show_default=True,
        ),
        click.option(
            "--mk-fig/--no-mk-fig",
            help="""Make figures to inspect the data.""",
            default=True,
            show_default=True,
        ),
        click.option(
            "--bodc-name/--gen-name",
            help="""Name of the output variables. Using --gen-name
    outputs generic variables names instead of BODC P01 name.
    [default: --bodc-name]""",
            default=True,
        ),
        click.option(
            "--keep_bt/--discard-bt",
            help="""Weather to use or discard the bottom (bt) track data.""",
            default=True,
            show_default=True,
        ),
    ]
    return options
