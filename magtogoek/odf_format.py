"""
Author : jerome.guay@protonmail.com
Date : 29-04-2021

Module to open and write  ODF (Ocean Data Format) files used by Maurice Lamontagne Institute.

ODF class method:
----------
read()

save()

to_dataset()

add_buoy_instrument()

add_general_cal()

add_polynomial_cal()

add_compass_cal()

add_history()

add_parameter()

from_dataframe()

Notes
-----
ODF object structure:
    Headers are stored as dictionaries containing. They are either direction attributes or store
    in one of the following attributes .buoy_instrument, .general_cal, .polynomial_cal, .compass, .history
    or .parameter.
    Data are pandas dataframe. ODF.data.
Writing ODF files.
    Using .save(filename), the ODF file will be written.
    - Headers keys are always printed in upper case.
    Headers values can be one of: int, float, str, list, tuple, or list(tuple).
      - floats are printed with the number of significant digit specified by the global variable PRECISION.
      - list elements are printed with the same headers key.
      - coefficients, directions and corrections items need to be stored as tuple for the correct formatting
        field width of 12 and 8 decimals precision.
"""
import logging
import typing as tp
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.utils import get_files_from_expression

NA_REP = "null"  # There should not be any null value in a odf file.
SPACE = " "  # single space
INDENT = "  "  # double space
NEWLINE = "\n"  # new line
PRECISION = 6

REPEATED_HEADERS = [
    "buoy_instrument",
    "general_cal",
    "polynomial_cal",
    "compass_cal",
    "history",
    "parameter",
]
NC_TIME_ENCODING = {
    "units": "seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}


def get_headers_default():
    return dict(
        odf=dict(file_specification=""),
        cruise=dict(
            country_institute_code="",
            cruise_number="",
            organization="",
            chief_scientist="",
            start_date="",
            end_date="",
            platform="",
            cruise_name="",
            cruise_description="",
        ),
        event=dict(
            data_type="",
            event_number="",
            event_qualifier1="",
            event_qualifier2="",
            creation_date="",
            orig_creation_date="",
            start_date_time="",
            end_date_time="",
            initial_latitude=None,
            initial_longitude=None,
            end_latitude=None,
            end_longitude=None,
            min_depth=None,
            max_depth=None,
            sampling_interval=None,
            sounding=None,
            depth_off_bottom=None,
            event_comments=[],
        ),
        buoy=dict(
            name="",
            type="",
            model="",
            height="",
            diameter="",
            weight="",
            description="",
        ),
        plankton=dict(
            water_volume="",
            volume_method="",
            lrg_plankton_removed="",
            collection_method="",
            mesh_size="",
            phase_of_daylight="",
            collector_dplmt_id="",
            collector_sample_id="",
            procedure="",
            preservation="",
            storage="",
            meters_sqd_flag="",
            plankton_comments=[],
        ),
        meteo=dict(
            air_temperature=None,
            atmospheric_pressure=None,
            wind_speed=None,
            wind_direction=None,
            sea_state=None,
            cloud_cover=None,
            ice_thickness=None,
            meteo_comments=[],
        ),
        instrument=dict(inst_type="", model="", serial_number="", description="",),
        quality=dict(quality_date="", quality_tests=[], quality_comments=[],),
        record=dict(
            num_calibration=None,
            num_swing=None,
            num_history=None,
            num_cycle=None,
            num_param=None,
        ),
    )


def _get_repeated_headers_default():
    return dict(
        buoy_instrument=dict(
            name="",
            type="",
            model="",
            serial_number="",
            description="",
            inst_start_date_time="",
            inst_end_date_time="",
            buoy_instrument_comments=[],
            sensors=[],
        ),
        general_cal=dict(
            parameter_code="",
            calibration_type="",
            calibration_date="",
            application_date="",
            number_coefficients=0,
            coefficients=(),  # NOTE for i in number_coefficients ' %12.8e '
            calibration_equation=[],
            calibration_comments=[],
        ),
        polynomial_cal=dict(
            parameter_code="",
            calibration_date="",
            application_date="",
            number_coefficients=0,
            coefficients=(),  # NOTE for i in number_coefficients ' %12.8e '
        ),
        compass_cal=dict(
            parameter_code="",
            calibration_date="",
            application_date="",
            # NOTE for j = 0:8 % 12.8e   % 12.8e   % 12.8e   % 12.8e, [(4*j) +1:(4*j)+4] # 8 FW.DP
            directions=(),
            corrections=(),
        ),
        history=dict(creation_date="", process=[]),
        parameter=dict(
            type="",
            name="",
            units="",
            code="",
            null_value=0,
            print_field_width=10,
            print_decimal_places=4,
            angle_of_section=0,
            magnetic_variation=0,
            depth=0,
            minimum_value=0,
            maximum_value=0,
            number_valid=0,
            number_null=0,
        ),
    )


class Odf:
    """
    ODF class object can make, read and write ODF (ocean data format) files.

    Useful methods
    ---------------
    read()

    save()

    to_dataset()

    add_buoy_instruments()

    add_compass_cal()

    add_general_cal()

    add_history()

    add_parameter()

    from_dataframe()

    Notes
    -----
    ODF object structure:
        Headers are stored as dictionaries containing. They are either direction attributes or store
        in one of the following attributes .buoy_instrument, .general_cal, .polynomial_cal, .compass, .history
        or .parameter.
    Data are pandas dataframe. ODF.data.
        Writing ODF files.
        Using .save(filename), the ODF file will be written.
        - Headers keys are always printed in upper case.
        Headers values can be one of: int, float, str, list, tuple, or list(tuple).
        - floats are printed with the number of significant digit specified by the global variable PRECISION.
        - list elements are printed with the same headers key.
        - coefficients, directions and corrections items need to be stored as tuple for the correct formatting
          field width of 12 and 8 decimals precision.
    """

    def __init__(self):
        self.odf = get_headers_default()["odf"]
        self.cruise = get_headers_default()["cruise"]
        self.event = get_headers_default()["event"]
        self.buoy = get_headers_default()["buoy"]
        self.plankton = get_headers_default()["plankton"]
        self.meteo = get_headers_default()["meteo"]
        self.instrument = get_headers_default()["instrument"]
        self.quality = get_headers_default()["quality"]
        self.record = get_headers_default()["record"]
        self.buoy_instrument = dict()
        self.general_cal = dict()
        self.polynomial_cal = dict()
        self.compass_cal = dict()
        self.history = dict()
        self.parameter = dict()
        self.data = pd.DataFrame()

    def __repr__(self):
        s = "<odf_format.ODF>" + NEWLINE
        s += "headers:" + NEWLINE

        for h in list(get_headers_default().keys()):
            if h in self.__dict__:
                if any(self.__dict__[h].values()):
                    s += h + NEWLINE
                else:
                    s += h + "(empty)" + NEWLINE

        for h in REPEATED_HEADERS:
            if self.__dict__[h]:
                s += h + f" ({len(self.__dict__[h])})" + NEWLINE
            else:
                s += h + " (empty)" + NEWLINE

        s += "data:" + NEWLINE
        if self.data.empty:
            s += SPACE + "(empty)" + NEWLINE

        else:
            s += SPACE + f"pandas.Dataframe of shape {self.data.shape}"

        return s

    def read(self, filename: str):
        """Read ODF files.
        The ODF headers section in nested dictionaries in ODF.headers and
        ODF.parameters. The data is store in a pandas.DataFrame.

        Notes
        -----
        All items values are stored in list. After all the headers are read, list of length one
        are converted to int, float or str.

        Calibration coefficients, directions and corrections are stored in tuple.
        """
        self.__init__()
        is_data = False
        current_header = {}  # used to be None, should work
        parameters_code = []
        repeated_header_counters = dict(
            parameter=0,
            buoy_instrument=0,
            general_cal=0,
            polynomial_cal=0,
            compass_cal=0,
            history=0,
        )
        with open(filename, "r", encoding="ISO-8859-1") as f:
            while not is_data:
                line = f.readline().split(",")[0]

                if not line:
                    break

                if line.startswith("  "):
                    key, item = _get_key_and_item(line)
                    if key in current_header:
                        if isinstance(current_header[key], list):
                            current_header[key].append(item)
                        else:
                            current_header[key] = [item]
                    else:
                        current_header[key] = [item]

                elif " -- DATA --" in line:
                    is_data = True

                elif any([_h.upper() + "_HEADER" in line for _h in REPEATED_HEADERS]):
                    for h in REPEATED_HEADERS:
                        if h.upper() + "_HEADER" in line:
                            header_key = h + "_" + str(repeated_header_counters[h])
                            repeated_header_counters[h] += 1
                            self.__dict__[h][header_key] = _get_repeated_headers_default()[h]
                            current_header = self.__dict__[h][header_key]
                else:
                    header_key = "_".join(line.split("_")[:-1]).lower()
                    current_header = self.__dict__[header_key]

            for _, section in self.__dict__.items():
                _reshape_header_items(section)

            for p in list(self.parameter.keys()):
                code = self.parameter[p]["code"]
                self.parameter[code] = self.parameter.pop(p)

                parameters_code.append(code)

            for bi in list(self.buoy_instrument.keys()):
                name = self.buoy_instrument[bi]["name"]
                self.buoy_instrument[name] = self.buoy_instrument.pop(bi)

            for cal_headers in ["general_cal", "polynomial_cal", "compass_cal"]:
                for cal in list(self.__dict__[cal_headers].keys()):
                    code = self.__dict__[cal_headers][cal]["parameter_code"]
                    self.__dict__[cal_headers][code] = self.__dict__[cal_headers].pop(cal)

            if is_data:
                self.data = pd.read_csv(
                    f,
                    names=parameters_code,
                    decimal=".",
                    delim_whitespace=True,
                    quotechar="'",
                )
            else:
                logging.error(f"Data section not found in ODF {filename}")

        return self

    def save(self, filename: str = None):
        """Save file

        Parameters
        ---------_
        filename :
            path/to/filename. filename will overwrite the value at Odf.odf['file_specification']"""
        filename = Path(filename)

        self.odf["file_specification"] = filename.name

        filename = filename.with_suffix(".ODF")

        with open(filename, "w+", encoding="ISO-8859-1") as f:
            f.write(self._headers_string_format())
            f.write(SPACE + "-- DATA --" + NEWLINE)
            self._write_data(buf=f)

    def to_dataset(self, dims: tp.Union[str, tp.List[str], tp.Tuple[str]] = None, time: tp.Union[str, tp.List[str], tp.Tuple[str]] = None):
        """
        Parameters
        ----------
        dims :
           Dimensions names. If one of the dimensions is named `SYTM_01`, it will be
           converted to datetime64.
        time :
            Specify which variable is to be converted into datetime64. The variable
            "SYTM_01" will be converted to datetime64 automatically.
        """
        logging.info(f'to_dataset params. dims: {dims}, time: {time}')
        if isinstance(dims, tuple):
            dims = list(dims)

        if isinstance(dims, list):
            if len(dims) == 0:
                dims = None

        _time = {'SYTM_01'}
        if time is not None:
            for t in time:
                _time.update({t})

        for t in _time:
            if t in self.data:
                try:
                    self.data[t] = pd.to_datetime(self.data[t], format="%d-%b-%Y %H:%M:%S.%f")
                    print(f"{t} converted to time.")
                except ValueError:
                    print(f'Not able to format {t} to time.')

        if dims is not None:
            [dims.remove(dim) for dim in dims if dim not in self.data]
            if len(dims) > 0:
                print(f"Dimensions: {dims}")
                dataset = xr.Dataset.from_dataframe(self.data.set_index(dims))
            else:
                print("Dimensions not found in in ODF.")
                print(f"Avaiable ODF variables: {list(self.data.keys())}")
                dataset = xr.Dataset.from_dataframe(self.data)
        else:
            dataset = xr.Dataset.from_dataframe(self.data)

        for p in self.parameter:
            dataset[p].attrs.update(self.parameter[p])

        variables = list(dataset)
        new_varname = {}
        for index, variable in enumerate(variables):
            if "QQQQ" in variable:
                new_varname[variable] = variables[index - 1].split('_')[0] + "_QC"

        dataset = dataset.rename(new_varname)

        if 'SYTM_01' in dataset.coords:
            [dataset['SYTM_01'].attrs.pop(key) for key in NC_TIME_ENCODING if key in dataset['SYTM_01'].attrs]
            dataset['SYTM_01'].encoding = NC_TIME_ENCODING

        history = {}
        for i, k in enumerate(self.history):
            process = self.history[k]["process"]
            if not isinstance(self.history[k]['process'], list):
                process = [self.history[k]['process']]
            history = {f"process_{i}": "\n".join([self.history[k]["creation_date"]] + process)}

        dataset.attrs = {
            **self.event,
            **self.cruise,
            **self.buoy,
            **self.instrument,
            **history,
        }

        return dataset

    def add_polynomial_cal(self, code: str, items: dict = None):
        """Add a polynomial cal headers to ODF.polynomial_cal

        Parameters
        ----------
        code :
            Name(key) for the parameter code.
        items :
            Dictionary containing parameter header items.
        """
        if items is None:
            items = {}
        self.polynomial_cal[code] = _get_repeated_headers_default()["polynomial_cal"]
        self.polynomial_cal[code]["code"] = code
        self.polynomial_cal[code].update(items)

    def add_general_cal(self, code: str, items: dict = None):
        """Add a general cal headers to ODF.general_cal

        Parameters
        ----------
        code :
            Name(key) for the parameter code.
        items:
            Dictionary containing parameter header items.
        """
        if items is None:
            items = {}
        self.general_cal[code] = _get_repeated_headers_default()["general_cal"]
        self.general_cal[code]["code"] = code
        self.general_cal[code].update(items)

    def add_compass_cal(self, code: str, items: dict = None):
        """Add a compass cal headers to ODF.compass_cal

        Parameters
        ----------
        code :
            Name(key) for the parameter code.
        items :
            Dictionary containing compass cal header items.
        """
        if items is None:
            items = {}
        self.compass_cal[code] = _get_repeated_headers_default()["compass_cal"]
        self.compass_cal[code]["code"] = code
        self.compass_cal[code].update(items)

    def add_buoy_instrument(self, name: str, items: dict = None):
        """Add a buoy instrument headers to ODF.instruments.

        Parameters
        ----------
        name :
            Name(key) for the instrument header.
        items :
            Dictionary containing parameter header items.
        """
        if items is None:
            items = {}
        self.buoy_instrument[name] = _get_repeated_headers_default()["buoy_instrument"]
        self.buoy_instrument[name]["name"] = name
        self.buoy_instrument[name].update(items)

    def add_parameter(
        self,
        code: str,
        data: tp.Union[list, np.ndarray],
        null_value: tp.Union[int, float],
        items: tp.Dict = None,
        qc_mask: np.ndarray = None,
    ):
        """Add a the parameter to ODF.parameters and the data to ODF.data.

        Computes `number_valid`, `number_null`, `minimum_value` and `maximum_value` from
        the data and a provided `null_value` in `items`.

        Parameters
        ----------
        code :
            Name(key) for the parameter code.
        data :
            1-D sequence of data. Each parameters must have the same length.
        null_value :
            `null_value` to compute  `number_valid` and `number_null`.
        items :
             dictionary containing the parameters metadata.
        qc_mask :
            Boolean mask use to compute min and max values.

        """
        if items is None:
            items = {}

        data = np.asarray(data)
        _null_value = null_value
        if code == "SYTM_01":
            _null_value = pd.Timestamp(null_value)
        data[~np.isfinite(data)] = _null_value

        self.parameter[code] = _get_repeated_headers_default()["parameter"]
        self.parameter[code].update(items)
        self.parameter[code]["code"] = code
        self.parameter[code]["null_value"] = null_value
        self.data[code] = data
        self.parameter[code]["number_valid"] = len(self.data[code])

        self._compute_parameter_attrs(code, qc_mask)

    def _compute_parameter_attrs(self, parameter: str, qc_mask: np.ndarray = None):
        """Compute `number_valid`, `number_null`, `minimum_value` and `maximum_value` from
        the data and the "null_value" in `parameter[parameter]`.
        """
        mask = np.ones(self.data[parameter].shape).astype(bool)

        if "QQQQ" not in parameter:
            null_value = self.parameter[parameter]["null_value"]
            n_null = (self.data[parameter] == null_value).sum().item()
            self.parameter[parameter]["number_null"] = n_null
            self.parameter[parameter]["number_valid"] -= n_null

            mask = (self.data[parameter] != null_value).values
            if qc_mask is not None:
                mask &= qc_mask

        self.parameter[parameter]["minimum_value"] = (
            self.data[parameter].where(mask).min()
        )
        self.parameter[parameter]["maximum_value"] = (
            self.data[parameter].where(mask).max()
        )

    def from_dataframe(
        self,
        dataframe: tp.Type[pd.DataFrame],
        null_values: tp.Union[int, float, list, tuple, dict],
        items: None,
    ):
        """Add data and parameters from a pandas.dataframe. Columns names are used for
        the new parameters code.

        Parameters
        ----------
        dataframe :
            The data to be added to the ODF.

        null_values :
            Value used for missing or null value in data. From this value `number_valid`,
            `number_null` will be computed. If a single value is provided, it will be
            applied to all the data. A dictionary of with matching keys matching dataframe
            columns or list and tuple can be pass with different null_value but all null_value
            must have the same length as the number of columns in the dataframe.
        items :
            Dictionary containing parameter header items. Keys must be the parameters code.

        """
        if items is None:
            items = {}

        if isinstance(dataframe, pd.DataFrame):
            dataframe = dataframe.reset_index(drop=True)
        else:
            raise TypeError("dataframe must be a pandas.DataFrame")

        _null_values = _get_null_values(dataframe.columns, null_values, items)

        for code in dataframe.columns:
            self.add_parameter(code, dataframe[code].values, _null_values[code], items[code])

        self.record = self._make_record()

        return self

    def add_history(self, items: dict = None):
        """Add a history header

        Parameters
        ----------
        items :
            Dictionary containing two items; 'creation_date' and 'process'.
            'creation_date' should be formatted like '01-JAN-2000 00:00:00.00
            'process' should a list of string.

        """
        if items is None:
            items = {}
        header_name = "history_" + str(len(self.history) + 1)
        self.history[header_name] = dict(_get_repeated_headers_default()["history"])
        self.history[header_name].update(items)
        if not self.history[header_name]["creation_date"]:
            self.history[header_name]["creation_date"] = odf_time_format(
                pd.Timestamp.now()
            )

    def _headers_string_format(self):
        s = ""
        for h in ["odf", "cruise", "event", "buoy", "plankton", "meteo", "instrument"]:
            if h in self.__dict__:
                if any(self.__dict__[h].values()):
                    s += _format_headers(h, self.__dict__[h])

        for _, header in self.buoy_instrument.items():
            s += _format_headers("buoy_instrument", header)

        if any(self.__dict__["quality"].values()):
            s += _format_headers("quality", self.__dict__["quality"])

        for h in ["general_cal", "polynomial_cal", "compass_cal", "history"]:
            for _, header in self.__dict__[h].items():
                s += _format_headers(h, header)

        for _, header in self.parameter.items():
            s += _format_headers("parameter", header)

        s += _format_headers("record", self._make_record())

        return s

    def _make_record(self):
        return dict(
            num_calibration=len(self.polynomial_cal),
            num_swing=len(self.compass_cal),
            num_history=len(self.history),
            num_cycle=len(self.data),
            num_param=len(self.parameter),
        )

    def _write_data(self, buf):
        """Write data to a buffer.

        See pandas.DataFrame.to_string

        """
        self.data.reset_index(inplace=True, drop=True)
        valid_data = []
        for key in self.parameter:
            if key in self.data.keys():
                valid_data.append(key)

        formats = {}
        for vd in valid_data:
            padding = self.parameter[vd]["print_field_width"]
            decimal_places = self.parameter[vd]["print_decimal_places"]
            if self.data[vd].dtype == int:
                formats[vd] = lambda x, p=padding: SPACE + str(x).rjust(p, SPACE)

            elif self.data[vd].dtypes == np.dtype("<M8[ns]"):
                formats[vd] = lambda x, p=padding: (SPACE + ("'" + odf_time_format(x) + "'").rjust(p, SPACE))

            elif self.data[vd].dtypes == np.floating:
                formats[vd] = lambda x, p=padding, d=decimal_places: (SPACE + f"{x:.{d}f}".rjust(p, SPACE))

        self.data.to_string(buf=buf, formatters=formats, header=False, index=False, na_rep=NA_REP)


def _get_null_values(
    codes: list, null_values: tp.Union[int, float, list, tuple], items: dict
) -> dict:
    _null_values = {}
    """
    """
    if isinstance(null_values, (float, int)):
        _null_values = dict.fromkeys(codes, null_values)
    elif isinstance(null_values, (list, tuple)):
        if len(null_values) != len(codes):
            raise ValueError(
                f"`null_values` length ({len(null_values)}) doesn't match"
                + " the number of columns ({len(dataframe.columns)})in the dataframe."
            )
        else:
            _null_values = dict(zip(codes, null_values))
    else:
        for key, params_items in items.items():
            if "null_value" in params_items:
                if not isinstance(params_items["null_value"](int, float)):
                    _null_values[key] = params_items["null_value"]
                else:
                    raise ValueError(f"[{key}][`null_values`] must be a `int` or `float`.")
            else:
                raise ValueError(f"[{key}] is missing a `null_values` key and value.")
    return _null_values


def _format_headers(name: str, header: dict) -> str:
    """

    Parameters
    ----------
    name
    header

    Returns
    -------

    """
    s = name.upper() + "_HEADER," + NEWLINE
    for key, value in header.items():
        if isinstance(value, pd.Timestamp):
            value = odf_time_format(value)
        if isinstance(value, str):
            s += INDENT + key.upper() + " = " + f"'{value}'," + NEWLINE
        elif isinstance(value, (int, np.integer)):
            s += INDENT + key.upper() + " = " + f"{value}," + NEWLINE
        elif isinstance(value, (float, np.floating)):
            s += INDENT + key.upper() + " = " + f"{value:.{PRECISION}f}," + NEWLINE
        elif isinstance(value, list):
            parent = INDENT + f"{key.upper()} = "
            s += _format_list(value, parent)
        elif isinstance(value, tuple):
            s += (
                INDENT
                + key.upper()
                + " = "
                + "".join([f"{v:{12}.{8}f}" for v in value])
                + ","
                + NEWLINE
            )

        elif not value:
            s += INDENT + key.upper() + " = ''" + "," + NEWLINE
        else:
            print("Could not format", name, key, value, type(value))

    return s


def _format_list(_list: list, parents: str) -> str:
    s = ""
    if len(_list) == 0:
        s += parents + "''," + NEWLINE
        return s
    else:
        for value in _list:
            if isinstance(value, tuple):
                s += (
                    parents
                    + " ".join([f"{v:{12}.{8}f}" for v in value])
                    + ","
                    + NEWLINE
                )
            else:
                s += parents + "'" + f"{value}'," + NEWLINE
        return s


def _get_key_and_item(line):
    """ Return key and item from a line. Split of `=`."""
    key, item = line.split("=", 1)
    key, item = key.strip().lower(), item.strip()
    if not item:
        pass
    elif not any(char in item for char in [":", "'", " "]):
        item = eval(item)
    else:
        item = item.strip().strip("'")
    return key, item


def _reshape_header_items(header):
    """Replace list of length one by the value it contains.

    The elements of items that keys are in [`coefficients`, `directions`, `corrections`] are
    split into tuple and are evaluated.

    """
    for key, item in header.items():
        if isinstance(item, dict):
            _reshape_header_items(item)

        elif isinstance(item, list):
            if key in ["coefficients", "directions", "corrections"]:
                for i in range(len(item)):
                    header[key][i] = tuple(map(eval, str(header[key][i]).split()))
            if len(item) == 1:
                header[key] = item[0]


def odf_time_format(time):
    """Convert to odf time format

    Parameters
    ----------
    time :
        Either pandas or datetime datetime format.

    Returns
    -------
    string formatted time.
    """
    try:
        odf_time = pd.Timestamp(time).strftime("%d-%b-%Y %H:%M:%S.%f").upper()[:-4]
    except ValueError:
        odf_time = "17-NOV-1858 00:00:00.00"
    return odf_time


def convert_odf_to_nc(
        input_files: tp.Union[str, tp.Tuple[str], tp.List[str]] = None,
        output_name: str = None,
        dims: tp.Union[str, tp.Tuple[str], tp.List[str]] = None,
        time: tp.Union[str, tp.Tuple[str], tp.List[str]] = None,
        merge: bool = False,
) -> None:
    """
    """
    logging.info(f"convert_odf_to_nc params. dims: {dims}, time: {time}, input_files: {input_files}, output_name: {output_name}")
    input_files = get_files_from_expression(input_files)
    datasets = []
    for fn in input_files:
        datasets.append(Odf().read(fn).to_dataset(dims=dims, time=time))
    if merge is True:
        output = Path(output_name if output_name is not None else input_files[0]).with_suffix('.nc')
        try:
            xr.merge(datasets, compat='override').to_netcdf(output)
            print(f"Netcdf file made -> {output}")
        except ValueError:
            print("Merging failed. Dimensions could be incompatible.")
            merge = False

    if merge is False:
        if output_name is not None:
            outputs = [output_name + '_' + str(i).rjust(2, '0') for i, _ in enumerate(input_files)]
        else:
            outputs = input_files
        for ds, output in zip(datasets, outputs):
            output = Path(output).with_suffix('.nc')
            ds.to_netcdf(output)
            print(f"Netcdf file made -> {output}")


if __name__ == "__main__":
    path = [
        "/home/jeromejguay/ImlSpace/Docs/ODF/Format_ODF/Exemples/CTD_BOUEE2019_RIKI_04130218_DN",
        "/home/jeromejguay/ImlSpace/Docs/ODF/Format_ODF/Exemples/MADCP_BOUEE2019_RIMOUSKI_553_VEL",
        "/home/jeromejguay/ImlSpace/Docs/ODF/Format_ODF/Exemples/MMOB_BOUEE2019_RIMOUSKI_IML4_METOCE",
        "/home/jeromejguay/ImlSpace/Docs/ODF/Format_ODF/Exemples/MADCP_BOUEE2019_RIMOUSKI_553_ANC",
    ]

    ds_vel = Odf().read(path[1] + ".ODF").to_dataset(dims=["DEPH_01", "SYTM_01"], time="SYTM_01")
    ds_anc = Odf().read(path[3] + ".ODF").to_dataset(dims=["DEPH_01", "SYTM_01"], time="SYTM_01")

    xr.merge((ds_vel, ds_anc), compat='override')
