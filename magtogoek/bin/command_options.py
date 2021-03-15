"""
TODO
"""

import click


def add_options(options):
    """decorator to pass list of options to click commands."""

    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def adcp_options():
    """return shared adcp options. They can they be passe with the add option decorator"""
    return [
        click.option(
            "-i",
            "--input-files",
            type=click.STRING,
            help="Expression identifying adcp files",
        ),
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
            "-F",
            "--platform-file",
            type=click.Path(exists=True),
            help="path/to/platform_file",
            nargs=1,
        ),
        click.option(
            "-G",
            "--gps",
            type=click.Path(exists=True),
            help="""path/to/netcdf4 file containing the gps data,
    `longitude`, `latitude`, of the platform. If provided,
    they will be used instead of the GPS data in the adcp file""",
        ),
        click.option(
            "-s",
            "--sonar",
            type=click.STRING,
            help="""String designating type of adcp. This
    is fed to CODAS Multiread or switches to the RTI
    binary reader. Must be one
    of `wh`, `os`, `bb`, `nb` or `sw`""",
        ),
        click.option(
            "-y",
            "--yearbase",
            type=click.INT,
            help="""year when the adcp sampling started. ex: `1970`""",
        ),
        click.option(
            "-O",
            "--adcp-orientation",
            type=click.Choice(["up", "down"]),
            help="""Vertical orientation of the adcp.""",
            default="down",
            show_default=True,
        ),
        click.option(
            "-l",
            "--start-time",
            type=click.STRING,
            help="Remove leading data before this date. Fomart (YYYYMMDDHHMM).",
            nargs=1,
        ),
        click.option(
            "-t",
            "--end-time",
            metavar="metavar test",
            type=click.STRING,
            help="Remove trailling data after this date. Format (YYYYMMDDHHMM).",
            nargs=1,
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
            "-E",
            "--error-velocity-threshold",
            type=click.FLOAT,
            help="Error velocity threshold. [m/s]",
            nargs=1,
            default=5,
            show_default=True,
        ),
        click.option(
            "--side-lobe/--no-side-lobe",
            help="Do side lobe correction.",
            default=True,
            show_default=True,
        ),
        click.option(
            "--m-corr/--no-m-corr",
            help="""Motion correction. Default[-no-m-corr] (True).
    Uses `bt` if available or GSP data. If the adcp
    file does not contain GPS data. A netcdf
    file with with variable named (`longitude`, `latitude`)
    needs to be provided with options `-G`""",
            default=False,
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
    ]
