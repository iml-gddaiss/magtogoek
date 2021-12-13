"""
Author: JeromeJGuay
Date: March 2 2021

This module contains the entry point for magtogoek CLI app `mtgk`.

Descriptions:
  FIXME

Usage:
    $ mtgk config [adcp, platform] [CONFIG_NAME] [OPTIONS]

    $ mtgk process [CONFIG_FILE]

    $ mtgk quick [adcp, ] [INPUT_FILES] [OPTIONS]

    $ mtgk check [rti, ] [INPUT_FILES]

Notes:
    Some module are imported by function since loading pandas, for example, is time consuming. Doing makes the
    navigation in the app quicker.
"""
import sys
import typing as tp
from pathlib import Path
from subprocess import run as subp_run

import click

from magtogoek.app_options import adcp_options, add_options
from magtogoek.configfile import BASE_CONFIG, ADCP_CONFIG
from magtogoek.utils import is_valid_filename, json2dict, resolve_relative_path
from magtogoek.version import VERSION

# ---------- Module or functions imported by commands ----------- #
# NOTE: PROBABLY NOT UP TO DATE
# from magtogoek.configfile import make_configfile
# from magtogoek.platforms import make_platform_template
# from magtogoek.adcp.loader import load_adcp_binary
# from magtogoek.adcp.utils import Logger
# from magtogoek.adcp.process import process_adcp, quick_process_adcp
# --------------------------------------------------------------- #

LOGO_PATH = resolve_relative_path("files/logo.json", __file__)


def _get_config_structure(_config: tp.Dict) -> tp.Dict:
    config_struct = dict()
    for section, items in _config.items():
        for item in items:
            config_struct[item] = section
    return config_struct


BASE_CONFIG_STRUCT = _get_config_structure(BASE_CONFIG)
ADCP_CONFIG_STRUCT = _get_config_structure(ADCP_CONFIG)

OPTIONS_NAME_TRANSLATOR = dict(
    adcp=dict(
        quality_control="qc",
        sidelobes_correction="sidelobes",
        merge_output_files="merge",
        drop_percent_good="drop_pg",
        drop_correlation="drop_corr",
        drop_amplitude="drop_amp",
        make_figures="mk_fig",
        make_log="mk_log",
    )
)
CONTEXT_SETTINGS = dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    help_option_names=["-h", "--help"],
)
TERMINAL_WIDTH = 80


def _print_info(ctx, callback, info_called):
    """Show command information"""
    if info_called is True:
        subp_run(["printf", r"\e[8;40;" + str(TERMINAL_WIDTH + 1) + "t"], check=True)
        click.clear()
        _print_logo(logo_path=LOGO_PATH, group=ctx.info_name)
        click.secho("\nDescriptions:", fg="red")
        _print_description(ctx.info_name)
        click.secho("\nUsage:", fg="red")
        _print_usage(ctx.info_name, ctx.parent)
        if ctx.info_name in ["mtgk", "config", "process", "quick", "check"]:
            click.secho("\nCommands:", fg="red")
        else:
            click.secho("\nArguments:", fg="red")
        _print_arguments(ctx.info_name)
        click.secho("\nOptions", fg="red")
        click.echo("  Use  -h/--help to show the options")
        click.echo("\n")
        sys.exit()


common_options = [
    click.option("--info", is_flag=True, callback=_print_info, help="Show command information"),
    click.version_option(VERSION)
]


# --------------------------- #
#      mtgk entry point       #
# --------------------------- #
@click.group(context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
def magtogoek(info):
    pass


# --------------------------- #
#        mtgk command         #
# --------------------------- #
@magtogoek.command("process")
@add_options(common_options)
@click.argument("config_file", metavar="[config_file]", type=click.Path(exists=True))
def process(info, config_file):
    """Process data by reading configfile"""
    # NOTE This could be update as a group with sensor specific command.
    # Doing so would allow the user to pass config options. The load_configfile
    # command is already able to take updated_params options and update de configfile.
    # The same options (or nearly all the same )as for adcp_config could be use.
    from configparser import ParsingError

    from magtogoek.configfile import load_configfile

    try:
        configuration = load_configfile(config_file)
    except ParsingError:
        print("Failed to open the given configfile.\n mtgk process aborted.")
        sys.exit()

    if configuration["HEADER"]["sensor_type"] == "adcp":
        from magtogoek.adcp.process import process_adcp

        process_adcp(configuration)


# --------------------------- #
#        mtgk groups          #
# --------------------------- #
@magtogoek.group("config", context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
def config(info):
    """Make configuration files or platform files"""


@magtogoek.group("quick", context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
def quick(info):
    """Quick data process without configfile"""


@magtogoek.group("check", context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
def check(info):
    """Get info on raw data files"""


@magtogoek.group("compute", context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
def compute(info):
    """Command to compute certain quantities."""


# --------------------------- #
#       config command        #
# --------------------------- #
@config.command("platform")
@add_options(common_options)
@click.argument("filename", metavar="[filename]", type=str)
@click.pass_context
def config_platform(ctx, info, filename):
    from magtogoek.platforms import make_platform_template

    filename = is_valid_filename(filename, ext=".json")
    make_platform_template(filename)
    click.echo(click.style(f"Platform file created for -> {filename}", bold=True))


@config.command("adcp")
@add_options(common_options)
@click.argument("config_name", metavar="[config_name]", type=str)
@click.option(
    "-T",
    "--platform",
    type=(click.Path(exists=True), str, str),
    help="platform_file, platform_id, sensor_id",
    default=(None, None, None),
    nargs=3,
)
@add_options(adcp_options())
@click.pass_context
def config_adcp(
        ctx, info, config_name, **options,
):
    """Command to make an adcp config files. The [OPTIONS] can be added
    before or after the [config_name]."""
    from magtogoek.configfile import make_configfile

    _print_passed_options(options)

    # check if a file already exists and format the `.ini` extension.
    config_name = is_valid_filename(config_name, ext=".ini")

    new_config_values = _format_options_for_configfile("adcp", options)

    make_configfile(filename=config_name, sensor_type="adcp", new_values=new_config_values)

    click.echo(
        click.style(
            f"Config file created for adcp processing -> {config_name}", bold=True
        )
    )


# --------------------------- #
#       quick command         #
# --------------------------- #
@quick.command("adcp")
@add_options(common_options)
@click.argument(
    "input_files",
    metavar="[input_files]",
    nargs=-1,
    type=click.Path(exists=True),
    required=True,
)
@add_options(adcp_options(input_files=False, sonar=False, yearbase=False))
@click.option(
    "-s",
    "--sonar",
    type=click.Choice(["wh", "sv", "os", "sw", "sw_pd0"]),
    help="String designating type of adcp. This  is fed to CODAS Multiread or switches to the magtogoek RTIReader.",
    required=True,
)
@click.option(
    "-y",
    "--yearbase",
    type=click.INT,
    help="""year when the adcp sampling started. ex: `1970`""",
    required=True,
)
@click.option(
    "-T",
    "--platform_type",
    type=click.Choice(["buoy", "mooring", "ship"]),
    help="Used for Proper BODC variables names",
    default="buoy",
)
@click.pass_context
def quick_adcp(
        ctx, info, input_files, sonar, yearbase, **options,
):
    """Command to make an quickly process adcp files. The [OPTIONS] can be added
    before or after the [inputs_files]."""
    from magtogoek.adcp.process import quick_process_adcp

    options = {
        **{"input_files": input_files, "yearbase": yearbase, "sonar": sonar},
        **options,
    }
    _print_passed_options(options)

    params = _convert_options_names("adcp", options)

    quick_process_adcp(params)


# --------------------------- #
#       check command         #
# --------------------------- #
@check.command("rti")
@add_options(common_options)
@click.argument(
    "input_files",
    metavar="[input_files]",
    nargs=-1,
    type=click.Path(exists=True),
    required=True,
)
@click.pass_context
def check_rti(ctx, info, input_files, **options):
    """Prints info about RTI .ENS files."""
    from magtogoek.adcp.rti_reader import RtiReader

    RtiReader(input_files).check_files()


@compute.command("nav", context_settings=CONTEXT_SETTINGS)
@add_options(common_options)
@click.argument(
    "input_files",
    metavar="[input_files]",
    nargs=-1,
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "-o",
    "--output-name",
    type=click.STRING,
    default=None,
    help="Name for the output file.",
)
@click.option(
    "-w", "--window", type=click.INT, default=1, help="Length of the averaging window.",
)
@click.pass_context
def navigation(ctx, info, input_files, **options):
    """Command to compute u_ship, v_ship, bearing from gsp data."""
    from magtogoek.navigation import compute_navigation

    compute_navigation(
        filenames=input_files,
        output_name=options["output_name"],
        window=options["window"],
    )


@magtogoek.command('odf2nc', context_settings=CONTEXT_SETTINGS)
@click.argument('input_files',
                metavar="[input_files]",
                nargs=-1,
                type=click.STRING,
                required=True)
@click.option(
    "-d",
    "--dims",
    type=click.STRING,
    multiple=True,
    default=None,
    help='Name of the variable to use as dimensions (coordinates).`-d` has to be called for every dimensions.')
@click.option(
    '-t',
    '--time',
    type=click.STRING,
    multiple=True,
    default=None,
    help='Name of the variables that need to be converted to datetime64. SYTM_01 time variable is automatically '
         'converted.')
@click.option('-m', '--merge', is_flag=True, default=False, help='Use the option to merge the output files.')
@click.option('-o', '--output_name', type=click.STRING, default=None)
@add_options(common_options)
@click.pass_context
def odf2nc(ctx, info, input_files, output_name, **options):
    from magtogoek.odf_format import convert_odf_to_nc
    convert_odf_to_nc(
        input_files=input_files,
        output_name=output_name,
        dims=options['dims'],
        time=options['time'],
        merge=options['merge'])


# ------------------------ #
#        Functions         #
# ------------------------ #
def _format_options_for_configfile(sensor_type, options):
    """format options into the  configfile structure"""
    options = _convert_options_names(sensor_type, options)

    configfile_struct = {}
    if sensor_type == "adcp":
        configfile_struct = {**BASE_CONFIG_STRUCT, **ADCP_CONFIG_STRUCT}
        if not options["bottom_depth"]:
            options["bottom_depth"] = ""
    options["platform_file"] = options["platform"][0]
    options["platform_id"] = options["platform"][1]
    options["sensor_id"] = options["platform"][2]
    del options["platform"]

    new_config_values = dict()
    for section in set(configfile_struct.values()):
        new_config_values[section] = dict()

    for option, value in options.items():
        if value is not None:
            new_config_values[configfile_struct[option]][option] = value

    return new_config_values


def _convert_options_names(sensor_type, options):
    """Translate options name.
    Translate options names from the command names to
    the parameters name used by magtogoek."""

    for key, item in OPTIONS_NAME_TRANSLATOR[sensor_type].items():
        options[key] = options.pop(item)

    return options


def _print_passed_options(ctx_params: tp.Dict):
    """print pass and default options/params"""
    click.secho("Options:", fg="green")
    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))
    for key, item in ctx_params.items():
        if item is not None:
            if item is True:
                click.echo(key + ": " + click.style(str(item), fg="green"))
            elif item is False:
                click.echo(key + ": " + click.style(str(item), fg="red"))
            elif type(item) is str:
                click.echo(key + ": " + click.style(str(item), fg="yellow"))
            else:
                click.echo(key + ": " + click.style(str(item), fg="blue"))
    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))


def _print_logo(logo_path: str = "files/logo.json", group: str = ""):
    """open and print logo from logo.json
    If a process is given, prints the process logo.
    """
    logos = json2dict(Path(__file__).parents[0] / Path(logo_path))
    click.secho("=" * TERMINAL_WIDTH, fg="white", bold=True)

    try:
        click.echo(click.style(logos["magtogoek"], fg="blue", bold=True))
        if group == "adcp":
            click.echo(click.style(logos["adcp"], fg="red", bold=True))

    except FileNotFoundError:
        click.echo(click.style("WARNING: logo.json not found", fg="yellow"))
    except KeyError:
        click.echo(click.style("WARNING: key in logo.json not found", fg="yellow"))

    click.echo(
        click.style(
            f"version: {VERSION}" + f" {group} ".rjust(67, " "), fg="green", bold=True,
        )
    )
    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))


def _print_arguments(group):
    """print group(command) command(arguments)"""
    #    _parent = parent.info_name if parent else ""
    messages = {"mtgk": '\n'.join(["  config".ljust(20, " ") + "Command to make configuration files",
                                   "  process".ljust(20, " ") + "Command to process data with configuration files",
                                   "  quick".ljust(20, " ") + "Command to quickly process data files",
                                   "  check".ljust(20, " ") + "Command to check the information on some file type",
                                   "  compute".ljust(20, " ") + "Command to compute certain quantities"]),
                "config":
                    '\n'.join(["  adcp".ljust(20, " ") + "Config file for adcp data. ",
                               "  platform".ljust(20, " ") + "Creates a platform.json file"]),
                "quick":
                    "  adcp".ljust(20, " ") + "Process adcp data.",

                "process": ("  [config_name]".ljust(20, " ")
                            + "Filename (path/to/file) of the configuration file."),
                "compute":
                    "  nav".ljust(20, " ")
                    + "Command to compute u_ship, v_ship, bearing from gsp data.",

                "nav": (
                        "  [file_name]".ljust(20, " ")
                        + "Filename (path/to/file, or expression) of the GPS files."

                ),
                "check": "  rti".ljust(20, " ") + "Print information on the rti .ens files. ",

                "adcp": "  [config_name]".ljust(20, " ")
                        + "Filename (path/to/file) for the new configuration file.",
                "platform": "  [filename]".ljust(20, " ")
                            + "Filename (path/to/file) for the new platform file.",
                }
    if group in messages:
        click.secho(messages[group], fg="white")


def _print_description(group):
    """print group/command descriptions"""
    messages = {"mtgk": (
        "Magtogoek is a Linux python package and command line application (CLI) for"
        " processing ocean data. At the moment, only Acoustic Doppler Current Profiler (ADCP)"
        " data can be processed. This package is developed by the Scientific"
        " Advice, Information and Support Branch at the Fisheries and Ocean Canada"
        " Maurice-Lamontagne Institute."),
        "config": (
            "The config command is used to create `.ini` configuration files or `.json`"
            " platform files. Configuration `.ini` files are used to write the desired"
            " processing configuration for different types of sensor (adcp, ctd, etc). Once"
            " created the configuration file   can be filled in any text editor or via"
            " optional arguments. Platform files are used to store platform metadata."
        ),
        "quick": "Quick way to process files.",
        "process": (
            "Command to execute the processing orders from a configuration file. If"
            " relative path where used in the configuration file, they are relative to directory"
            " where the command is called and not where the configuration file is located."
        ),
        "check": (
            "Print some raw files information. Only available for adcp RTI .ENS files."
        ),
        "adcp": (
            "\n"
            "        sonar\n"
            "        -----\n"
            "           os : OceanSurveyor (RDI)\n"
            "           wh : WorkHorse (RDI)\n"
            "           sv : SentinelV (RDI)\n"
            "           sw : SeaWatch (RTI)\n"
            "           sw_pd0 : SeaWatch (RTI in RDI pd0 file format)\n"
            "\n"
            "        quality control\n"
            "        ---------------\n"
            "           - velocity, amplitude, correlation, percentgood, roll, pitch, \n"
            "             side_lobe.\n"
            "           - Temperatures outside [-2, 32] Celsius. \n"
            "           - Pressures outside [0, 180] dbar.           \n"
            "        "
        ),
        "nav": (
            " Compute u_ship (eastward velocity), v_ship (northward velocity) and the bearing"
            " of the input gps data. The GPS input files can be nmea text file, gpx XML files or"
            " a netcdf files with `lon`, `lat` variables and `time` coordinates. Using the command"
            " `-w`, an averaging window can be use to smooth the computed navigation data."
            " A matplotlib plot is made after each computation."
        ),
        "platform": "Creates an empty platform.json file",
        "odf2nc": "Converts odf files to netcdf",
    }
    if group in messages:
        click.echo(click.wrap_text(messages[group], width=TERMINAL_WIDTH, initial_indent=''))


def _print_usage(group, parent):
    """print group/command usage"""
    _parent = parent.info_name if parent else ""

    if group == "mtgk":
        click.echo("  mtgk [config, process, quick, check]")
    if group == "config":
        click.echo("  mtgk config [adcp, platform,] [CONFIG_NAME] [OPTIONS]")
    if group == "platform":
        click.echo("  mtgk config platform [FILENAME] [OPTIONS]")
    if group == "process":
        click.echo("  mtgk process [CONFIG_FILE] [OPTIONS]")
    if group == "quick":
        click.echo("  mtgk quick [adcp, ] [FILENAME,...] [OPTIONS]")
    if group == "adcp":
        if _parent == "config":
            click.echo("  mtgk config adcp [CONFIG_NAME] [OPTIONS]")
        if _parent == "quick":
            click.echo("  mtgk quick adcp [INPUT_FILES] [SONAR] [YEARBASE] [OPTIONS]")
    if group == "check":
        click.echo("  mtgk check [rti,] [INPUT_FILES] ")
    if group == "rti":
        click.echo("  mtgk check rti [INPUT_FILES] ")
    if group == "nav":
        click.echo("  mtgk compute nav [INPUT_FILES] ")
