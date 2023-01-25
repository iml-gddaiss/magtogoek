import sys

import typing as tp
from pathlib import Path

from magtogoek import logger as l, PLATFORM_TYPES, SENSOR_TYPES
from magtogoek.platforms import PlatformMetadata, load_platform_metadata, default_platform_metadata
from magtogoek.utils import ensure_list_format

DEFAULT_PLATFORM_TYPE = "buoy"
CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]


class BaseProcessConfig:
    config_file: str = None
    sensor_type: str = None
    platform_type: str = None
    input_files: str = None
    platform_file: str = None
    platform_id: str = None
    sensor_id: str = None
    netcdf_output: tp.Union[str, bool] = None
    odf_output: tp.Union[str, bool] = None

    navigation_file: str = None

    merge_output_files: bool = None
    bodc_name: bool = None
    force_platform_metadata: bool = None

    make_figures: tp.Union[str, bool] = None
    make_log: bool = None
    odf_data: str = None
    metadata: dict = None
    platform_metadata: PlatformMetadata = None

    netcdf_path: str = None
    odf_path: str = None
    log_path: str = None
    figures_path: str = None
    figures_output: bool = None

    drop_empty_attrs: bool = False
    headless: bool = False

    def __init__(self, config_dict: dict = None):
        self.metadata: dict = {}

        if config_dict is not None:
            self._load_config_dict(config_dict)

        if isinstance(self.input_files, str):
            self.input_files = ensure_list_format(self.input_files)

        if len(self.input_files) == 0:
            raise ValueError("No adcp file was provided in the configfile.")

        self._load_platform_metadata()

        self.platform_type = self.platform_metadata.platform.platform_type

    def _load_config_dict(self, config: dict) -> dict:
        """Split and flattens"""
        for section, options in config.items():
            if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
                for option in options:
                    self.metadata[option] = config[section][option]
            else:
                for option in options:
                    self.__dict__[option] = config[section][option]

    def _load_platform_metadata(self):
        if self.platform_file is not None:
            if Path(self.platform_file).is_file():
                self.platform_metadata = load_platform_metadata(self.platform_file, self.platform_id)
            else:
                print( # This should not happen since it check when loading the config file.
                    f"platform_file, {self.platform_file}, not found\n"
                    f"Aborting"
                )
                sys.exit()

        else:
            if self.platform_type not in PLATFORM_TYPES:
                self.platform_type = DEFAULT_PLATFORM_TYPE
                l.warning(f"platform_type not specified or not one of {PLATFORM_TYPES}.")
                l.warning(f"platform_type set to `{self.platform_type}` for platform_type.")
            if not self.sensor_id:
                self.sensor_id = self.sensor_type + "_01"
            self.platform_metadata = default_platform_metadata(self.platform_type, self.sensor_id, self.sensor_type)

    def resolve_outputs(self):
        _resolve_outputs(self)


def _resolve_outputs(pconfig: BaseProcessConfig):
    """Figure out what outputs to make and their respective paths.

    ~~~ To whom ever reads the code that follows, I'm sorry. ~~~

    There is three parameters the user can set in the `pconfig`:

        [`netcdf_output`, `odf_output`,  `figure_output`]

    They can all have values of:
        - None
        - bool
        - `file name`
        - `path to directory`
        - `path to directory` + `file name`

    --- Logic Flow ---

    1. `default_path` and `default_filename` are defined. if the processing was done with
        a) a config file (.ini) they are respectively to path to the config file its name.
        b) the `quick` command, they are respectively the path to the first input file and its name.

    2. If both `netcdf_output`, `odf_output` are `False`, `nc_output` is set True.

    3. If `netcdf_output` is not `None` or `False`:
        a) Depending on the value of `netcdf_output`: True, a filename, a path to directory or a path to a filename,
           an output path is build using `default_path` and `default_filename` if needed.

        b) Updates `default_path` and `default_filename` using `netcdf_path` value.

    4. If `odf_output` is not `None` or `False`:
        a) Depending on the value of `odf_output`: True, a filename, a path to directory or a path to a filename,
           an output path is build using `default_path` if needed. ODF doesn't require a filename since it is built
           by default using metadata in the ODF file. Thus `default_filename` is not used here.

        b) If `netcdf_output` is False:
           Updates `default_path` using `odf_path` value. Updates `default_filename` if `odf_path` has a filename
           otherwise it stays the same..

    5. TODO FIGURE.

    6. `log_path` is made using `default_path` and `default_filename`.

    ...

    """

    if pconfig.config_file is not None:
        default_path, default_filename = Path(pconfig.config_file).parent, Path(pconfig.config_file).name
    else:
        default_path, default_filename = Path(pconfig.input_files[0]).parent, Path(pconfig.input_files[0]).name

    if not pconfig.odf_output and not pconfig.netcdf_output:
        pconfig.netcdf_output = True

    if pconfig.netcdf_output:
        _make_netcdf_output_path(pconfig, default_path, default_filename)
        default_path, default_filename = Path(pconfig.netcdf_path).parent, Path(pconfig.netcdf_path).stem

    if pconfig.odf_output:
        _make_odf_output_path(pconfig, default_path)
        if not pconfig.netcdf_output:
            default_path = Path(pconfig.odf_path).parent
            if not is_directory(pconfig.odf_path):
                default_filename = Path(pconfig.odf_path).stem

    if pconfig.make_figures:
        _make_figure_output_path(pconfig, default_path, default_filename)

    pconfig.log_path = str(default_path.joinpath(default_filename))


def _make_netcdf_output_path(pconfig: BaseProcessConfig, default_path: Path, default_filename: Path):

    if pconfig.netcdf_output is True:
        pconfig.netcdf_path = str(default_path.joinpath(default_filename))
    else:
        if is_filename(pconfig.netcdf_output):
            netcdf_path = default_path.joinpath(Path(pconfig.netcdf_output)).resolve()
        elif is_directory(pconfig.netcdf_output):
            netcdf_path = Path(pconfig.netcdf_output).joinpath(default_filename)
        elif parent_is_dir(pconfig.netcdf_output):
            netcdf_path = Path(pconfig.netcdf_output)
        else:
            raise ValueError(f'Path path to {pconfig.netcdf_output} does not exists.')

        pconfig.netcdf_path = str(netcdf_path)
        pconfig.netcdf_output = True


def _make_odf_output_path(pconfig: BaseProcessConfig, default_path: Path):

    if pconfig.odf_output is True:
        pconfig.odf_path = str(default_path)
    else:
        if is_filename(pconfig.odf_output):
            odf_path = default_path.joinpath(Path(pconfig.odf_output)).resolve()
        elif is_directory(pconfig.odf_output):
            odf_path = Path(pconfig.odf_output)
        elif parent_is_dir(pconfig.odf_output):
            odf_path = Path(pconfig.odf_output)
        else:
            raise ValueError(f'Path to {pconfig.odf_output} does not exists.')

        pconfig.odf_path = str(odf_path)
        pconfig.odf_output = True


def _make_figure_output_path(pconfig: BaseProcessConfig, default_path: Path, default_filename: Path):
    if pconfig.make_figures is True:
        pconfig.figures_output = True
        if pconfig.headless is True:
            pconfig.figures_path = str(default_path.joinpath(default_filename))
    else:
        _figures_output = Path(pconfig.make_figures)
        if Path(_figures_output.name) == _figures_output:
            _figures_path = default_path.joinpath(_figures_output).resolve()
        elif _figures_output.is_dir():
            _figures_path = _figures_output.joinpath(default_filename)
        elif _figures_output.parent.is_dir():
            _figures_path = _figures_output
        else:
            raise ValueError(f'Path to {_figures_output} does not exists.')

        pconfig.figures_path = str(_figures_path)
        pconfig.figures_output = True


def is_filename(path: str):
    return Path(path).name == path


def is_directory(path: str):
    return Path(path).is_dir()


def parent_is_dir(path: str):
    return Path(path).parent.is_dir()
