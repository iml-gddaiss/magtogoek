"""
module to map xarray dataset to Odf
"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import xarray as xr
from typing import List, Union, Tuple, Dict, Optional
from magtogoek import CONFIGURATION_PATH
from magtogoek.odf_format import Odf, odf_time_format
from magtogoek.platforms import PlatformMetadata
from magtogoek.utils import json2dict

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

ADCP_COMMENTS_SENSOR = {
    'pres': {'sensor': 'PRESSURE_SENSOR_01', 'comments': {'CODE': 'DEPH_01', 'Name': 'pressure'}},
    'heading': {'sensor': 'COMPAS_SENSOR_01', 'comments': {'CODE': 'HEAD_01', 'Name': 'compas'}},
    'roll_': {'sensor': 'INClINOMETER_SENSOR_01', 'comments': {'CODE': 'ROLL_01', 'Name': 'tilt'}},
    'temperature': {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE': 'TE90_01', 'Name': 'temperature'}}
}


PARAMETERS_TYPES = {
    "int8": "INT",  # "BYTE",  # -128, 127
    "int16": "INT",  # SHORT  # -32768, 32767
    "int32": "INT",
    "int64": "LONG",
    "float16": "HALF",
    "float32": "SING",
    "float64": "DOUB",
    "|S1": "SYTM",
    "datetime64[ns]": "SYTM",
}
BEAM_PARAMETERS = ("time", "depth", "v1", "v2", "v3", "v4")
VEL_PARAMTERS = ("time", "depth", "u", "v", "w", "e")
ANC_PARAMTERS = ('time', 'pitch', 'roll_', 'heading', 'pres', 'temperature', 'lon', 'lat')
QC_PARAMETERS = ('u', 'v', 'w', 'pres', 'temperature')

PARAMETERS_METADATA_PATH = CONFIGURATION_PATH.joinpath("odf_parameters_metadata.json")

PARAMETERS_METADATA = json2dict(PARAMETERS_METADATA_PATH)


def make_odf(
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        sensor_id: str,
        config_attrs: dict,
        generic_variables_name: List[str],
        bodc_name: bool = True,
        event_qualifier2: str = 'VEL',
        output_path: Optional[str] = None, ):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    sensor_id :

    config_attrs :
        Global attributes parameter from the configFile.
    generic_variables_name :
        List of the generic name fo the variables. Python variables used in the code.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    event_qualifier2:
        Either `'VEL'` or `'ANC'`.
    output_path:
        If a path(str) is provided, there is two possibilities: if the path is only a directory, the file name
        will be made from the odf['file_specification']. If a file name is also provided, the 'event_qualifier2'
        will be appended to it if it's not present in the `output_path`.

    """
    odf = Odf()

    _make_cruise_header(odf, platform_metadata, config_attrs)
    _make_event_header(odf, dataset, config_attrs, event_qualifier2)
    _make_odf_header(odf)
    if platform_metadata.platform.platform_type == "buoy":
        _make_buoy_header(odf, platform_metadata)
        _make_adcp_buoy_instrument_header(odf, dataset, platform_metadata, sensor_id, generic_variables_name)
        _make_other_buoy_instrument_header(odf, platform_metadata)
    else:
        _make_instrument_header(odf, dataset)
    _make_quality_header(odf, dataset)
    _make_history_header(odf, dataset)

    if event_qualifier2 == 'VEL':
        if dataset.attrs['coord_system'] == 'beam':
            parameters = BEAM_PARAMETERS
        else:
            parameters = VEL_PARAMTERS
    else:
        parameters = ANC_PARAMTERS

    _make_parameter_headers(odf, dataset, parameters, bodc_name)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            if event_qualifier2 not in output_path.name:
                output_path = Path(str(output_path.with_suffix('')) + f'_{event_qualifier2}')
            odf.odf["file_specification"] = output_path.name

        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)
        print(f"odf {event_qualifier2.upper()} file made -> {output_path}")

    return odf


def _make_cruise_header(odf: Odf, platform_metadata: PlatformMetadata, config_attrs: dict):
    odf.cruise["country_institute_code"] = config_attrs["country_institute_code"]
    odf.cruise["organization"] = config_attrs["organization"]
    odf.cruise["chief_scientist"] = config_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(config_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(config_attrs["end_date"])
    odf.cruise["cruise_number"] = config_attrs["cruise_number"]
    odf.cruise["cruise_name"] = config_attrs["cruise_name"]
    odf.cruise["cruise_description"] = config_attrs["cruise_description"]

    odf.cruise["platform"] = platform_metadata.platform.platform_name
    if platform_metadata.platform.platform_type == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"


def _make_event_header(odf, dataset, config_attrs, event_qualifier2):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['data_type'] = dataset.attrs['data_type'].upper()
    odf.event["creation_date"] = odf_time_format(datetime.now())
    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
    if 'delta_t_sec' in dataset.attrs:
        odf.event['sampling_interval'] = dataset.attrs['delta_t_sec']
    odf.event["event_number"] = config_attrs["event_number"]
    odf.event["event_qualifier1"] = config_attrs["event_qualifier1"]
    odf.event["event_qualifier2"] = event_qualifier2
    if 'sounding' in dataset.attrs:
        odf.event['sounding'] = dataset.attrs['sounding']
    odf.event["event_comments"] = config_attrs["event_comments"]
    _set_event_header_geospatials(odf, dataset)


def _set_event_header_geospatials(odf: Odf, dataset: xr.Dataset) -> None:
    """ Set geospatial metadata from dataset.

    Sets :
     - initial_latitude, end_latitude
     - initial_latitude, end_longitude
     - depth_off_bottom

    Parameters
    ----------
    odf :
    dataset :
    """
    odf.event['start_date_time'] = odf_time_format(dataset.time.values.min())
    odf.event['end_date_time'] = odf_time_format(dataset.time.values.max())

    if odf.event['event_qualifier2'] == 'ANC':
        if 'xducer_depth' in dataset:
            odf.event['min_depth'] = dataset['xducer_depth'].values.min()
            odf.event['max_depth'] = dataset['xducer_depth'].values.max()
        elif dataset.attrs['P01_CODES_MAP']['xducer_depth'] in dataset:
            odf.event['min_depth'] = dataset[dataset.attrs['P01_CODES_MAP']['xducer_depth']].values.min()
            odf.event['max_depth'] = dataset[dataset.attrs['P01_CODES_MAP']['xducer_depth']].values.max()
        else:
            odf.event['min_depth'] = dataset.attrs['sensor_depth']
            odf.event['max_depth'] = dataset.attrs['sensor_depth']
    else:
        odf.event['min_depth'] = dataset.depth.values.min()
        odf.event['max_depth'] = dataset.depth.values.max()

    if "lat" in dataset and "lon" in dataset:
        odf.event["initial_latitude"] = dataset.lat.values[0]
        odf.event["end_latitude"] = dataset.lat.values[-1]
        odf.event["initial_longitude"] = dataset.lon.values[0]
        odf.event["end_longitude"] = dataset.lon.values[-1]
    elif "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["depth_off_bottom"] = 0
    if odf.event["sounding"] is not None:
        odf.event["depth_off_bottom"] = odf.event['sounding'] - odf.event['max_depth']


def _make_odf_header(odf):
    """
    Make field specification with:
    data_type, cruise_number, event_number, event_qualifier1, event_qualifier2
    Joins with `_` and add the extension `.ODF`.
    """
    name_part = [
        odf.event["data_type"],
        odf.cruise["cruise_number"],
        odf.event["event_number"],
        odf.event["event_qualifier1"],
        odf.event["event_qualifier2"],
    ]

    odf.odf["file_specification"] = "_".join(name_part).strip("_").upper() + ".ODF"


def _make_instrument_header(odf, dataset):
    """
    inst_type
    model
    serial_number
    description
    """
    # Note maybe rename it to instrument_comments.
    for key_odf, key_nc in (('inst_type', 'manufacturer'), ("description", "comments")):
        if key_nc in dataset.attrs:
            odf.instrument[key_odf] = dataset.attrs[key_nc]
    for key in ['model', 'serial_number']:
        if key in dataset.attrs:
            odf.instrument[key] = str(dataset.attrs[key])


def _make_buoy_header(odf: Odf, platform_metadata: PlatformMetadata):
    """
    Use BUOY_ATTRS
    """
    odf.buoy["name"] = platform_metadata.platform.platform_name
    for key in ['type', 'model', 'diameter', 'weight', 'height', 'description']:
        if key in platform_metadata.buoy_specs.__dict__:
            odf.buoy[key] = str(platform_metadata.buoy_specs.__dict__[key])


def _make_adcp_buoy_instrument_header(odf: Odf, dataset: xr.Dataset, platform_metadata: PlatformMetadata, sensor_id: str,
                                      generic_variables_name: List[str]):
    """

    Parameters
    ----------
    odf
    dataset
    platform_metadata
    sensor_id
    generic_variables_name :
        List of the generic name fo the variables. Python variables used in the code.

    Returns
    -------

    """

    #
    #"""
    odf.add_buoy_instrument(sensor_id)
    header = odf.buoy_instrument[sensor_id]

    for key_odf, key_nc in (('type', 'manufacturer'),):
        if key_nc in dataset.attrs:
            header[key_odf] = dataset.attrs[key_nc]
    for key in ['model', 'serial_number', 'description']:
        if key in dataset.attrs:
            header[key] = str(dataset.attrs[key])

    header["inst_start_date_time"] = odf_time_format(dataset.time.values.min())
    header["inst_end_date_time"] = odf_time_format(dataset.time.values.max())

    _make_adcp_buoy_instrument_comments(odf, sensor_id, dataset, platform_metadata)
    _make_adcp_buoy_instrument_sensor_comments(odf, sensor_id, dataset, generic_variables_name)


def _make_adcp_buoy_instrument_comments(odf: Odf, sensor_id: str, dataset: xr.Dataset, platform_metadata: PlatformMetadata):
    """

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    configuration = "CONFIGURATION_01"
    comments = {}
    keys = (("Mode", "orientation"),
            ("Ping_Type", "ping_type"),
            ("Frequency", "frequency"),
            ("Firmware_Version", "firmware_version"),
            ("Ping_per_Ensemble", "ping_per_ensemble"),
            ("Ensemble_Length_s", "delta_t_sec"),
            ("ADCP_Depth_m", "sensor_depth"),
            ("Distance_ADCP_to_First_Bin_Center_m", "bin1dist"),
            ("Bin_Size_m", "bin_size"),
            ("Blank_m", "blank"),
            ("Transmit_Pulse_Length_m", "transmit_pulse_length_m"))
    for key_odf, key_nc in keys:
        if key_nc in dataset.attrs:
            comments[key_odf] = dataset.attrs[key_nc]

    if "ping_per_ensemble" in dataset.attrs and "delta_t_sec" in dataset.attrs:
        if dataset.attrs["ping_per_ensemble"] and dataset.attrs["delta_t_sec"]:
            comments["Ping_Interval_s"] = round(
                dataset.attrs["ping_per_ensemble"]
                / dataset.attrs["delta_t_sec"],
                2,
            )
    if "magnetic_declination" in dataset.attrs:
        if "magnetic_declination_units" in dataset.attrs:
            comments["Magnetic_Declination"] = (
                    str(dataset.attrs["magnetic_declination"])
                    + " "
                    + dataset.attrs["magnetic_declination_units"]
            )
    comments["Bin_Count"] = len(dataset.depth)
    comments['Comments'] = platform_metadata.__dict__[sensor_id].comments

    for key, value in comments.items():
        odf.buoy_instrument[sensor_id]["buoy_instrument_comments"].append(
            configuration + "." + key + ": " + str(value)
        )


def _make_adcp_buoy_instrument_sensor_comments(odf: Odf, sensor_id: str, dataset: xr.Dataset, generic_variables_name: List[str]):
    """

    Parameters
    ----------
    odf

    sensor_id

    dataset

    generic_variables_name :
      List of the generic name fo the variables. Python variables used in the code.

    Returns
    -------
    """
    dataset_attrs = {'Manufacturer': 'manufacturer', 'Depth': 'sensor_depth', 'Serial_Number': 'serial_number'}
    for var, item in ADCP_COMMENTS_SENSOR.items():
        if var in generic_variables_name:
            for key, value in item['comments'].items():
                odf.buoy_instrument[sensor_id]["sensors"].append(item['sensor'] + "." + key + ': ' + value)
            for key, value in dataset_attrs.items():
                if value in dataset.attrs:
                    if dataset.attrs[value] is not None:
                        odf.buoy_instrument[sensor_id]["sensors"].append(
                            item['sensor'] + "." + key + ': ' + str(dataset.attrs[value])
                        )


def _make_other_buoy_instrument_header(odf: Odf, platform_metadata: PlatformMetadata):
    """

    Parameters
    ----------
    odf
    platform_metadata

    Returns
    -------
    """
    configuration = "CONFIGURATION_01"
    for sensor_id, sensor in platform_metadata.__dict__.items():
        if sensor_id in ['platform', 'buoy_specs']:
            continue
        odf.add_buoy_instrument(sensor_id)
        odf.buoy_instrument[sensor_id]['type'] = sensor.sensor_type
        odf.buoy_instrument[sensor_id]['model'] = sensor.model
        odf.buoy_instrument[sensor_id]['serial_number'] = sensor.serial_number
        odf.buoy_instrument[sensor_id]['description'] = sensor.description
        comments = {
            "Firmware_Version": sensor.firmware_version,
            "depth_m": sensor.sensor_depth,
            "Comments": sensor.comments
        }

        for key, value in comments.items():
            odf.buoy_instrument[sensor_id]["buoy_instrument_comments"].append(
                configuration + "." + key + ": " + str(value)
            )


def _make_quality_header(odf, dataset):
    """
    """
    comments = dataset.attrs['quality_comments'].strip("\n").split("\n")
    time_stamp = _find_section_timestamp(comments.pop())

    odf.quality["quality_date"] = odf_time_format(datetime.now())
    if time_stamp:
        odf.quality["quality_date"] = odf_time_format(time_stamp)

    odf.quality["quality_tests"] = comments
    keys = ['flags_reference', 'flags_values', 'flags_meanings']
    for key in keys:
        odf.quality["quality_comments"].append(key + ': ' + str(dataset.attrs[key]))


def _make_history_header(odf, dataset):
    """Make one or more history_header.
    1 - Default process comments is added with a Timestamp (datetime.now()).
    2 - Looks for log section `[Loading adcp data], [Data transformation]` in
        dataset.attrs['history'] and add the log messages that follow.
    3 - New history_header are made for each TimeStamp found with the log section.
    """
    processing = ["Data processed by Magtogoek Processing Software. More at " + REPOSITORY_ADDRESS]
    creation_date = odf_time_format(datetime.now())

    iter_logbook = iter(re.split(r"(\[.*])", dataset.attrs["history"]))
    for log_entry in iter_logbook:
        if log_entry in ["[Loading adcp data]", "[Data transformation]"]:
            logs = next(iter_logbook).strip("\n").split("\n")
            time_stamp = _find_section_timestamp(logs[0])
            if time_stamp is not None:
                del logs[0]
                odf.add_history({"creation_date": creation_date, "process": processing})
                creation_date = odf_time_format(pd.Timestamp(time_stamp))
                processing = []
            processing += logs
    odf.add_history({"creation_date": creation_date, "process": processing})


def _make_parameter_headers(odf, dataset, variables: List[str], bodc_name=False):
    """
    Parameters
    ----------
    odf:
    dataset:
        Dataset to which add the navigation data.
    variables:
       variables to put in the ODF.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    Notes
    -----
    The variable order in the ODF will be the same as in the variables list parameter.
    """

    parameters_metadata = {}
    parameters = []
    qc_parameters = []

    for var in variables:
        dataset_variable_name = var
        if bodc_name is True and not var in ('time', 'depth'):
            dataset_variable_name = dataset.attrs["P01_CODES_MAP"][var]
        if dataset_variable_name in dataset.variables:
            parameters_metadata[dataset_variable_name] = PARAMETERS_METADATA[var]
            parameters.append(dataset_variable_name)
            if var in QC_PARAMETERS and dataset_variable_name + '_QC' in dataset.variables:
                qc_parameters.append(dataset_variable_name + '_QC')

    dims = ['time', 'depth'] if 'depth' in variables else ['time']
    data = dataset[parameters + qc_parameters].to_dataframe().reset_index().sort_values(dims)

    qc_increment = 1
    for var in parameters:
        add_qc_var = var + '_QC' in qc_parameters

        items = {"depth": dataset.attrs["sensor_depth"],
                 'magnetic_variation': dataset.attrs["magnetic_declination"],
                 "type": PARAMETERS_TYPES[str(dataset[var].data.dtype)]}
        items.update(parameters_metadata[var])

        qc_mask = data[var + '_QC'].values <= 2 if add_qc_var is True else None

        null_value = items["null_value"] if "null_value" in items else dataset[var].encoding["_FillValue"]

        odf.add_parameter(code=items["code"],
                          data=data[var].values,
                          null_value=null_value,
                          items=items,
                          qc_mask=qc_mask)

        if add_qc_var is True:
            qc_items = {
                "code": "QQQQ_" + str(qc_increment).zfill(2),
                "name": "Quality flag: " + items['name'],
                "units": "none",
                "print_field_width": 1,
                "print_decimal_places": 0,
                "null_value": 9,
                "type": PARAMETERS_TYPES[str(dataset[var + '_QC'].data.dtype)]
            }
            odf.add_parameter(code=qc_items["code"],
                              data=data[var + '_QC'].values,
                              null_value=9,
                              items=qc_items,
                              qc_mask=None)
            qc_increment += 1


def _find_section_timestamp(s: str) -> str:
    r""" String of Section - Timestamp

    regex : ([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})'
    """
    regex = r"([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    match = re.findall(regex, s)
    if match:
        return match[0]
    return None


if __name__ == "__main__":
    #    from magtogoek.adcp.process import _get_config, _load_platform
    #    from magtogoek.configfile import load_configfile

    _nc_file = "../../test/files/iml6_2017_wh.nc"
    _platform_files = "../../test/files/iml_platforms.json"
    _config_file = "../../test/files/adcp_iml6_2017.ini"

    #    _dataset = xr.open_dataset(_nc_file)
    #    _params, _global_attrs = _get_config(load_configfile(_config_file))
    #    _params["platform_file"] = _platform_files
    #    _sensor_metadata = _load_platform(_params)

    _p01_to_generic_name = {
        "u": "LCEWAP01",
        "u_QC": "LCEWAP01_QC",
        "v": "LCNSAP01",
        "v_QC": "LCNSAP01_QC",
        "w": "LRZAAP01",
        "w_QC": "LRZAAP01_QC",
        "e": "LERRAP01",
    }

#    _odf = make_odf(_dataset, _sensor_metadata, _global_attrs, _p01_to_generic_name)
