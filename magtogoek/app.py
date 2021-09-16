"""
Author: JeromeJGuay
Date: March 2 2021

This module contains the entry point for magtogoek CLI app `mtgk`.

Descriptions:
  FIXME

Usage:
    $ mtgk config [adcp, platform] [CONFIG_NAME] [OPTIONS]

    $ mtgk process [CONFIG_FILE]

    $ mtgk quick [adcp, ] [INPUT_FILES] [OPTIONS] FIXME has been modified. Probably not working.

    $ mtgk check [rti, ] [INPUT_FILES]



NOTE
-Maybe add a fonction for the navigation data. from csv ?
   -n nc_fileaname
   -c csv_filename
   -o output netcdf4 file name
   -l longitude_var_name latitude_var_name (2 args)
   -t time_dims_name
   -w length of the averaging window


"""
import typing as tp
from pathlib import Path
from subprocess import run as subp_run

import click

from magtogoek.app_options import adcp_options, add_options
from magtogoek.utils import is_valid_filename, json2dict
from magtogoek.version import VERSION

# ---------- Module or functions imported by commands ----------- #
# FIXME NOT UP TO DATE
# from magtogoek.configfile import make_configfile
# from magtogoek.platforms import make_platform_template
# from magtogoek.adcp.loader import load_adcp_binary
# from magtogoek.adcp.utils import Logger
# from magtogoek.adcp.process import process_adcp, quick_process_adcp
# --------------------------------------------------------------- #
# with open("../version.txt", "r") as f:


LOGO_PATH = "files/logo.json"

BASE_CONFIG_STRUCT = {
    "input_files": "INPUT",
    "platform_file": "INPUT",
    "platform_id": "INPUT",
    "sensor_id": "INPUT",
    "netcdf_output": "OUTPUT",
    "odf_output": "OUTPUT",
}
ADCP_CONFIG_STRUCT = {
    "yearbase": "ADCP_PROCESSING",
    "adcp_orientation": "ADCP_PROCESSING",
    "sonar": "ADCP_PROCESSING",
    "navigation_file": "ADCP_PROCESSING",
    "magnetic_declination": "ADCP_PROCESSING",
    "sensor_depth": "ADCP_PROCESSING",
    "fixed_sensor_depth": "ADCP_PROCESSING",
    "keep_bt": "ADCP_PROCESSING",
    "quality_control": "ADCP_QUALITY_CONTROL",
    "amplitude_threshold": "ADCP_QUALITY_CONTROL",
    "percentgood_threshold": "ADCP_QUALITY_CONTROL",
    "correlation_threshold": "ADCP_QUALITY_CONTROL",
    "horizontal_velocity_threshold": "ADCP_QUALITY_CONTROL",
    "vertical_velocity_threshold": "ADCP_QUALITY_CONTROL",
    "error_velocity_threshold": "ADCP_QUALITY_CONTROL",
    "sidelobes_correction": "ADCP_QUALITY_CONTROL",
    "bottom_depth": "ADCP_QUALITY_CONTROL",
    "depth_range": "ADCP_QUALITY_CONTROL",
    "pitch_threshold": "ADCP_QUALITY_CONTROL",
    "roll_threshold": "ADCP_QUALITY_CONTROL",
    "leading_trim": "ADCP_QUALITY_CONTROL",
    "trailing_trim": "ADCP_QUALITY_CONTROL",
    "motion_correction_mode": "ADCP_QUALITY_CONTROL",
    "merge_output_files": "ADCP_OUTPUT",
    "bodc_name": "ADCP_OUTPUT",
    "drop_percent_good": "ADCP_OUTPUT",
    "drop_correlation": "ADCP_OUTPUT",
    "drop_amplitude": "ADCP_OUTPUT",
    "make_figures": "ADCP_OUTPUT",
    "make_log": "ADCP_OUTPUT",
}

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


def _print_info(ctx, callback):
    """Show command information"""
    if callback:
        subp_run(["printf", "\e[8;40;" + str(TERMINAL_WIDTH + 1) + "t"])
        click.clear()
        _print_logo(logo_path=LOGO_PATH, group=ctx.info_name, version=VERSION)
        click.secho("\nDescriptions:", fg="red")
        _print_description(ctx.info_name)
        click.secho("\nUsage:", fg="red")
        _print_usage(ctx.info_name, ctx.parent)
        if ctx.info_name in ["mtgk", "config", "process", "quick", "check"]:
            click.secho("\nCommands:", fg="red")
        else:
            click.secho("\nArguments:", fg="red")
        _print_arguments(ctx.info_name, ctx.parent)
        click.secho("\nOptions", fg="red")
        click.echo("  Use  -h/--help to show the options")
        click.echo("\n")
        exit()


# --------------------------- #
#      mtgk entry point       #
# --------------------------- #
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
def magtogoek(info):
    pass


# --------------------------- #
#        mtgk command         #
# --------------------------- #
@magtogoek.command("process")
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
@click.argument("config_file", metavar="[config_file]", type=click.Path(exists=True))
def process(config_file, info):
    """Process data by reading configfile"""
    # NOTE This could be update as a group with sensor specific command.
    # Doing so would allow the user to pass config options. The load_configfile
    # command is already able to take uptaded_params options and update de configile.
    # The same options (or nearly all the same )as for adcp_config could be use.
    from configparser import ParsingError

    from magtogoek.configfile import load_configfile

    try:
        config = load_configfile(config_file)
    except ParsingError:
        print("Failed to open the given configfile.\n mtgk process aborded.")
        exit()

    if config["HEADER"]["sensor_type"] == "adcp":
        from magtogoek.adcp.process import process_adcp

        process_adcp(config)


# --------------------------- #
#        mtgk groups          #
# --------------------------- #
@magtogoek.group("config", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
def config(info):
    """Make configuration files or platform files"""
    pass


@magtogoek.group("quick", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
def quick(info):
    """Quick data process without configfile"""
    pass


@magtogoek.group("check", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
def check(info):
    """Get info on raw data files"""
    pass


@magtogoek.group("compute", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
def compute(info):
    """Command to compute certain quantities."""
    pass


# --------------------------- #
#       config command        #
# --------------------------- #
@config.command("platform")
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
@click.argument("filename", metavar="[filename]", type=str)
@click.pass_context
def config_platform(ctx, filename, info):
    from magtogoek.platforms import make_platform_template

    filename = is_valid_filename(filename, ext=".json")
    make_platform_template(filename)
    click.echo(click.style(f"Platform file created for -> {filename}", bold=True))


@config.command("adcp")
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
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
    ctx, config_name, **options,
):
    """Command to make an adcp config files. The [OPTIONS] can be added
    before or after the [config_name]."""
    from magtogoek.configfile import make_configfile

    _print_passed_options(options)

    # check if a file already exists and format the `.ini` extension.
    config_name = is_valid_filename(config_name, ext=".ini")

    config_params = _format_options_for_configfile("adcp", options)

    make_configfile(
        filename=config_name, sensor_type="adcp", config_params=config_params
    )

    click.echo(
        click.style(
            f"Config file created for adcp processing -> {config_name}", bold=True
        )
    )


# --------------------------- #
#       quick command         #
# --------------------------- #
@quick.command("adcp")
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
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
    type=click.Choice(["ship", "mooring"]),
    help="Used for Proper BODC variables names",
    default="mooring",
)
@click.pass_context
def quick_adcp(
    ctx, input_files, sonar, yearbase, **options,
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
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
@click.argument(
    "input_files",
    metavar="[input_files]",
    nargs=-1,
    type=click.Path(exists=True),
    required=True,
)
@click.pass_context
def check_rti(ctx, input_files, **options):
    """Prints info about RTI .ENS files."""
    from magtogoek.adcp.rti_reader import RtiReader

    RtiReader(input_files).check_files()


@compute.command("nav", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--info", is_flag=True, callback=_print_info, help="Show command information"
)
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
def navigation(ctx, input_files, **options):
    """Command to compute u_ship, v_ship, bearing from gsp data."""
    from magtogoek.navigation import compute_navigation

    compute_navigation(
        filenames=input_files,
        output_name=options["output_name"],
        window=options["window"],
    )


# ------------------------ #
#        Functions         #
# ------------------------ #
def _format_options_for_configfile(sensor_type, options):
    """format options into the  configfile struture"""
    options = _convert_options_names(sensor_type, options)

    if sensor_type == "adcp":
        configfile_struct = {**BASE_CONFIG_STRUCT, **ADCP_CONFIG_STRUCT}
        if not options["bottom_depth"]:
            options["bottom_depth"] = ""
        options["platform_file"] = options["platform"][0]
        options["platform_id"] = options["platform"][1]
        options["sensor_id"] = options["platform"][2]
        del options["platform"]

    updated_params = dict()
    for section in set(configfile_struct.values()):
        updated_params[section] = dict()

    for option, value in options.items():
        if value is not None:
            updated_params[configfile_struct[option]][option] = value

    return updated_params


def _convert_options_names(sensor_type, options):
    """Translate options name.
    Translate options anmes from the commad names to
    the parameters name used by magtogoek."""

    for key, item in OPTIONS_NAME_TRANSLATOR[sensor_type].items():
        options[key] = options.pop(item)

    return options


def _print_passed_options(ctx_params: tp.Dict):
    """print pass and default options/paramsd"""
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


def _print_logo(
    logo_path: str = "files/logo.json", group: str = "", version: str = "unavailable",
):
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


def _print_arguments(group, parent):
    """print group(command) command(arguments)"""
    _parent = parent.info_name if parent else ""
    if group == "mtgk":
        click.secho(
            "  config".ljust(20, " ") + "Command to make configuration files",
            fg="white",
        )
        click.secho(
            "  process".ljust(20, " ")
            + "Command process data with configuration files",
            fg="white",
        )
        click.secho(
            "  quick".ljust(20, " ") + "Command to quickly process data files",
            fg="white",
        )
        click.secho(
            "  check".ljust(20, " ")
            + "Command to check the informations on some file type.",
            fg="white",
        )
        click.secho(
            "  compute".ljust(20, " ") + "Command to compute certain quantities.",
            fg="white",
        )
    if group == "config":
        click.secho("  adcp".ljust(20, " ") + "Config file for adcp data. ", fg="white")
        click.secho(
            "  platform".ljust(20, " ") + "Creates a platform.json file", fg="white"
        )

    if group == "quick":
        click.secho("  adcp".ljust(20, " ") + "Process adcp data. ", fg="white")

    if group == "process":
        click.secho(
            "  [config_name]".ljust(20, " ")
            + "Filename (path/to/file) of the configuration file.",
            fg="white",
        )

    if group == "compute":
        click.secho(
            "  nav".ljust(20, " ")
            + "Command to compute u_ship, v_ship, bearing from gsp data.",
            fg="white",
        )

    if group == "nav":
        click.secho(
            "  [file_name]".ljust(20, " ")
            + "Filename (path/to/file, or expression) of the GPS files.",
            fg="white",
        )

    if group == "check":
        click.secho(
            "  rti".ljust(20, " ") + "Print information on the rti .ens files. ",
            fg="white",
        )

    if group == "adcp":
        click.secho(
            "  [config_name]".ljust(20, " ")
            + "Filename (path/to/file) for the new configuration file.",
            fg="white",
        )

    if group == "platform":
        click.secho(
            "  [filename]".ljust(20, " ")
            + "Filename (path/to/file) for the new platform file.",
            fg="white",
        )


def _print_description(group):
    """print group/command desciptions"""
    if group == "mtgk":
        click.echo("""FIXME""")
    if group == "config":
        click.echo(
            """  The config command is used to create `.ini` configuration files or `.json` 
  platform files. Configuration `.ini` files are used to write the desired 
  processing configuration for different types of sensor (adcp, ctd, etc). Once
  created the configuration file   can be filled in any text editor or via
  optional arguments. Platform files are used to store platform metedata.""",
        )
    if group == "quick":
        click.echo("""Quick way to process files.""")
    if group == "process":
        click.echo(
            """  Command to execute the processing orders from a configuration file. If
  relative path where used in the configuration file, they are relative to directory
  where the command is called and not where the configuration file is located."""
        )
    if group == "check":
        click.echo(
            """Print somes raw files informations. Only available for adcp RTI .ENS files."""
        )
    if group == "adcp":
        click.echo(
            """
        sonar
        -----
           os : OceanSurveillor (RDI)
           wh : WorkHorse (RDI)
           sv : SentinelV (RDI)
           sw : SeaWatch (RTI)
           sw_pd0 : SeaWatch (RTI in RDI pd0 file format)

        quality_control
        ---------------
           Velocities in any direction are set to NaN if greater than 15 meter
           per seconds.
           Failing amplitude, correlation and percentgood, roll, pitch,
           horizontal/vertical velocities test returns a flag_value of 3.
           Temperatures outside [-2, 32] Celcius value outside and pressures
           outide [0, 180] dbar value or depths below sidelobe depth limite
           have a flag_value of 4.
        """
        )
    if group == "nav":
        click.echo(
            """ Compute u_ship (eastward velocity), v_ship (northward velocity) and the bearing
of the input gps data. The GPS input files can be nmea text file, gpx XML files or
a netcdf files with `lon`, `lat` variables and `time` coordinates. Using the command `-w`, an averaging window can be use to smooth the computed navigation data. A matplotlib plot is made after each computation."""
        )

    if group == "platform":
        click.echo("""Creates an empty platform.json file""")  # FIXME


def _print_usage(group, parent):
    """print group/command usage"""
    _parent = parent.info_name if parent else ""

    if group == "mtgk":
        click.echo("  mtgk [config, process, quick, check]")
    if group == "config":
        click.echo("  mtgk config [adcp, platform,] [CONFIG_NAME] [OPTIONS]")
    if group == "platform":
        click.echo(f"  mtgk config platform [FILENAME] [OPTIONS]")
    if group == "process":
        click.echo("  mtgk process [CONFIG_FILE] [OPTIONS]")
    if group == "quick":
        click.echo("  mtgk quick [adcp, ] [FILENAME,...] [OPTIONS]")
    if group == "adcp":
        if _parent == "config":
            click.echo(f"  mtgk config adcp [CONFIG_NAME] [OPTIONS]")
        if _parent == "quick":
            click.echo(f"  mtgk quick adcp [INPUT_FILES] [SONAR] [YEARBASE] [OPTIONS]")
    if group == "check":
        click.echo(f"  mtgk check [rti,] [INPUT_FILES] ")
    if group == "rti":
        click.echo(f"  mtgk check rti [INPUT_FILES] ")
    if group == "nav":
        click.echo(f"  mtgk compute nav [INPUT_FILES] ")
